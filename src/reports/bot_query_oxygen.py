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
LOG_FILE = os.path.join(os.environ.get("LOGS_DIR", "logs"), "bot_query_oxygen.log")
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

def get_bot_report():
    logger.info("Iniciando geração de relatório de oxigênio.")
    now = datetime.now()
    twelve_hours_ago = now - timedelta(hours=12)
    
    conn = None
    try:
        # 1. CONECTAR AO BANCO
        conn = get_sqlite_connection()
        if conn is None:
            logger.error("Erro: Não foi possível conectar ao banco de dados SQLite.")
            send_telegram_message("❌ Erro ao gerar relatório de oxigênio: falha na conexão com o BD.")
            return

        query = f"""
            SELECT tanque as nome_estrutura, oxigenio, timestamp_site 
            FROM leituras 
            WHERE timestamp_site >= '{twelve_hours_ago.strftime('%Y-%m-%d %H:%M:%S')}' 
            ORDER BY timestamp_site ASC
        """
        df = pd.read_sql_query(query, conn)

        if df.empty:
            logger.info(f"Nenhum dado encontrado desde {twelve_hours_ago} para o relatório de oxigênio.")
            send_telegram_message("ℹ️ Nenhum dado de oxigênio encontrado nas últimas 12h.")
            return

        df['timestamp_site'] = pd.to_datetime(df['timestamp_site'])

        # 2. GERAR GRÁFICO E CONSTRUIR MENSAGEM (UNIFICADO)
        plt.style.use('seaborn-v0_8-darkgrid')
        plt.figure(figsize=(10, 5))
        
        # 3. CONSTRUIR MENSAGEM (FOCO SMARTWATCH)
        msg = f"📊 *Relatório {now.strftime('%H:%M')}h*\n"

        # Agrupamos por estrutura para iterar apenas uma vez sobre os dados
        for tank, struct_data in df.groupby('nome_estrutura'):
            if not tank or struct_data.empty: continue

            # Plotagem
            plt.plot(struct_data['timestamp_site'], struct_data['oxigenio'], label=tank, linewidth=2)

            # Dados para a mensagem (últimas 4 leituras)
            struct_last_data = struct_data.tail(4)
            if struct_last_data.empty: continue

            o2_atual = struct_last_data['oxigenio'].iloc[-1]
            avg_4 = struct_last_data['oxigenio'].mean()
            ts_site = struct_last_data['timestamp_site'].iloc[-1]

            # Cálculo de Confiança (CV < 0.15)
            # Evita ZeroDivisionError
            std_dev = statistics.stdev(struct_last_data['oxigenio']) if len(struct_last_data) > 1 else 0
            cv = (std_dev / avg_4) if avg_4 > 0 else 0

            conf_emoji = "🛡️" if cv < 0.15 else "⚠️"
            trend = "📈" if o2_atual >= avg_4 else "📉"
            status = "🟢" if o2_atual >= LIMITE_O2 else "🔴"
            hora_f = ts_site.strftime('%H:%M')

            msg += f"\n📍 *{tank}*\n"
            msg += f"Oxigênio: `{o2_atual:.2f}` {trend} {status}\n"
            msg += f"Md4: `{avg_4:.2f}` | ⌚{hora_f} {conf_emoji}\n"

        plt.axhline(y=LIMITE_O2, color='red', linestyle='--', alpha=0.5, label="Limite Crítico")
        plt.title('Tendencia de O2 (Ultimas 12h)')
        plt.xlabel('Hora')
        plt.ylabel('Mg/L')
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.legend()
        plt.tight_layout()
        
        plot_path = os.path.join(REPORT_DIR, 'bot_oxygen_trend.png')
        if not os.path.exists(REPORT_DIR):
            os.makedirs(REPORT_DIR)
        plt.savefig(plot_path, dpi=100)
        plt.close()
        logger.info(f"Gráfico de tendência de oxigênio salvo em {plot_path}")

        # 4. ENVIAR PARA O TELEGRAM
        send_telegram_photo(msg, plot_path, chat_id=CHAT_ID_FROM_ARGS)
        logger.info("Relatório de oxigênio enviado para o Telegram.")

    except Exception as e:
        logger.error(f"ERRO CRITICO ao gerar relatório de oxigênio: {e}", exc_info=True)
        send_telegram_message(f"❌ Erro crítico ao gerar relatório de oxigênio: {e}", chat_id=CHAT_ID_FROM_ARGS)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    get_bot_report()

