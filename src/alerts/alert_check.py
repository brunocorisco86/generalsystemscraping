import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Importar serviços do projeto
from src.services.database import get_sqlite_connection
from src.services.notification import send_telegram_message

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
        # Nota: Usamos 'data_coleta' ou 'timestamp_site' dependendo da precisão desejada.
        # Aqui usamos data_coleta que é preenchido pelo nosso script de scraping.
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

        for tanque, oxigenio, temperatura in leituras:


        for tanque, oxigenio, temperatura in leituras:
            # Log de monitoramento
            logger.info("Verificando %s: %s Mg/L", tanque, oxigenio)

            # Dispara o alerta se estiver abaixo do limite
            if oxigenio < LIMITE_OXIGENIO_CRITICO:
                mensagem = (
                    f"🚨 *ALERTA CRÍTICO* 🚨\n\n"
                    f"📍 Tanque: *{tanque}*\n"
                    f"🔴 Oxigênio: *{oxigenio} Mg/L* 🔴\n"
                    f"🌡️ Temp: {temperatura}°C\n"
                    f"⏰ Hora: {datetime.now().strftime('%H:%M:%S')}"
                )
                send_telegram_message(mensagem)
                logger.info("Alerta enviado para %s (O2: %s)", tanque, oxigenio)

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
