#!/usr/bin/env python3
"""
Cliente de Integração Direta com a API GraphQL (AWS AppSync) do Noctua IoT.
Permite consultar telemetria dos sensores, ler/alterar configurações de thresholds/timers
e enviar comandos para motores com proteção contra acionamentos acidentais.
"""
import os
import json
import uuid
import logging
from typing import Dict, Any, Optional, List
import requests
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

logger = logging.getLogger(__name__)

# Defaults do ecossistema Noctua IoT
DEFAULT_APPSYNC_URL = "https://qhurq5cthrd75ppzeyutzcclje.appsync-api.sa-east-1.amazonaws.com/graphql"
DEFAULT_GATEWAY_ID = "10:20:BA:65:3A:B8"
KNOWN_ENDPOINTS = {
    "10:20:BA:66:2E:C8": "Tanque 1",
    "10:20:BA:6A:90:00": "Tanque 2"
}

# --- QUERIES GRAPHQL ---

QUERY_LIST_SENSOR_DATA = """
query ListSensorData(
  $gatewayId: ID!,
  $limit: Int,
  $sortDirection: ModelSortDirection
) {
  listSensorDataByGatewayIdAndUpdatedAt(
    gatewayId: $gatewayId
    limit: $limit
    sortDirection: $sortDirection
  ) {
    items {
      id
      gatewayId
      endpointId
      bucketId
      ts
      o2
      sat
      temperature
      hpa
      engines
      o2Readings
      probe
      timer
      rssi
      snr
      criticalO2
      criticalO2Max
      errors
      createdAt
      updatedAt
    }
    nextToken
  }
}
"""

QUERY_LIST_HOURLY_DATA = """
query ListHourlyData(
  $endpointId: ID!,
  $limit: Int,
  $sortDirection: ModelSortDirection
) {
  listHourlyDataByEndpointIdAndTimestamp(
    endpointId: $endpointId
    limit: $limit
    sortDirection: $sortDirection
  ) {
    items {
      id
      gatewayId
      endpointId
      timestamp
      o2
      sat
      temp
      hpa
      engines
      rssi
      snr
      errors
      createdAt
      updatedAt
    }
    nextToken
  }
}
"""

QUERY_GET_ENDPOINT = """
query GetEndpoint($id: ID!) {
  getEndpoint(id: $id) {
    id
    gatewayId
    name
    timer
    autoOn
    engines
    criticalO2
    criticalO2Max
    o2Ajusted
    createdAt
    updatedAt
  }
}
"""

MUTATION_UPDATE_ENDPOINT = """
mutation UpdateEndpoint($input: UpdateEndpointInput!) {
  updateEndpoint(input: $input) {
    id
    gatewayId
    name
    timer
    autoOn
    engines
    criticalO2
    criticalO2Max
    o2Ajusted
    updatedAt
  }
}
"""

MUTATION_CREATE_COMMAND = """
mutation CreateCommand($input: CreateCommandMessagesInput!) {
  createCommandMessages(input: $input) {
    messageId
    endpointId
    gatewayId
    command
    message
    status
    createdAt
    updatedAt
  }
}
"""

QUERY_GET_COMMAND = """
query GetCommand($messageId: ID!) {
  getCommandMessages(messageId: $messageId) {
    messageId
    endpointId
    gatewayId
    command
    message
    status
    createdAt
    updatedAt
  }
}
"""


class NoctuaClientException(Exception):
    """Exceção base para erros de comunicação ou regra de negócio com Noctua IoT."""
    pass


class NoctuaReadOnlyException(NoctuaClientException):
    """Disparada quando uma operação de escrita é tentada sob NOCTUA_READ_ONLY=true."""
    pass


