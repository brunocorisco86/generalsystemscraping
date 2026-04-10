import os
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Importar serviços do projeto
from src.services.database import get_sqlite_connection
from src.services.notification import send_telegram_message

# Carregar variáveis de ambiente
load_dotenv()

# Configurações via .env
MINUTOS_OFFLINE_ALERTA = int(os.getenv("MINUTOS_OFFLINE_ALERTA", 30))

def check_last_reading():
    """
    Verifica o tempo da última leitura dos tanques. 
    Envia alerta se o atraso for maior que o configurado.
    """
    conn = None
    try:
        conn = get_sqlite_connection()
        if not conn:
            print("❌ Erro: Não foi possível conectar ao banco de dados.")
            return

        cursor = conn.cursor()

        # Busca tanques distintos
        cursor.execute("SELECT DISTINCT tanque FROM leituras")
        tanks = [row[0] for row in cursor.fetchall()]

        if not tanks:
            send_telegram_message("🚫 *Atenção:* Nenhum dado de tanque encontrado para monitoramento offline.")
            return

        for tank in tanks:
            # Busca a última leitura baseada no timestamp_site (que reflete o sensor)
            cursor.execute("""
                SELECT timestamp_site FROM leituras
                WHERE tanque = ? ORDER BY timestamp_site DESC LIMIT 1
            """, (tank,))
            result = cursor.fetchone()

            if result and result[0]:
                last_reading_str = result[0]
                try:
                    last_reading_time = datetime.strptime(last_reading_str, '%Y-%m-%d %H:%M:%S')
                    time_difference = datetime.now() - last_reading_time

                    if time_difference > timedelta(minutes=MINUTOS_OFFLINE_ALERTA):
                        message = (
                            f"⚠️ *Alerta: Sistema OFFLINE!* ⚠️\n\n"
                            f"*Tanque:* {tank}\n"
                            f"*Última leitura:* `{last_reading_str}`\n"
                            f"O sistema não registra dados há mais de {MINUTOS_OFFLINE_ALERTA} minutos."
                        )
                        send_telegram_message(message)
                        print(f"✅ Alerta offline enviado para {tank}")
                except ValueError:
                    print(f"⚠️ Erro ao converter timestamp: {last_reading_str} para o tanque {tank}")
            else:
                send_telegram_message(f"❓ *Aviso:* Tanque {tank} cadastrado, mas sem leituras recentes.")

    except Exception as e:
        print(f"❌ Erro no monitoramento offline: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Para executar do root: python3 -m src.alerts.offline_check
    check_last_reading()
