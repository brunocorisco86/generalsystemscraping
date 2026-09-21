import os
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

# Importar o serviço de banco de dados do projeto
from src.services.database import (
    get_sqlite_connection,
    get_estrutura_uid,
    get_default_estrutura_info,
    get_all_estruturas_map,
    is_system_suspended,
    SQLITE_DB_PATH
)
from src.services.noctua_client import NoctuaClient, NoctuaClientException

# Configuração do logger
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

def ensure_leituras_table(conn):
    """Garante que a tabela de leituras exista com o schema correto."""
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leituras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            estrutura_uid TEXT,
            nome_estrutura TEXT,
            oxigenio REAL,
            temperatura REAL,
            timestamp_site TIMESTAMP,
            data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            aeradores_ativos INTEGER DEFAULT 0
        )
    ''')
    try:
        cursor.execute("ALTER TABLE leituras ADD COLUMN nome_estrutura TEXT")
    except Exception:
        pass
    conn.commit()

def collect_via_api() -> bool:
    """
    Realiza a coleta das leituras dos tanques diretamente via AWS AppSync GraphQL do Noctua IoT.
    Substitui integralmente o scraping por Selenium/Chromium, reduzindo latência e consumo de RAM.
    """
    client = NoctuaClient()
    
    # 1. Obter leituras mais recentes por tanque via GraphQL
    logger.info("Solicitando telemetria recente via Noctua GraphQL API...")
    readings = client.get_latest_readings_by_tanque()

    if not readings:
        logger.warning("Nenhum dado retornado pela API GraphQL do Noctua IoT.")
        return False

    # 2. Conectar ao SQLite de borda
    os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
    conn = get_sqlite_connection()
    if not conn:
        raise Exception("Não foi possível conectar ao banco SQLite local.")

    try:
        ensure_leituras_table(conn)
        cursor = conn.cursor()
        estruturas_map = get_all_estruturas_map()

        inseridos = 0
        for nome_tanque, data in readings.items():
            nome_upper = (nome_tanque or "").strip().upper()
            if not nome_upper or "N/A" in nome_upper or "DESCONHECIDO" in nome_upper:
                logger.warning("Ignorando tanque com nome inválido/N/A: %s", nome_tanque)
                continue

            oxigenio = data["oxigenio"]
            temperatura = data["temperatura"]
            aeradores = data["aeradores_ativos"]
            raw_ts = data.get("timestamp")

            # Filtro de sensor offline/zerado
            if oxigenio == 0.0 and temperatura == 0.0:
                logger.warning("%s ignorado (O2 e Temperatura zerados).", nome_tanque)
                continue

            # Tratamento de Timestamp para formato SQL padrão (YYYY-MM-DD HH:MM:SS)
            ts_sql = None
            if raw_ts:
                try:
                    # Suporta ISO8601 (ex: 2026-09-20T18:00:00.000Z ou 2026-09-20T18:00:00Z)
                    clean_ts = raw_ts.replace("Z", "+00:00")
                    dt_obj = datetime.fromisoformat(clean_ts)
                    ts_sql = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    ts_sql = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            else:
                ts_sql = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Resolver UID da estrutura
            uid = estruturas_map.get(nome_tanque)
            if not uid:
                logger.warning("UID para %s não encontrado no mapa de estruturas. Gerando fallback...", nome_tanque)
                info_env = get_default_estrutura_info()
                pluscode = info_env['pluscode'] if nome_tanque == info_env['nome'] else "UNKNOWN"
                uid = get_estrutura_uid(nome_tanque, pluscode)

            # Evitar duplicata se já existir leitura para a mesma estrutura e timestamp_site
            cursor.execute('''
                SELECT id FROM leituras 
                WHERE nome_estrutura = ? AND timestamp_site = ?
            ''', (nome_tanque, ts_sql))
            if cursor.fetchone():
                logger.info("Leitura já existente para %s no timestamp %s. Ignorando duplicata.", nome_tanque, ts_sql)
                continue

            # Inserção no banco
            cursor.execute('''
                INSERT INTO leituras (estrutura_uid, nome_estrutura, oxigenio, temperatura, aeradores_ativos, timestamp_site)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (uid, nome_tanque, oxigenio, temperatura, aeradores, ts_sql))

            logger.info("✅ Coletado via API: %s | O2: %.2f mg/L | Temp: %.1f°C | Aeradores: %d | TS: %s",
                        nome_tanque, oxigenio, temperatura, aeradores, ts_sql)
            inseridos += 1

        conn.commit()
        logger.info("Coleta via API concluída com sucesso! Total inserido: %d.", inseridos)
        return inseridos > 0

    finally:
        conn.close()

def scrape_and_save():
    """
    Função principal de tomada de dados.
    Utiliza preferencialmente a API GraphQL direta.
    """
    if is_system_suspended():
        logger.info("Sistema suspenso. Ignorando tomada de dados.")
        return

    logger.info("Iniciando tomada de dados dos tanques...")
    try:
        sucesso = collect_via_api()
        if sucesso:
            return
    except Exception as e:
        logger.error("Erro na tomada de dados via API GraphQL: %s", e)

    logger.warning("Tomada de dados finalizada com pendências ou sem novas leituras.")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    scrape_and_save()
