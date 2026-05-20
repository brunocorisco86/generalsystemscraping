import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Importar serviços do projeto
from src.services.database import get_sqlite_connection
from src.services.notification import send_telegram_photo, send_telegram_message
from src.bots.agent import analyze_feed_prediction_sync

# Carregar variáveis de ambiente
load_dotenv()

# --- CONFIGURAÇÕES ---
REPORTS_DIR = os.environ.get("REPORTS_DIR", "reports")
LIMITE_TRATO = float(os.environ.get("FEED_LIMITE_TRATO", 3.0))

def run_production_logic():
    agora = datetime.now()
    # CONSTRAINT: Só envia mensagem entre 07h e 09:59h
    if not (7 <= agora.hour < 10):
        print(f"Fora do horário de envio (07h-10h): {agora.strftime('%H:%M')}")
        return

    conn = None
    try:
        conn = get_sqlite_connection()
        if not conn: return
        
        # 1. Buscar Clima Atual (Temperatura Ambiente, Pressão, Umidade, Nuvens)
        cursor = conn.cursor()
        cursor.execute("SELECT temperatura, pressao, umidade, cloud_cover FROM clima_historico ORDER BY data_coleta DESC LIMIT 1")
        clima_row = cursor.fetchone()
        temp_ambiente, pressao, umidade, cloud_cover = clima_row if (clima_row and len(clima_row) == 4) else (clima_row[0], clima_row[1], clima_row[2], 0.0) if clima_row else (25.0, 1013.25, 70.0, 0.0)
        
        # Prepara resumo para o Agente (Micro-contexto otimizado)
        status_pres = "Estável" if pressao >= 1010 else ("Baixa" if pressao < 1005 else "Normal")
        status_cloud = f"{cloud_cover:.0f}% nublado"
        resumo_agente = f"Clima: {temp_ambiente:.1f}C, {umidade:.0f}%, {pressao:.1f}hPa ({status_pres}), {status_cloud}. "
        
        # Cabeçalho do Clima para o Telegram
        clima_header = f"🌤️ `{temp_ambiente:.1f}ºC` | ⏲️ `{pressao:.1f}hPa` | ☁️ `{cloud_cover:.0f}%`"

        # 2. Buscar Leituras (O2 e Temp Água)
        inicio_view = agora - timedelta(hours=15)
        query = f"SELECT nome_estrutura, oxigenio, temperatura, timestamp_site FROM leituras WHERE timestamp_site BETWEEN '{inicio_view}' AND '{agora}' ORDER BY timestamp_site ASC"
        df = pd.read_sql_query(query, conn)
        conn.close()

        if df.empty: return
        df['timestamp_site'] = pd.to_datetime(df['timestamp_site'])
        
        tank_groups = df.groupby('nome_estrutura')
        status_check = {}
        struct_results = []
        
        for tank, tdf in tank_groups:
            if not tank: continue
            tdf['o2_smooth'] = tdf['oxigenio'].rolling(window=5, center=True).mean().fillna(tdf['oxigenio'])
            last_o2 = tdf['o2_smooth'].iloc[-1]
            last_temp_agua = tdf['temperatura'].iloc[-1] if 'temperatura' in tdf.columns else 24.0
            status_check[tank] = last_o2
            struct_results.append({'tank': tank, 'df': tdf, 'last_o2': last_o2, 'temp_agua': last_temp_agua})

        tanks_info = []

        if all(val >= LIMITE_TRATO for val in status_check.values()):
            # Busca o parecer PRIMEIRO para decidir o tom da mensagem
            for t, val in status_check.items():
                temp_w = next(item['temp_agua'] for item in struct_results if item['tank'] == t)
                tanks_info.append(f"{t}: O2={val:.1f}, Temp={temp_w:.1f}C, Trato=LIBERADO_PELO_O2")
            
            parecer = analyze_feed_prediction_sync(resumo_agente + " | ".join(tanks_info))
            
            msg = f"🐟 *Aviso de Arraçoamento*\n{clima_header}\n"
            msg += f"\n💡 *Parecer do Especialista:*\n_{parecer}_\n\n"
            
            for t, val in status_check.items():
                temp_w = next(item['temp_agua'] for item in struct_results if item['tank'] == t)
                # Se o parecer contiver palavras de cautela ou o O2 estiver baixo/temp baixa, usa ⚠️
                if "suspender" in parecer.lower() or "reduzir" in parecer.lower() or val <= (LIMITE_TRATO + 0.5):
                    icon = "⚠️"
                else:
                    icon = "✅"
                msg += f"{icon} *{t}:* `{val:.2f}` mg/L | `{temp_w:.1f}ºC`.\n"
            
            send_telegram_message(msg)
            return

        inicio_calc = agora - timedelta(minutes=90)
        meio_dia = agora.replace(hour=12, minute=0, second=0, microsecond=0)
        best_accel_coeffs = None
        max_gain = -999

        for item in struct_results:
            calc_df = item['df'][item['df']['timestamp_site'] >= inicio_calc].copy()
            if len(calc_df) < 3: continue
            calc_df['t_min'] = (calc_df['timestamp_site'] - inicio_calc).dt.total_seconds() / 60
            coeffs = np.polyfit(calc_df['t_min'], calc_df['o2_smooth'], 2)
            current_gain = coeffs[0] * 120 + coeffs[1]
            if current_gain > max_gain:
                max_gain = current_gain
                best_accel_coeffs = coeffs

        plt.style.use('seaborn-v0_8-darkgrid')
        plt.figure(figsize=(12, 7))
        colors = {'Tanque 1': '#1f77b4', 'Tanque 2': '#ff7f0e'}
        analysis_text = f"📈 *Previsão do Horário de Arraçoamento*\n📅 {agora.strftime('%H:%M')}\n{clima_header}\n\n"

        for item in struct_results:
            tank, tdf, last_o2, temp_w = item['tank'], item['df'], item['last_o2'], item['temp_agua']
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

            analysis_text += f"🐟 *{tank}:* `{last_o2:.2f}` mg/L | `{temp_w:.1f}ºC` -> *{hora_trato}*\n"
            tanks_info.append(f"{tank}: O2={last_o2:.1f}, Temp={temp_w:.1f}C, Trato={hora_trato}")
            
            plt.plot(tdf['timestamp_site'], tdf['oxigenio'], 'o', alpha=0.1, color=color)
            plt.plot(tdf['timestamp_site'], tdf['o2_smooth'], '-', color=color, label=f'{tank}')
            plt.plot(future_times, future_o2, '--', color=color, label=f'Proj. {tank}')

        # Chamada ao Agente Especialista com Micro-Contexto
        parecer = analyze_feed_prediction_sync(resumo_agente + " | ".join(tanks_info))
        analysis_text += f"\n💡 *Parecer do Especialista:*\n_{parecer}_"

        plt.axhline(y=LIMITE_TRATO, color='green', linestyle='-', alpha=0.3)
        plt.title('Estimativa de Recuperação de O2')
        plt.legend(loc='lower right')
        plt.tight_layout()

        if not os.path.exists(REPORTS_DIR): os.makedirs(REPORTS_DIR)
        plot_path = os.path.join(REPORTS_DIR, 'trato_hoje.png')
        plt.savefig(plot_path)
        plt.close()
        
        send_telegram_photo(analysis_text, plot_path)

    except Exception as e: print(f"Erro: {e}")

if __name__ == "__main__":
    run_production_logic()
