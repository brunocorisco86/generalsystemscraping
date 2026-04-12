import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
import sys
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Adicionar o caminho do projeto ao sys.path para permitir importações do src
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

from src.services.database import get_sqlite_connection
from src.services.notification import send_telegram_photo, send_telegram_message

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# --- CONFIGURAÇÕES DE LOGGING ---
LOG_FILE = os.path.join(os.environ.get("LOGS_DIR", "logs"), "bot_query_temp_7d.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler() # Para também mostrar no console/stdout
    ]
)
logger = logging.getLogger(__name__)

# --- CONFIGURAÇÕES DO SCRIPT ---
REPORT_DIR = os.environ.get("REPORTS_DIR", "reports")
# ChatID vindo do Node-RED ou padrão (usar o padrão do .env se não for fornecido)
CHAT_ID_FROM_ARGS = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("TELEGRAM_CHAT_ID")

def get_weekly_temp_report():
    logger.info("Iniciando geração de relatório semanal de temperatura (7 dias).")
    now = datetime.now()
    seven_days_ago = now - timedelta(days=7)

    conn = None
    try:
        # 1. CONECTAR AO BANCO
        conn = get_sqlite_connection()
        if conn is None:
            logger.error("Erro: Não foi possível conectar ao banco de dados SQLite.")
            send_telegram_message("❌ Erro ao gerar relatório de temperatura (7 dias): falha na conexão com o BD.", chat_id=CHAT_ID_FROM_ARGS)
            return

        query = f"""
            SELECT tanque, temperatura, timestamp_site
            FROM leituras
            WHERE timestamp_site >= '{seven_days_ago.strftime('%Y-%m-%d %H:%M:%S')}'
            ORDER BY timestamp_site ASC
        """
        df = pd.read_sql_query(query, conn)

        if df.empty:
            logger.info(f"Nenhum dado de temperatura encontrado desde {seven_days_ago} para o relatório de temperatura.")
            send_telegram_message("ℹ️ Nenhum dado de temperatura encontrado nos últimos 7 dias.", chat_id=CHAT_ID_FROM_ARGS)
            return

        df['timestamp_site'] = pd.to_datetime(df['timestamp_site'])

        # --- AJUSTE DE EIXO DINÂMICO ---
        v_min, v_max = df['temperatura'].min(), df['temperatura'].max()

        # 2. GERAR GRÁFICO E CONSTRUIR MENSAGEM (UNIFICADO)
        plt.style.use('seaborn-v0_8-darkgrid')
        plt.figure(figsize=(10, 5))

        msg = "🌡️ *Resumo Semanal Temperatura*\nPeríodo: 7 dias\n"

        for tank, tank_df in df.groupby('tanque'):
            if not tank_df.empty:
                # Plotagem
                plt.plot(tank_df['timestamp_site'], tank_df['temperatura'], label=tank, linewidth=1.5)

                # Mensagem
                msg += f"\n📍 *{tank}*\nMín: `{tank_df['temperatura'].min():.1f}ºC` | Máx: `{tank_df['temperatura'].max():.1f}ºC`"

        # Ajuste dinâmico para preencher a tela do smartwatch
        plt.ylim(v_min - 0.5, v_max + 0.5)

        plt.title('Historico de Temperatura (Ultimos 7 Dias)')
        plt.xlabel('Data')
        plt.ylabel('Graus Celsius')
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.legend(loc='upper left')
        plt.tight_layout()

        plot_path = os.path.join(REPORT_DIR, 'temp_7d_trend.png')
        if not os.path.exists(REPORT_DIR):
            os.makedirs(REPORT_DIR)
        plt.savefig(plot_path, dpi=100)
        plt.close()
        logger.info(f"Gráfico de tendência de temperatura (7 dias) salvo em {plot_path}")

        # 4. ENVIAR PARA o TELEGRAM
        send_telegram_photo(msg, plot_path, chat_id=CHAT_ID_FROM_ARGS)
        logger.info("Relatório de temperatura (7 dias) enviado para o Telegram.")

    except Exception as e:
        logger.error(f"ERRO CRITICO ao gerar relatório de temperatura (7 dias): {e}", exc_info=True)
        send_telegram_message(f"❌ Erro crítico ao gerar relatório de temperatura (7 dias): {e}", chat_id=CHAT_ID_FROM_ARGS)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    get_weekly_temp_report()
