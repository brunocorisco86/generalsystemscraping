import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
import statistics
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
LOG_FILE = os.path.join(os.environ.get("LOGS_DIR", "logs"), "bot_query_temp.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- CONFIGURAÇÕES DO SCRIPT ---
REPORT_DIR = os.environ.get("REPORTS_DIR", "reports")
CHAT_ID_FROM_ARGS = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("TELEGRAM_CHAT_ID")

def get_bot_report():
    logger.info("Iniciando geração de relatório de temperatura.")
    now = datetime.now()
    twelve_hours_ago = now - timedelta(hours=12)
    
    conn = None
    try:
        # 1. CONECTAR AO BANCO
        conn = get_sqlite_connection()
        if conn is None:
            logger.error("Erro: Não foi possível conectar ao banco de dados SQLite.")
            send_telegram_message("❌ Erro ao gerar relatório de temperatura: falha na conexão com o BD.")
            return

        query = f"""
            SELECT tanque as nome_estrutura, temperatura, timestamp_site 
            FROM leituras 
            WHERE timestamp_site >= '{twelve_hours_ago.strftime('%Y-%m-%d %H:%M:%S')}' 
            ORDER BY timestamp_site ASC
        """
        df = pd.read_sql_query(query, conn)

        if df.empty:
            logger.info(f"Nenhum dado encontrado desde {twelve_hours_ago} para o relatório de temperatura.")
            send_telegram_message("ℹ️ Nenhum dado de temperatura encontrado nas últimas 12h.")
            return

        df['timestamp_site'] = pd.to_datetime(df['timestamp_site'])

        # 2. GERAR GRÁFICO E CONSTRUIR MENSAGEM
        plt.style.use('seaborn-v0_8-darkgrid')
        plt.figure(figsize=(10, 5))
        
        # 3. CONSTRUIR MENSAGEM
        msg = f"🌡️ *Relatório {now.strftime('%H:%M')}h*\n"

        for tank, struct_data in df.groupby('nome_estrutura'):
            if not tank or struct_data.empty: continue

            # Plotagem
            plt.plot(struct_data['timestamp_site'], struct_data['temperatura'], label=tank, linewidth=2)

            # Dados para a mensagem (últimas 4 leituras)
            struct_last_data = struct_data.tail(4)
            if struct_last_data.empty: continue

            temp_atual = struct_last_data['temperatura'].iloc[-1]
            avg_4 = struct_last_data['temperatura'].mean()
            ts_site = struct_last_data['timestamp_site'].iloc[-1]

            std_dev = statistics.stdev(struct_last_data['temperatura']) if len(struct_last_data) > 1 else 0
            cv = (std_dev / avg_4) if avg_4 > 0 else 0

            conf_emoji = "🛡️" if cv < 0.15 else "⚠️"
            trend = "📈" if temp_atual >= avg_4 else "📉"
            hora_f = ts_site.strftime('%H:%M')

            msg += f"\n📍 *{tank}*\n"
            msg += f"Temperatura: `{temp_atual:.2f}ºC` {trend}\n"
            msg += f"Md4: `{avg_4:.2f}ºC` | ⌚{hora_f} {conf_emoji}\n"

        plt.title('Tendencia de Temperatura (Ultimas 12h)')
        plt.xlabel('Hora')
        plt.ylabel('ºC')
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.legend()
        plt.tight_layout()
        
        plot_path = os.path.join(REPORT_DIR, 'bot_temp_trend.png')
        plt.savefig(plot_path, dpi=100)
        plt.close()
        
        send_telegram_photo(msg, plot_path, chat_id=CHAT_ID_FROM_ARGS)
        logger.info("Relatório de temperatura enviado para o Telegram.")

    except Exception as e:
        logger.error(f"ERRO CRITICO ao gerar relatório de temperatura: {e}", exc_info=True)
        send_telegram_message(f"❌ Erro crítico ao gerar relatório de temperatura: {e}", chat_id=CHAT_ID_FROM_ARGS)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    get_bot_report()
