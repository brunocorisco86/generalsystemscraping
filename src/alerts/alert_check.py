import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Importar serviços do projeto
import asyncio
from src.services.database import get_sqlite_connection, get_postgres_connection, get_all_estruturas_map
from src.services.notification import send_telegram_message
from src.bots.agent import analyze_alert_data

# Configuração do logger
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Configurações via .env
LIMITE_OXIGENIO_CRITICO = float(os.getenv("LIMITE_OXIGENIO_CRITICO", 1.5))

def check_alerts():
    """Verifica as últimas leituras no banco de dados e dispara alertas se necessário."""
    conn = None
    try:
        conn = get_sqlite_connection()
        if not conn:
            logger.error("Não foi possível conectar ao banco de dados SQLite.")
            return
            
        cursor = conn.cursor()

        # Busca a última leitura de cada tanque usando subquery
        cursor.execute("""
            SELECT t1.nome_estrutura, t1.oxigenio, t1.temperatura 
            FROM leituras t1
            INNER JOIN (
                SELECT nome_estrutura, MAX(data_coleta) as max_date
                FROM leituras
                GROUP BY nome_estrutura
            ) t2 ON t1.nome_estrutura = t2.nome_estrutura AND t1.data_coleta = t2.max_date
        """)
        leituras = cursor.fetchall()

        if not leituras:
            return

        # --- FILTRAGEM DE LOTES ATIVOS (PostgreSQL) ---
        estruturas_ativas = None
        pg_conn = get_postgres_connection()
        if pg_conn:
            try:
                pg_cur = pg_conn.cursor()
                pg_cur.execute("SELECT estrutura_uid FROM lotes WHERE data_abate IS NULL")
                estruturas_ativas = {r[0] for r in pg_cur.fetchall()}
            except Exception as e:
                logger.error(f"Erro ao buscar estruturas ativas no Postgres para alert_check: {e}")
            finally:
                pg_conn.close()

        estruturas_map = get_all_estruturas_map()

        for tanque, oxigenio, temperatura in leituras:
            # Filtra apenas se houver conexão bem-sucedida e o tanque não estiver ativo
            uid = estruturas_map.get(tanque)
            if estruturas_ativas is not None and (not uid or uid not in estruturas_ativas):
                logger.info("Ignorando verificação para %s (Lote inativo)", tanque)
                continue

            # Log de monitoramento
            logger.info("Verificando %s: %s Mg/L", tanque, oxigenio)

            # Dispara o alerta se estiver abaixo do limite
            if oxigenio < LIMITE_OXIGENIO_CRITICO:
                logger.info(f"O2 baixo em {tanque} ({oxigenio}). Solicitando análise da IA...")
                # Chama a IA para analisar o histórico recente e validar
                mensagem_ia = asyncio.run(analyze_alert_data(tanque, oxigenio, temperatura))
                
                if mensagem_ia:
                    send_telegram_message(mensagem_ia)
                    logger.info("Alerta validado e enviado para %s", tanque)
                else:
                    logger.info("Alerta suprimido pela IA (falso positivo) para %s", tanque)

    except Exception as e:
        logger.error("Erro ao processar alertas: %s", e)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Configuração básica de logging para execução direta
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    # Para executar do root: python3 -m src.alerts.alert_check
    check_alerts()
