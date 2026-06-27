import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Importar serviços do projeto
from src.services.database import get_sqlite_connection, get_postgres_connection, get_all_estruturas_map
from src.services.notification import send_telegram_message

# Configuração do logger
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Configurações via .env
MINUTOS_OFFLINE_ALERTA = int(os.getenv("MINUTOS_OFFLINE_ALERTA", 30))

def check_last_reading():
    """
    Verifica o tempo da última leitura dos tanques. 
    Envia alerta se o atraso for maior que o configurado.
    """
    logger.info("--- Iniciando Verificação de Status Offline ---")
    logger.info("Configuração: Alerta após %d minutos de inatividade.", MINUTOS_OFFLINE_ALERTA)
    
    conn = None
    try:
        conn = get_sqlite_connection()
        if not conn:
            logger.error("Erro Crítico: Não foi possível conectar ao banco de dados SQLite.")
            return

        cursor = conn.cursor()

        # Busca a última leitura de cada tanque em uma única consulta
        cursor.execute("""
            SELECT nome_estrutura, MAX(timestamp_site) as last_reading
            FROM leituras
            GROUP BY nome_estrutura
        """)
        results = cursor.fetchall()

        if not results:
            logger.warning("Nenhum data de tanque encontrado na tabela 'leituras'.")
            send_telegram_message("🚫 *Atenção:* Nenhum dado de tanque encontrado para monitoramento offline.")
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
                logger.error(f"Erro ao buscar estruturas ativas no Postgres para offline_check: {e}")
            finally:
                pg_conn.close()

        estruturas_map = get_all_estruturas_map()

        logger.info("Encontrados %d tanques para verificar.", len(results))

        for tank, last_reading_str in sorted(results):
            if not tank: continue

            # Filtra apenas se houver conexão bem-sucedida e o tanque não estiver ativo
            uid = estruturas_map.get(tank)
            if estruturas_ativas is not None and (not uid or uid not in estruturas_ativas):
                logger.info("Ignorando verificação offline para %s (Lote inativo)", tank)
                continue

            if last_reading_str:
                try:
                    last_reading_time = datetime.strptime(last_reading_str, '%Y-%m-%d %H:%M:%S')
                    time_difference = datetime.now() - last_reading_time
                    diff_minutos = int(time_difference.total_seconds() / 60)

                    logger.info("Verificando %s:", tank)
                    logger.info("   • Última leitura: %s", last_reading_str)
                    logger.info("   • Atraso atual: %d minutos", diff_minutos)

                    if diff_minutos > MINUTOS_OFFLINE_ALERTA:
                        logger.warning("   🚨 STATUS: OFFLINE (Limite de %d min excedido!)", MINUTOS_OFFLINE_ALERTA)
                        message = (
                            f"⚠️ *Alerta: Sistema OFFLINE!* ⚠️\n\n"
                            f"*Tanque:* {tank}\n"
                            f"*Última leitura:* `{last_reading_str}`\n"
                            f"O sistema não registra dados há mais de {MINUTOS_OFFLINE_ALERTA} minutos."
                        )
                        send_telegram_message(message)
                        logger.info("   ✅ Notificação enviada para o Telegram.")
                    else:
                        logger.info("   🟢 STATUS: ONLINE (Dentro do limite)")
                
                except ValueError:
                    logger.error("   Erro: Formato de timestamp inválido para o tanque %s: %s", tank, last_reading_str)
            else:
                logger.info("🔍 Verificando %s: ❓ Sem leituras recentes encontradas.", tank)
                send_telegram_message(f"❓ *Aviso:* Tanque {tank} cadastrado, mas sem leituras recentes.")

    except Exception as e:
        logger.error("Erro Inesperado no monitoramento offline: %s", e)
    finally:
        if conn:
            conn.close()
    
    logger.info("--- Verificação Finalizada ---")

if __name__ == "__main__":
    # Configuração básica de logging para execução direta
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    # Para executar do root: python3 -m src.alerts.offline_check
    check_last_reading()
