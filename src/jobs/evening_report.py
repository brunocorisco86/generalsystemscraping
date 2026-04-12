import os
import glob
import logging
from datetime import datetime
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from dotenv import load_dotenv

# Adicionar o caminho do projeto ao sys.path para permitir importações do src
import sys
# Adicionar o caminho do projeto ao sys.path para permitir importações do src
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)


from src.services.database import get_sqlite_connection  # noqa: E402
from src.services.notification import send_telegram_photo  # noqa: E402

# Configuração do logger
logger = logging.getLogger(__name__)

# --- CONFIGURAÇÕES ---
load_dotenv()
REPORT_DIR = os.environ.get("REPORTS_DIR", "reports")
NOVO_LIMITE = 1.5  # mg/L para o modo Vigília

def generate_evening_report():
    """
    Gera um relatório de final de tarde com um gráfico do nível de oxigênio
    e envia para o Telegram.
    """
    if not os.path.exists(REPORT_DIR):
        os.makedirs(REPORT_DIR)
    
    # Limpa relatórios antigos
    for f in glob.glob(os.path.join(REPORT_DIR, 'evening_*')):
        try:
            os.remove(f)
        except OSError as e:
            logger.error("Erro ao remover arquivo antigo %s: %s", f, e)

    now = datetime.now()
    start_time = now.replace(hour=16, minute=0, second=0, microsecond=0)

    conn = None
    try:
        conn = get_sqlite_connection()
        if conn is None:
            logger.error("Erro: Não foi possível conectar ao banco de dados SQLite.")
            return

        query = f"""
            SELECT tanque, oxigenio, temperatura, timestamp_site
            FROM leituras
            WHERE timestamp_site >= '{start_time.strftime('%Y-%m-%d %H:%M:%S')}'
            ORDER BY timestamp_site ASC
        """
        df = pd.read_sql_query(query, conn)

        if df.empty:
            logger.warning("Nenhum dado encontrado para o relatório da noite.")
            return

        df['timestamp_site'] = pd.to_datetime(df['timestamp_site'])

        # --- GERAÇÃO DO PLOT ---
        plt.style.use('seaborn-v0_8-darkgrid')
        plt.figure(figsize=(12, 6))
        plt.axhline(y=NOVO_LIMITE, color='red', linestyle='--', label=f'Alerta Vigília ({NOVO_LIMITE} mg/L)')

        analysis_text = (
            "🌙 *MUDANÇA PARA MODO VIGÍLIA*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Encerrando relatórios detalhados. A partir de agora, as notificações serão **ultra-simplificadas** (1 linha) para facilitar a leitura noturna.\n\n"
            f"📢 *CONFIGURAÇÃO:* Alerta crítico reajustado para *{NOVO_LIMITE} mg/L*.\n\n"
            f"📊 *Resumo da Tarde (16h ➔ {now.strftime('%H:%M')}):*\n"
        )

        for tank in sorted(df['tanque'].unique()):
            tank_data = df[df['tanque'] == tank]
            if not tank_data.empty:
                plt.plot(tank_data['timestamp_site'], tank_data['oxigenio'], label=f'{tank}', marker='o', markersize=3, linestyle='-')
                o2_atual = tank_data['oxigenio'].iloc[-1]
                temp_atual = tank_data['temperatura'].iloc[-1]
                analysis_text += f"🐟 *{tank}:* `{o2_atual:.1f}` mg/L | `{temp_atual:.1f}°C`\n"

        plt.title(f'Fechamento de Ciclo Diário - {now.strftime("%d/%m/%Y")}')
        plt.xlabel('Hora')
        plt.ylabel('Oxigênio (mg/L)')
        plt.legend()
        plt.grid(True, which='both', linestyle='--', linewidth=0.5)
        plt.tight_layout()

        plot_path = os.path.join(REPORT_DIR, 'evening_plot.png')
        plt.savefig(plot_path, dpi=100)
        plt.close()

        # Envia a foto para o Telegram usando o serviço centralizado
        send_telegram_photo(analysis_text, plot_path)
        logger.info("Relatório noturno gerado e enviado com sucesso para %s.", plot_path)

    except Exception as e:
        logger.error("Erro no fechamento: %s", e)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Configuração básica de logging para execução direta
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    generate_evening_report()

