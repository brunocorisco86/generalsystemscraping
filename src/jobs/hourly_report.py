import sqlite3
import requests
import statistics # Biblioteca nativa para o desvio padrão
from datetime import datetime

# CONFIGURAÇÕES
TELEGRAM_TOKEN = "8355153356:AAG55aFGL153Uzwo4w48uj1_vDV8BC2sim4"
TELEGRAM_CHAT_ID = "-1003744398479"
LIMITE_OXIGENIO_CRITICO = 2.0
DB_PATH = "/home/dietpi/piscicultura_monitor/piscicultura_dados.db"

def send_telegram_report(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Erro: {e}")

def get_hourly_report():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Busca a lista de tanques únicos
        cursor.execute("SELECT DISTINCT tanque FROM leituras")
        tanques = [row[0] for row in cursor.fetchall()]

        if not tanques: return "Sem dados."

        relatorio = f"📊 *Relatório das {datetime.now().strftime('%H')} horas*\n"

        for tanque in tanques:
            # Consulta atualizada incluindo 'aeradores_ativos'
            cursor.execute("""
                SELECT oxigenio, temperatura, timestamp_site, aeradores_ativos
                FROM leituras WHERE tanque = ?
                ORDER BY data_coleta DESC LIMIT 4
            """, (tanque,))
            leituras = cursor.fetchall()

            if not leituras: continue

            # Extração de listas para cálculos estatísticos
            lista_ox = [r[0] for r in leituras]
            lista_temp = [r[1] for r in leituras]

            # Atribuição da leitura mais recente (índice 0)
            ox_atual, temp_atual, ts_site, aeradores_atuais = leituras[0]
            
            avg_ox = statistics.mean(lista_ox)
            avg_temp = statistics.mean(lista_temp)

            # --- CÁLCULO DE CONFIANÇA ---
            if len(lista_ox) > 1:
                stdev_ox = statistics.stdev(lista_ox)
                cv = (stdev_ox / avg_ox) if avg_ox > 0 else 0
                confianca_emoji = "🛡️" if cv < 0.15 else "⚠️"
            else:
                confianca_emoji = "❓"

            trend_ox = "📈" if ox_atual >= avg_ox else "📉"
            trend_temp = "📈" if temp_atual >= avg_temp else "📉"
            status_ox = "🟢" if ox_atual >= LIMITE_OXIGENIO_CRITICO else "🔴"

            hora_ts = ts_site.split()[-1][:5] if ts_site else "--:--"

            # Layout com a adição dos aeradores e emoji de ventilador
            relatorio += f"\n📍 *{tanque}*\n"
            relatorio += f"Oxigênio: `{ox_atual:.2f}` {trend_ox} {status_ox}\n"
            relatorio += f"Temperatura: `{temp_atual:.1f}ºC` {trend_temp}\n"
            relatorio += f"Aeradores: `{aeradores_atuais}` 🌀\n" # Nova linha solicitada
            relatorio += f"⌚ {hora_ts} {confianca_emoji}\n"

        conn.close()
        return relatorio

    except Exception as e:
        return f"❌ Erro: {e}"

if __name__ == "__main__":
    mensagem_final = get_hourly_report()
    send_telegram_report(mensagem_final)
