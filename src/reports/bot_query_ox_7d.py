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

from src.services.database import get_sqlite_connection  # noqa: E402
from src.services.notification import send_telegram_photo, send_telegram_message  # noqa: E402

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

os.makedirs('logs', exist_ok=True)
os.makedirs('reports', exist_ok=True)

# --- CONFIGURAÇÕES DE LOGGING ---
LOG_FILE = os.path.join(os.environ.get("LOGS_DIR", "logs"), "bot_query_ox_7d.log")
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
LIMITE_O2 = 2.0

def get_weekly_report():
    logger.info("Iniciando geração de relatório semanal de oxigênio (7 dias).")
    now = datetime.now()
    seven_days_ago = now - timedelta(days=7)

    conn = None
    try:
        conn = get_sqlite_connection()
        if conn is None:
            logger.error("Erro: Não foi possível conectar ao banco de dados SQLite.")
            send_telegram_message("❌ Erro ao gerar relatório de oxigênio (7 dias): falha na conexão com o BD.")
            return

        query = f"""
            SELECT tanque as nome_estrutura, oxigenio, timestamp_site
            FROM leituras
            WHERE timestamp_site >= '{seven_days_ago.strftime('%Y-%m-%d %H:%M:%S')}'
            ORDER BY timestamp_site ASC
        """
        df = pd.read_sql_query(query, conn)

        if df.empty:
            logger.info(f"Nenhum dado encontrado desde {seven_days_ago} para o relatório de oxigênio (7 dias).")
            send_telegram_message("ℹ️ Nenhum dado de oxigênio encontrado nos últimos 7 dias.", chat_id=CHAT_ID_FROM_ARGS)
            return

        df['timestamp_site'] = pd.to_datetime(df['timestamp_site'])

        # --- AJUSTE DE EIXO DINÂMICO ---
        v_min, v_max = df['oxigenio'].min(), df['oxigenio'].max()

        plt.style.use('seaborn-v0_8-darkgrid')
        plt.figure(figsize=(10, 5))

        msg = f"🗓️ *Resumo Semanal Oxigênio*\nPeríodo: 7 dias\n"

        # Agrupamos por tanque para iterar apenas uma vez sobre os dados
        for tank, struct_data in df.groupby('nome_estrutura'):
            if not tank or struct_data.empty: continue
            
            # Plotagem
            plt.plot(struct_data['timestamp_site'], struct_data['oxigenio'], label=tank, linewidth=1.5)
            # Estatísticas para a mensagem
            msg += f"\n📍 *{tank}*\nMín: `{struct_data['oxigenio'].min():.2f}` | Máx: `{struct_data['oxigenio'].max():.2f}`"

        plt.axhline(y=LIMITE_O2, color='red', linestyle='--', alpha=0.4, label="Limite Crítico")
        plt.ylim(max(0, v_min - 0.5), v_max + 0.5)
        
        plt.title('Historico de Oxigenio (Ultimos 7 Dias)')
        plt.xlabel('Hora')
        plt.ylabel('Mg/L')
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.legend(loc='upper left')
        plt.tight_layout()

        plot_path = os.path.join(REPORT_DIR, 'ox_7d_trend.png')
        if not os.path.exists(REPORT_DIR):
            os.makedirs(REPORT_DIR)
        plt.savefig(plot_path, dpi=100)
        plt.close()
        logger.info(f"Gráfico de tendência de oxigênio (7 dias) salvo em {plot_path}")

        send_telegram_photo(msg, plot_path, chat_id=CHAT_ID_FROM_ARGS)
        logger.info("Relatório de oxigênio (7 dias) enviado para o Telegram.")

    except Exception as e:
        logger.error(f"ERRO CRITICO ao gerar relatório de oxigênio (7 dias): {e}", exc_info=True)
        send_telegram_message(f"❌ Erro crítico ao gerar relatório de oxigênio (7 dias): {e}", chat_id=CHAT_ID_FROM_ARGS)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    get_weekly_report()

