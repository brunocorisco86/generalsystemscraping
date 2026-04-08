import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import requests
import os
from datetime import datetime, timedelta

# --- CONFIGURAÇÕES ---
DB_PATH = '/home/dietpi/piscicultura_monitor/piscicultura_dados.db'
REPORT_DIR = '/home/dietpi/piscicultura_monitor/reports'
TELEGRAM_TOKEN = "8355153356:AAG55aFGL153Uzwo4w48uj1_vDV8BC2sim4"
TELEGRAM_CHAT_ID = "-1003744398479"
LIMITE_TRATO = 3.0

def send_telegram(text, photo_path=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/"
    if photo_path:
        with open(photo_path, 'rb') as photo:
            requests.post(url + "sendPhoto", data={'chat_id': TELEGRAM_CHAT_ID, 'caption': text, 'parse_mode': 'Markdown'}, files={'photo': photo})
    else:
        requests.post(url + "sendMessage", data={'chat_id': TELEGRAM_CHAT_ID, 'text': text, 'parse_mode': 'Markdown'})

def run_production_logic():
    agora = datetime.now()
    
    # CONSTRAINT: Só envia mensagem entre 07h e 09h
    if not (7 <= agora.hour < 9):
        print(f"Fora do horário de envio (07h-09h): {agora.strftime('%H:%M')}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        inicio_view = agora - timedelta(hours=15)
        query = f"SELECT tanque, oxigenio, timestamp_site FROM leituras WHERE timestamp_site BETWEEN '{inicio_view}' AND '{agora}' ORDER BY timestamp_site ASC"
        df = pd.read_sql_query(query, conn)
        conn.close()

        if df.empty: return
        df['timestamp_site'] = pd.to_datetime(df['timestamp_site'])
        
        tank_groups = df.groupby('tanque')
        status_check = {}
        tank_results = []
        
        # 1. Verificação Rápida de Status
        for tank, tdf in tank_groups:
            tdf['o2_smooth'] = tdf['oxigenio'].rolling(window=5, center=True).mean().fillna(tdf['oxigenio'])
            last_o2 = tdf['o2_smooth'].iloc[-1]
            status_check[tank] = last_o2
            tank_results.append({'tank': tank, 'df': tdf, 'last_o2': last_o2})

        # SE TODOS ESTIVEREM ACIMA DE 3.0 -> SÓ TEXTO
        if all(val >= LIMITE_TRATO for val in status_check.values()):
            msg = "🐟 *Aviso de Arraçoamento*\n\n"
            for t, val in status_check.items():
                msg += f"✅ *{t}:* `{val:.2f}` mg/L. Liberado para tratar!\n"
            send_telegram(msg)
            return

        # 2. LOGICA DE PROJEÇÃO (Se algum estiver abaixo de 3.0)
        inicio_calc = agora - timedelta(minutes=90)
        meio_dia = agora.replace(hour=12, minute=0, second=0, microsecond=0)
        best_accel_coeffs = None
        max_gain = -999

        # Encontrar Tanque Líder
        for item in tank_results:
            calc_df = item['df'][item['df']['timestamp_site'] >= inicio_calc].copy()
            if len(calc_df) < 3: continue
            calc_df['t_min'] = (calc_df['timestamp_site'] - inicio_calc).dt.total_seconds() / 60
            coeffs = np.polyfit(calc_df['t_min'], calc_df['o2_smooth'], 2)
            current_gain = coeffs[0] * 120 + coeffs[1]
            if current_gain > max_gain:
                max_gain = current_gain
                best_accel_coeffs = coeffs

        # Plotagem Equalizada
        plt.figure(figsize=(12, 7))
        colors = {'Tanque 1': '#1f77b4', 'Tanque 2': '#ff7f0e'}
        analysis_text = f"📈 *Previsão do Horário de Arraçoamento*\n📅 {agora.strftime('%H:%M')}\n\n"

        for item in tank_results:
            tank, tdf, last_o2 = item['tank'], item['df'], item['last_o2']
            color = colors.get(tank, 'gray')
            p_model = np.poly1d(best_accel_coeffs)
            t_start = (agora - inicio_calc).total_seconds() / 60
            future_t = np.linspace(t_start, (meio_dia - inicio_calc).total_seconds() / 60, 100)
            future_o2 = p_model(future_t) + (last_o2 - p_model(t_start))
            future_times = [inicio_calc + timedelta(minutes=float(m)) for m in future_t]

            hora_trato = " > 12:00"
            for tm, val in zip(future_t, future_o2):
                if val >= LIMITE_TRATO:
                    trato_dt = inicio_calc + timedelta(minutes=float(tm))
                    hora_trato = trato_dt.strftime('%H:%M')
                    plt.axvline(x=trato_dt, color=color, linestyle=':', alpha=0.5)
                    break

            analysis_text += f"🐟 *{tank}:* `{last_o2:.2f}` mg/L -> `{hora_trato}`\n"
            plt.plot(tdf['timestamp_site'], tdf['oxigenio'], 'o', alpha=0.1, color=color)
            plt.plot(tdf['timestamp_site'], tdf['o2_smooth'], '-', color=color, label=f'{tank}')
            plt.plot(future_times, future_o2, '--', color=color, label=f'Proj. {tank}')

        plt.axhline(y=LIMITE_TRATO, color='green', linestyle='-', alpha=0.3)
        plt.title('Estimativa de Recuperação de O2')
        plt.legend(loc='lower right')
        plt.tight_layout()

        if not os.path.exists(REPORT_DIR): os.makedirs(REPORT_DIR)
        plot_path = os.path.join(REPORT_DIR, 'trato_hoje.png')
        plt.savefig(plot_path)
        plt.close()
        
        send_telegram(analysis_text, plot_path)

    except Exception as e: print(f"Erro: {e}")

if __name__ == "__main__":
    run_production_logic()
