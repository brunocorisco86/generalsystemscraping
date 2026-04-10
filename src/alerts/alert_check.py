import os
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

# Importar serviços do projeto
from src.services.database import get_sqlite_connection
from src.services.notification import send_telegram_message

# Carregar variáveis de ambiente
load_dotenv()

# Configurações via .env
LIMITE_OXIGENIO_CRITICO = float(os.getenv("LIMITE_OXIGENIO_CRITICO", 1.5))

def check_alerts():
    """Verifica as últimas leituras no banco de dados e dispara alertas se necessário."""
    conn = None
    try:
        conn = get_sqlite_connection()
        if not conn:
            print("❌ Erro: Não foi possível conectar ao banco de dados.")
            return
            
        cursor = conn.cursor()

        # Busca a última leitura de cada tanque usando subquery
        # Nota: Usamos 'data_coleta' ou 'timestamp_site' dependendo da precisão desejada.
        # Aqui usamos data_coleta que é preenchido pelo nosso script de scraping.
        cursor.execute("""
            SELECT t1.tanque, t1.oxigenio, t1.temperatura
            FROM leituras t1
            INNER JOIN (
                SELECT tanque, MAX(data_coleta) as max_data
                FROM leituras
                GROUP BY tanque
            ) t2 ON t1.tanque = t2.tanque AND t1.data_coleta = t2.max_data
        """)

        leituras = cursor.fetchall()

        if not leituras:
            print(f"[{datetime.now()}] Nenhuma leitura encontrada para verificar.")
            return

        for tanque, oxigenio, temperatura in leituras:
            # Log de monitoramento no console
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Verificando {tanque}: {oxigenio} Mg/L")

            # Dispara o alerta se estiver abaixo do limite
            if oxigenio < LIMITE_OXIGENIO_CRITICO:
                mensagem = (
                    f"🚨 *ALERTA CRÍTICO* 🚨\n\n"
                    f"📍 Tanque: *{tanque}*\n"
                    f"🔴 Oxigênio: *{oxigenio} Mg/L* 🔴\n"
                    f"🌡️ Temp: {temperatura}°C\n"
                    f"⏰ Hora: {datetime.now().strftime('%H:%M:%S')}"
                )
                send_telegram_message(mensagem)
                print(f"✅ Alerta enviado para {tanque} (O2: {oxigenio})")

    except Exception as e:
        print(f"❌ Erro ao processar alertas: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Para executar do root: python3 -m src.alerts.alert_check
    check_alerts()
