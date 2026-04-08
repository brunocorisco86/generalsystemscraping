import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import requests
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
LOG_FILE = os.path.join(os.environ.get("LOGS_DIR", "logs"), "bot_query_ox_15d.log")
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

def get_fortnightly_report():
    logger.info("Iniciando geração de relatório quinzenal de oxigênio (15 dias).")
    now = datetime.now()
    fifteen_days_ago = now - timedelta(days=15)

    conn = None
    try:
        conn = get_sqlite_connection()
        if conn is None:
            logger.error("Erro: Não foi possível conectar ao banco de dados SQLite.")
            send_telegram_message(f"❌ Erro ao gerar relatório de oxigênio (15 dias): falha na conexão com o BD.", chat_id=CHAT_ID_FROM_ARGS)
            return

        query = f"SELECT tanque, oxigenio, timestamp_site FROM leituras WHERE timestamp_site >= '{fifteen_days_ago.strftime('%Y-%m-%d %H:%M:%S')}' ORDER BY timestamp_site ASC"
        df = pd.read_sql_query(query, conn)

        if df.empty:
            logger.info(f"Nenhum dado encontrado desde {fifteen_days_ago} para o relatório de oxigênio (15 dias).")
            send_telegram_message("ℹ️ Nenhum dado de oxigênio encontrado nos últimos 15 dias.", chat_id=CHAT_ID_FROM_ARGS)
            return

        df['timestamp_site'] = pd.to_datetime(df['timestamp_site'])
        
        plt.style.use('seaborn-v0_8-darkgrid')
        plt.figure(figsize=(14, 8))
        
        # 1. Trazer o limiar inferior de 2.0 mg/L
        plt.axhline(y=2.0, color='red', linestyle='--', linewidth=2, label='Limiar Crítico (2.0 mg/L)', alpha=0.7)

        for tank in sorted(df['tanque'].unique()):
            tank_df = df[df['tanque'] == tank].copy()
            if not tank_df.empty:
                tank_df.set_index('timestamp_site', inplace=True)
                
                # Plot dos dados brutos (linha fina e transparente para não poluir)
                plt.plot(tank_df.index, tank_df['oxigenio'], label=f'Bruto: {tank}', linewidth=0.8, alpha=0.5)

                # 2. Média móvel da máxima e mínima diária
                # Agrupamos por dia ('D') pegando os extremos
                daily_stats = tank_df['oxigenio'].resample('D').agg(['min', 'max'])
                
                # Calculamos a média móvel (rolling) de 3 dias para suavizar
                # center=True ajuda a alinhar a média ao meio do período no plot
                daily_stats['min_moving'] = daily_stats['min'].rolling(window=3, min_periods=1, center=True).mean()
                daily_stats['max_moving'] = daily_stats['max'].rolling(window=3, min_periods=1, center=True).mean()

                # Plot das Médias Móveis
                plt.plot(daily_stats.index, daily_stats['max_moving'], '--', label=f'Tendência Máx {tank}', linewidth=2)
                plt.plot(daily_stats.index, daily_stats['min_moving'], ':', label=f'Tendência Mín {tank}', linewidth=2)

        # Ajustes de Eixo
        v_min = min(1.5, df['oxigenio'].min()) # Garante que o 2.0 apareça bem
        v_max = df['oxigenio'].max()
        plt.ylim(max(0, v_min - 0.5), v_max + 1.0)
        
        plt.title('Histórico de Oxigênio (15 Dias) - Tendências Diárias e Alertas')
        plt.ylabel('Oxigênio (mg/L)')
        plt.xlabel('Data')
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.legend(loc='upper left', bbox_to_anchor=(1, 1)) # Legenda fora do gráfico
        plt.tight_layout()

        plot_path = os.path.join(REPORT_DIR, 'ox_15d_trend.png')
        if not os.path.exists(REPORT_DIR):
            os.makedirs(REPORT_DIR)
        plt.savefig(plot_path, dpi=100)
        plt.close()
        logger.info(f"Gráfico de tendência de oxigênio (15 dias) salvo em {plot_path}")

        msg = f"📅 *Histórico Quinzenal*\n📍 Análise de 15 dias finalizada.\n⚠️ Limiar crítico monitorado em 2.0 mg/L."
        send_telegram_photo(msg, plot_path, chat_id=CHAT_ID_FROM_ARGS)
        logger.info("Relatório de oxigênio (15 dias) enviado para o Telegram.")

    except Exception as e:
        logger.error(f"ERRO CRITICO ao gerar relatório de oxigênio (15 dias): {e}", exc_info=True)
        send_telegram_message(f"❌ Erro crítico ao gerar relatório de oxigênio (15 dias): {e}", chat_id=CHAT_ID_FROM_ARGS)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    get_fortnightly_report()