class NoctuaClient:
    """Cliente HTTP síncrono para o AWS AppSync do Noctua IoT."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        gateway_id: Optional[str] = None,
        read_only: Optional[bool] = None,
        timeout_seconds: int = 15
    ):
        self.api_url = api_url or os.getenv("NOCTUA_APPSYNC_URL", DEFAULT_APPSYNC_URL)
        self.api_key = api_key or os.getenv("NOCTUA_API_KEY", "")
        self.gateway_id = gateway_id or os.getenv("NOCTUA_GATEWAY_ID", DEFAULT_GATEWAY_ID)
        
        # Trava de segurança para escrita/motores
        if read_only is not None:
            self.read_only = read_only
        else:
            self.read_only = os.getenv("NOCTUA_READ_ONLY", "true").lower() in ("true", "1", "yes")

        self.timeout = timeout_seconds
        self.session = requests.Session()

    def _get_headers(self) -> Dict[str, str]:
        if not self.api_key or self.api_key.startswith("da2-chave_temporaria"):
            logger.warning("NOCTUA_API_KEY não configurada ou usando placeholder.")
        return {
            "Content-Type": "application/json",
            "x-api-key": self.api_key
        }

    def _execute_graphql(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Executa uma chamada GraphQL no AWS AppSync com tratamento de status e erros."""
        payload = {
            "query": query,
            "variables": variables or {}
        }
        headers = self._get_headers()

        try:
            response = self.session.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
        except requests.RequestException as e:
            logger.error("Erro de conexão com o AWS AppSync: %s", e)
            raise NoctuaClientException(f"Falha de rede ao conectar à API Noctua: {e}") from e

        if response.status_code != 200:
            logger.error("Resposta HTTP de erro (%s): %s", response.status_code, response.text)
            raise NoctuaClientException(
                f"Erro na API Noctua HTTP {response.status_code}: {response.text[:200]}"
            )

        data = response.json()
        if "errors" in data and data["errors"]:
            logger.error("Erros no retorno GraphQL: %s", data["errors"])
            raise NoctuaClientException(f"Erro GraphQL: {data['errors']}")

        return data.get("data", {})

    def test_connection(self) -> Dict[str, Any]:
        """Testa se as credenciais e o endpoint GraphQL respondem com sucesso."""
        try:
            data = self.get_latest_sensor_data(limit=1)
            return {
                "status": "success",
                "message": "Conexão com AWS AppSync estabelecida com sucesso!",
                "items_count": len(data.get("items", []))
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    # =========================================================================
    # 1. LEITURA DE TELEMETRIA
    # =========================================================================

    def get_latest_sensor_data(self, gateway_id: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """Consulta as leituras mais recentes registradas para o gateway."""
        gid = gateway_id or self.gateway_id
        variables = {
            "gatewayId": gid,
            "limit": limit,
            "sortDirection": "DESC"
        }
        res = self._execute_graphql(QUERY_LIST_SENSOR_DATA, variables)
        return res.get("listSensorDataByGatewayIdAndUpdatedAt", {"items": []})

    def get_latest_readings_by_tanque(self) -> Dict[str, Dict[str, Any]]:
        """
        Consulta os dados recentes e extrai a leitura mais atual de cada tanque conhecido.
        Retorna dicionário indexado pelo nome do tanque, ex:
        {
            'Tanque 1': {'o2': 4.5, 'temperature': 25.2, 'sat': 90.0, 'engines': '00000', ...},
            'Tanque 2': {'o2': 3.8, 'temperature': 24.9, ...}
        }
        """
        raw_data = self.get_latest_sensor_data(limit=50)
        items = raw_data.get("items", [])
        
        result: Dict[str, Dict[str, Any]] = {}
        for item in items:
            endpoint_id = (item.get("endpointId") or "").strip().upper()
            
            # Identificar o nome do tanque correspondente
            tanque_nome = None
            for mac, name in KNOWN_ENDPOINTS.items():
                if mac.upper() == endpoint_id:
                    tanque_nome = name
                    break
            
            if not tanque_nome:
                # Se não estiver no mapa padrão, usa o próprio endpointId
                tanque_nome = f"Tanque ({endpoint_id})"

            # Como vêm ordenados por DESC (mais recentes primeiro), mantemos apenas o primeiro visto
            if tanque_nome not in result:
                # Parsing de motores: engines pode ser string '00000' ou similar
                engines_raw = str(item.get("engines") or "")
                aeradores_ativos = sum(1 for c in engines_raw if c == '1')

                result[tanque_nome] = {
                    "endpoint_id": item.get("endpointId"),
                    "gateway_id": item.get("gatewayId"),
                    "nome_estrutura": tanque_nome,
                    "oxigenio": float(item.get("o2", 0.0) or 0.0),
                    "temperatura": float(item.get("temperature", 0.0) or 0.0),
                    "saturacao": float(item.get("sat", 0.0) or 0.0),
                    "hpa": float(item.get("hpa", 0.0) or 0.0),
                    "engines": engines_raw,
                    "aeradores_ativos": aeradores_ativos,
                    "rssi": item.get("rssi"),
                    "snr": item.get("snr"),
                    "critical_o2": item.get("criticalO2"),
                    "critical_o2_max": item.get("criticalO2Max"),
                    "timestamp": item.get("ts") or item.get("updatedAt") or item.get("createdAt"),
                    "updated_at": item.get("updatedAt"),
                    "errors": item.get("errors")
                }

        return result

    def get_hourly_sensor_data(self, endpoint_id: str, limit: int = 48) -> List[Dict[str, Any]]:
        """Consulta o histórico de dados agregados por hora para um endpoint específico."""
        variables = {
            "endpointId": endpoint_id,
            "limit": limit,
            "sortDirection": "DESC"
        }
        res = self._execute_graphql(QUERY_LIST_HOURLY_DATA, variables)
        items = res.get("listHourlyDataByEndpointIdAndTimestamp", {}).get("items", [])
        return items

    # =========================================================================
    # 2. CONFIGURAÇÃO DE ENDPOINTS (THRESHOLDS & TIMERS)
    # =========================================================================

    def get_endpoint_config(self, endpoint_id: str) -> Dict[str, Any]:
        """Consulta as configurações e parâmetros de um tanque/endpoint."""
        variables = {"id": endpoint_id}
        res = self._execute_graphql(QUERY_GET_ENDPOINT, variables)
        endpoint = res.get("getEndpoint")
        if not endpoint:
            raise NoctuaClientException(f"Endpoint {endpoint_id} não encontrado na API Noctua.")
        return endpoint

    def update_endpoint_thresholds(
        self,
        endpoint_id: str,
        critical_o2: Optional[float] = None,
        critical_o2_max: Optional[float] = None,
        auto_on: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Atualiza os limiares de oxigênio crítico e o modo de automação.
        Garante limites operacionais de segurança (1.0 <= O2 <= 10.0).
        """
        if self.read_only:
            raise NoctuaReadOnlyException(
                "Operação bloqueada: NOCTUA_READ_ONLY está ativo. Nenhuma alteração foi enviada."
            )

        input_payload: Dict[str, Any] = {"id": endpoint_id}

        if critical_o2 is not None:
            if not (1.0 <= critical_o2 <= 10.0):
                raise ValueError(f"critical_o2 fora da faixa de segurança (1.0 - 10.0): {critical_o2}")
            input_payload["criticalO2"] = float(critical_o2)

        if critical_o2_max is not None:
            if not (1.0 <= critical_o2_max <= 15.0):
                raise ValueError(f"critical_o2_max fora da faixa de segurança (1.0 - 15.0): {critical_o2_max}")
            input_payload["criticalO2Max"] = float(critical_o2_max)

        if auto_on is not None:
            input_payload["autoOn"] = bool(auto_on)

        logger.info("Enviando mutation UpdateEndpoint: %s", input_payload)
        res = self._execute_graphql(MUTATION_UPDATE_ENDPOINT, {"input": input_payload})
        return res.get("updateEndpoint", {})

    def update_endpoint_timer(self, endpoint_id: str, timer_data: Any) -> Dict[str, Any]:
        """
        Atualiza a programação de janelas horárias (timer).
        timer_data pode ser um dicionário/lista ou uma string JSON já serializada.
        """
        if self.read_only:
            raise NoctuaReadOnlyException(
                "Operação bloqueada: NOCTUA_READ_ONLY está ativo. Nenhuma alteração foi enviada."
            )

        if isinstance(timer_data, (dict, list)):
            timer_str = json.dumps(timer_data)
        elif isinstance(timer_data, str):
            # Valida se é JSON válido
            json.loads(timer_data)
            timer_str = timer_data
        else:
            raise ValueError("timer_data deve ser dict, list ou string JSON válida.")

        input_payload = {
            "id": endpoint_id,
            "timer": timer_str
        }

        logger.info("Enviando mutation UpdateEndpoint Timer para %s", endpoint_id)
        res = self._execute_graphql(MUTATION_UPDATE_ENDPOINT, {"input": input_payload})
        return res.get("updateEndpoint", {})

    # =========================================================================
    # 3. COMANDOS DE ACIONAMENTO DE MOTORES (PROTOCOLO SEGURO)
    # =========================================================================

    def send_motor_command(
        self,
        endpoint_id: str,
        command: str,
        gateway_id: Optional[str] = None,
        message: str = "Acionamento manual via sistema"
    ) -> Dict[str, Any]:
        """
        Envia mensagem de comando para o gateway/endpoint do tanque.
        Bloqueado rigorosamente se NOCTUA_READ_ONLY=true.
        """
        if self.read_only:
            raise NoctuaReadOnlyException(
                "Operação de envio de comando bloqueada: NOCTUA_READ_ONLY está ativo."
            )

        # Allowlist estrita de endpoints
        if endpoint_id.upper() not in [m.upper() for m in KNOWN_ENDPOINTS.keys()]:
            raise NoctuaClientException(f"Endpoint não autorizado na allowlist: {endpoint_id}")

        msg_id = str(uuid.uuid4())
        gid = gateway_id or self.gateway_id

        input_payload = {
            "messageId": msg_id,
            "endpointId": endpoint_id,
            "gatewayId": gid,
            "command": command,
            "message": message
        }

        logger.warning("ENVIANDO COMANDO FÍSICO PARA MOTORES: %s", input_payload)
        res = self._execute_graphql(MUTATION_CREATE_COMMAND, {"input": input_payload})
        return res.get("createCommandMessages", {})

    def get_command_status(self, message_id: str) -> Dict[str, Any]:
        """Consulta o status de entrega do comando (SENT, DELIVERED, GATEWAY_OFFLINE, etc.)."""
        res = self._execute_graphql(QUERY_GET_COMMAND, {"messageId": message_id})
        return res.get("getCommandMessages", {})


# --- FUNÇÃO PRINCIPAL / CLI PARA TESTES E DIAGNÓSTICO ---

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Utilitário CLI do Noctua IoT Client")
    parser.add_argument("--test", action="store_true", help="Testa conectividade com AWS AppSync")
    parser.add_argument("--readings", action="store_true", help="Exibe leituras recentes dos tanques")
    parser.add_argument("--endpoint", type=str, help="MAC de endpoint para inspecionar configurações")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    client = NoctuaClient()

    print("\n--- Noctua IoT Client CLI ---")
    print(f"URL: {client.api_url}")
    print(f"Gateway ID: {client.gateway_id}")
    print(f"Read-Only Ativo: {client.read_only}")
    print(f"API Key Definida: {'Sim (' + client.api_key[:6] + '...)' if client.api_key else 'Não'}")

    if args.test or (not args.readings and not args.endpoint):
        print("\nTestando conectividade...")
        result = client.test_connection()
        print(f"Resultado: {result}")

    if args.readings:
        print("\nBuscando leituras mais recentes por tanque...")
        try:
            readings = client.get_latest_readings_by_tanque()
            print(json.dumps(readings, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"Erro ao obter leituras: {e}")

    if args.endpoint:
        print(f"\nBuscando configurações do endpoint {args.endpoint}...")
        try:
            cfg = client.get_endpoint_config(args.endpoint)
            print(json.dumps(cfg, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"Erro ao obter endpoint: {e}")


if __name__ == "__main__":
    main()
