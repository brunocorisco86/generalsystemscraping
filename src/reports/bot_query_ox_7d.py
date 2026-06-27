import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
import sys
import logging
import pytz
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Adicionar o caminho do projeto ao sys.path para permitir importações do src
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

from src.services.database import get_sqlite_connection, get_postgres_connection, get_all_estruturas_map  # noqa: E402
from src.services.notification import send_telegram_photo, send_telegram_message  # noqa: E402
from src.bots.agent import analyze_custom_report_sync  # noqa: E402

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
    # Forçar fuso horário local (GMT-3)
    tz = pytz.timezone('America/Sao_Paulo')
    now = datetime.now(tz)
    seven_days_ago = now - timedelta(days=7)

    conn = None
    try:
        conn = get_sqlite_connection()
        if conn is None:
            logger.error("Erro: Não foi possível conectar ao banco de dados SQLite.")
            send_telegram_message("❌ Erro ao gerar relatório de oxigênio (7 dias): falha na conexão com o BD.")
            return

        query = """
            SELECT nome_estrutura, oxigenio, timestamp_site
            FROM leituras
            WHERE timestamp_site >= ?
            ORDER BY timestamp_site ASC
        """
        df = pd.read_sql_query(query, conn, params=(seven_days_ago.strftime('%Y-%m-%d %H:%M:%S'),))

        if df.empty:
            logger.info(f"Nenhum dado encontrado desde {seven_days_ago} para o relatório de oxigênio (7 dias).")
            send_telegram_message("ℹ️ Nenhum dado de oxigênio encontrado nos últimos 7 dias.", chat_id=CHAT_ID_FROM_ARGS)
            return

        df['timestamp_site'] = pd.to_datetime(df['timestamp_site'])

        # --- FILTRAGEM DE LOTES ATIVOS (PostgreSQL) ---
        estruturas_ativas = None
        pg_conn = get_postgres_connection()
        if pg_conn:
            try:
                pg_cur = pg_conn.cursor()
                pg_cur.execute("SELECT estrutura_uid FROM lotes WHERE data_abate IS NULL")
                estruturas_ativas = {r[0] for r in pg_cur.fetchall()}
            except Exception as e:
                logger.error(f"Erro ao buscar estruturas ativas no Postgres: {e}")
            finally:
                pg_conn.close()

        estruturas_map = get_all_estruturas_map()

        # --- AJUSTE DE EIXO DINÂMICO ---
        v_min, v_max = df['oxigenio'].min(), df['oxigenio'].max()

        plt.style.use('seaborn-v0_8-darkgrid')
        plt.figure(figsize=(10, 5))

        msg = "🗓️ *Resumo Semanal Oxigênio*\nPeríodo: 7 dias\n"

        # Agrupamos por estrutura para iterar apenas uma vez sobre os dados
        for tank, struct_data in df.groupby('nome_estrutura'):
            if not tank or struct_data.empty:
                continue

            uid = estruturas_map.get(tank)
            if estruturas_ativas is not None and (not uid or uid not in estruturas_ativas):
                logger.info("Ignorando tanque %s (Lote inativo)", tank)
                continue
            
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

        # --- CONSULTA AO ESPECIALISTA (IA) ---
        logger.info("Solicitando parecer do especialista...")
        parecer_ia = analyze_custom_report_sync(
            "Relatório Semanal de Oxigênio (7 Dias)", 
            msg, 
            df.to_csv(index=False)
        )
        if parecer_ia:
            msg += f"\n🤖 *Parecer do Especialista:*\n{parecer_ia}\n"

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

