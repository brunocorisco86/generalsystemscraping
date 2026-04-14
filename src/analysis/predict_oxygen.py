import os
import pandas as pd
import numpy as np
import matplotlib
import logging
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Importar serviços do projeto
from src.services.database import get_sqlite_connection
from src.services.notification import send_telegram_photo

# Configuração do logger
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# --- CONFIGURAÇÕES ---
REPORTS_DIR = os.environ.get("REPORTS_DIR", "reports")
LIMITE_SEGURANCA = float(os.environ.get("OX_LIMITE_SEGURANCA", 2.0))

def get_historical_value(tanque, target_datetime):
    conn = None
    try:
        conn = get_sqlite_connection()
        if not conn:
            return None
        start_search = target_datetime - timedelta(minutes=15)
        end_search = target_datetime + timedelta(minutes=15)
        query = f"SELECT oxigenio FROM leituras WHERE tanque = '{tanque}' AND timestamp_site BETWEEN '{start_search}' AND '{end_search}' ORDER BY ABS(strftime('%s', timestamp_site) - strftime('%s', '{target_datetime}')) LIMIT 1"
        res = conn.execute(query).fetchone()
        return res[0] if res else None
    except Exception as e:
        logger.error("Erro ao obter valor histórico para o tanque %s: %s", tanque, e)
        return None
    finally:
        if conn:
            conn.close()

def generate_prediction():
    now = datetime.now().replace(second=0, microsecond=0)
    start_history = now - timedelta(days=5)
    target_time_today = now.replace(hour=22, minute=0)
    yesterday_now = now - timedelta(days=1)

    conn = None
    try:
        conn = get_sqlite_connection()
        if not conn:
            return
        query = f"SELECT tanque, oxigenio, timestamp_site FROM leituras WHERE timestamp_site >= '{start_history}' ORDER BY timestamp_site ASC"
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        logger.error("Erro ao carregar dados para previsão: %s", e)
        return
    finally:
        if conn:
            conn.close()

    if df.empty:
        return
    df['timestamp_site'] = pd.to_datetime(df['timestamp_site'])

    plt.style.use('seaborn-v0_8-darkgrid')
    plt.figure(figsize=(12, 7))

    analysis_text = (
        f"📢 *Informativo Diário de Monitoramento (17h)*\n"
        f"Previsão do oxigênio com base em dado histórico recente.\n"
        f"📅 *Data:* {now.strftime('%d/%m %H:%M')}\n\n"
    )

    colors = {'Tanque 1': '#1f77b4', 'Tanque 2': '#ff7f0e'}

    for tank, tank_df in df.groupby('tanque'):
        o2_agora = tank_df['oxigenio'].iloc[-1]
        time_agora = tank_df['timestamp_site'].iloc[-1]
        o2_mesmo_horario_ontem = get_historical_value(tank, yesterday_now)

        # --- LÓGICA DE FORECAST EXPONENCIAL ---
        horas_para_prever = (target_time_today - time_agora).total_seconds() / 3600
        recent = tank_df[tank_df['timestamp_site'] >= (now - timedelta(hours=2))]
        if len(recent) > 1:
            taxa_queda = (recent['oxigenio'].iloc[0] - o2_agora) / 2
            taxa_queda = max(taxa_queda, 0.66)
        else:
            taxa_queda = 0.65

        k = taxa_queda / max(o2_agora, 0.1)
        future_times = [time_agora + timedelta(minutes=10*i) for i in range(int(horas_para_prever*6)+1)]
        future_o2 = [o2_agora * np.exp(-k * (t - time_agora).total_seconds()/3600) for t in future_times]
        o2_predito = future_o2[-1]

        color = colors.get(tank)
        plt.plot(tank_df['timestamp_site'], tank_df['oxigenio'], label=f'{tank} (Histórico)', color=color)
        plt.plot(future_times, future_o2, color=color, linestyle='--', label=f'Projeção {tank}')

        o2_ontem_22h = get_historical_value(tank, yesterday_now.replace(hour=22, minute=0))
        diff_str = f"({ '📈' if (o2_agora - o2_mesmo_horario_ontem) > 0 else '📉' } `{o2_agora - o2_mesmo_horario_ontem:+.2f}` vs ontem)" if o2_mesmo_horario_ontem else ""

        status = "🔴 *RISCO ALTO*" if o2_predito < LIMITE_SEGURANCA else "🟢 *ESTÁVEL*"
        analysis_text += (
            f"🐟 *{tank}:* {status}\n"
            f"   • Agora: `{o2_agora:.2f}` {diff_str}\n"
            f"   • Ontem (22h): `{o2_ontem_22h if o2_ontem_22h else 'N/A'}`\n"
            f"   • Previsão Hoje (22h): `{o2_predito:.2f}`\n"
            f"   • {'⚠️ *ACIONAR AERADORES!*' if o2_predito < LIMITE_SEGURANCA else '✅ Seguir cronograma.'}\n\n"
        )

    plt.axhline(y=LIMITE_SEGURANCA, color='red', linestyle='-', alpha=0.3, label='Limite Crítico')
    plt.title('Monitoramento e Projeção de Oxigênio (Decaimento Exponencial)')
    plt.legend(loc='upper right')
    plt.grid(True, alpha=0.2)
    plt.tight_layout()

    plot_path = os.path.join(REPORTS_DIR, 'forecast_exp.png')
    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR)
    plt.savefig(plot_path)
    plt.close()

    try:
        send_telegram_photo(analysis_text, plot_path)
    except Exception as e:
        logger.error("Erro ao enviar foto para o Telegram: %s", e)

if __name__ == "__main__":
    generate_prediction()

if __name__ == "__main__":
    generate_prediction()
