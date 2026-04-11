import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# --- CONFIGURAÇÕES ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DB_PATH = os.environ.get("SQLITE_DB_PATH", os.path.join(PROJECT_ROOT, "data/piscicultura_dados.db"))
REPORT_DIR = os.environ.get("REPORT_DIR", os.path.join(PROJECT_ROOT, "reports"))
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
LIMITE_SEGURANCA = float(os.environ.get("OX_LIMITE_SEGURANCA", 2.0))

def get_historical_value(tanque, target_datetime):
    try:
        # Se o caminho for relativo, garante que seja absoluto a partir da raiz do projeto
        db_path_abs = DB_PATH if os.path.isabs(DB_PATH) else os.path.join(PROJECT_ROOT, DB_PATH)
        conn = sqlite3.connect(db_path_abs)
        start_search = target_datetime - timedelta(minutes=15)
        end_search = target_datetime + timedelta(minutes=15)
        query = f"SELECT oxigenio FROM leituras WHERE tanque = '{tanque}' AND timestamp_site BETWEEN '{start_search}' AND '{end_search}' ORDER BY ABS(strftime('%s', timestamp_site) - strftime('%s', '{target_datetime}')) LIMIT 1"
        res = conn.execute(query).fetchone()
        conn.close()
        return res[0] if res else None
    except: return None

def generate_prediction():
    now = datetime.now().replace(second=0, microsecond=0)
    start_history = now - timedelta(days=5)
    target_time_today = now.replace(hour=22, minute=0)
    yesterday_now = now - timedelta(days=1)

    try:
        conn = sqlite3.connect(DB_PATH)
        query = f"SELECT tanque, oxigenio, timestamp_site FROM leituras WHERE timestamp_site >= '{start_history}' ORDER BY timestamp_site ASC"
        df = pd.read_sql_query(query, conn)
        conn.close()

        if df.empty: return
        df['timestamp_site'] = pd.to_datetime(df['timestamp_site'])
        
        plt.figure(figsize=(12, 7))
        
        # Saudação ajustada para o grupo
        analysis_text = (
            f"📢 *Informativo Diário de Monitoramento (17h)*\n"
            f"Previsão do oxigênio com base em dado histórico recente.\n"
            f"📅 *Data:* {now.strftime('%d/%m %H:%M')}\n\n"
        )

        colors = {'Tanque 1': '#1f77b4', 'Tanque 2': '#ff7f0e'}

        for tank in df['tanque'].unique():
            tank_df = df[df['tanque'] == tank].copy()
            o2_agora = tank_df['oxigenio'].iloc[-1]
            time_agora = tank_df['timestamp_site'].iloc[-1]
            o2_mesmo_horario_ontem = get_historical_value(tank, yesterday_now)
            
            # --- LÓGICA DE FORECAST EXPONENCIAL ---
            # Tempo restante em horas
            horas_para_prever = (target_time_today - time_agora).total_seconds() / 3600
            
            # Calculamos a taxa de queda nas últimas 2 horas
            recent = tank_df[tank_df['timestamp_site'] >= (now - timedelta(hours=2))]
            if len(recent) > 1:
                taxa_queda = (recent['oxigenio'].iloc[0] - o2_agora) / 2
                taxa_queda = max(taxa_queda, 0.66) # Garante queda mínima conservadora
            else:
                taxa_queda = 0.65
            
            # Curva Exponencial: O2(t) = O2_atual * e^(-k*t)
            # k é a constante de decaimento baseada na taxa de queda atual
            k = taxa_queda / max(o2_agora, 0.1)
            
            # Gerar pontos da curva para o gráfico
            future_times = [time_agora + timedelta(minutes=10*i) for i in range(int(horas_para_prever*6)+1)]
            future_o2 = [o2_agora * np.exp(-k * (t - time_agora).total_seconds()/3600) for t in future_times]
            o2_predito = future_o2[-1]

            # Plotagem
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
        plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
        plt.grid(True, alpha=0.2)
        plt.tight_layout()
        
        plot_path = os.path.join(REPORT_DIR, 'forecast_exp.png')
        plt.savefig(plot_path)
        plt.close()

        send_to_telegram(analysis_text, plot_path)

    except Exception as e: print(f"Erro: {e}")

def send_to_telegram(text, photo_path):
    with open(photo_path, 'rb') as photo:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto", data={'chat_id': TELEGRAM_CHAT_ID, 'caption': text, 'parse_mode': 'Markdown'}, files={'photo': photo})

if __name__ == "__main__":
    generate_prediction()
