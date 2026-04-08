import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import requests
import os
import glob
from datetime import datetime, timedelta

# --- CONFIGURAÇÕES ---
DB_PATH = '/home/dietpi/piscicultura_monitor/piscicultura_dados.db'
REPORT_DIR = '/home/dietpi/piscicultura_monitor/reports'
TELEGRAM_TOKEN = "8355153356:AAG55aFGL153Uzwo4w48uj1_vDV8BC2sim4"
TELEGRAM_CHAT_ID = "-1003744398479"
LIMITE_CRITICO = 2.0  # mg/L

def generate_report():
    # 0 - Limpeza da pasta de relatórios
    if not os.path.exists(REPORT_DIR):
        os.makedirs(REPORT_DIR)
    
    files = glob.glob(f'{REPORT_DIR}/*')
    for f in files:
        try:
            os.remove(f)
        except:
            pass

    # Definição do intervalo: Ontem 18:00 até Hoje 08:00
    now = datetime.now()
    end_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
    start_time = (end_time - timedelta(days=1)).replace(hour=18, minute=0)

    try:
        # Conexão e Leitura dos Dados
        conn = sqlite3.connect(DB_PATH)
        query = f"""
            SELECT tanque, oxigenio, temperatura, timestamp_site 
            FROM leituras 
            WHERE timestamp_site BETWEEN '{start_time.strftime('%Y-%m-%d %H:%M:%S')}' 
            AND '{end_time.strftime('%Y-%m-%d %H:%M:%S')}'
            ORDER BY timestamp_site ASC
        """
        
        # Correção do erro anterior: pd.read_sql_query
        df = pd.read_sql_query(query, conn)
        conn.close()

        if df.empty:
            print(f"Sem dados encontrados entre {start_time} e {end_time}")
            return

        # Converter para datetime e garantir ordenação
        df['timestamp_site'] = pd.to_datetime(df['timestamp_site'])

        # 1 & 2 - Geração do Plot (Gráfico)
        plt.figure(figsize=(12, 6))
        
        # Linha Crítica de 2.0 mg/L
        plt.axhline(y=LIMITE_CRITICO, color='red', linestyle='--', linewidth=2, label=f'Limite Crítico ({LIMITE_CRITICO} mg/L)')
        
        analysis_text = f"📊 *Relatório Noturno: {start_time.strftime('%d/%m')} ➔ {end_time.strftime('%d/%m')}*\n\n"
        
        # Plotar uma curva para cada tanque
        for tank in df['tanque'].unique():
            tank_data = df[df['tanque'] == tank]
            plt.plot(tank_data['timestamp_site'], tank_data['oxigenio'], label=f'{tank} - O2', marker='.', markersize=4)
            
            # Análise breve por tanque
            o2_min = tank_data['oxigenio'].min()
            temp_avg = tank_data['temperatura'].mean()
            
            # Alerta visual se atingiu o limite crítico
            status = "🚨 *PERIGO*" if o2_min <= LIMITE_CRITICO else "✅ *OK*"
            analysis_text += f"{status} - {tank}:\n   • O2 Mínimo: `{o2_min:.2f} mg/L`\n   • Temp Média: `{temp_avg:.1f}°C`\n\n"

        plt.title(f'Curva de Oxigênio - Período Noturno ({start_time.strftime("%H:%M")} às {end_time.strftime("%H:%M")})')
        plt.xlabel('Horário da Leitura')
        plt.ylabel('Oxigênio Dissolvido (mg/L)')
        plt.legend(loc='upper right')
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        
        # Salvar imagem
        plot_path = os.path.join(REPORT_DIR, 'nightly_plot.png')
        plt.savefig(plot_path)
        plt.close()

        # 3 - Envio para o Telegram
        send_to_telegram(analysis_text, plot_path)
        print("Relatório enviado com sucesso!")

    except Exception as e:
        print(f"Ocorreu um erro no processamento: {e}")

def send_to_telegram(text, photo_path):
    url_photo = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    
    try:
        with open(photo_path, 'rb') as photo:
            payload = {
                'chat_id': TELEGRAM_CHAT_ID,
                'caption': text,
                'parse_mode': 'Markdown'
            }
            files = {'photo': photo}
            response = requests.post(url_photo, data=payload, files=files, timeout=20)
            response.raise_for_status()
    except Exception as e:
        print(f"Falha ao enviar Telegram: {e}")

if __name__ == "__main__":
    generate_report()
