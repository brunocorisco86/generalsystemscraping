import os
from datetime import datetime
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
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] --- Iniciando Verificação de Status Offline ---")
    print(f"Configuração: Alerta após {MINUTOS_OFFLINE_ALERTA} minutos de inatividade.")
    
    conn = None
    try:
        conn = get_sqlite_connection()
        if not conn:
            print("❌ Erro Crítico: Não foi possível conectar ao banco de dados SQLite.")
            return

        cursor = conn.cursor()

        # Busca a última leitura de cada tanque em uma única consulta
        cursor.execute("""
            SELECT tanque, MAX(timestamp_site) as last_reading
            FROM leituras
            GROUP BY tanque
        """)
        results = cursor.fetchall()

        if not results:
            print("⚠️ Aviso: Nenhum dado de tanque encontrado na tabela 'leituras'.")
            send_telegram_message("🚫 *Atenção:* Nenhum dado de tanque encontrado para monitoramento offline.")
            return

        print(f"Encontrados {len(results)} tanques para verificar.")

        for tank, last_reading_str in sorted(results):
            if last_reading_str:
                try:
                    last_reading_time = datetime.strptime(last_reading_str, '%Y-%m-%d %H:%M:%S')
                    time_difference = datetime.now() - last_reading_time
                    diff_minutos = int(time_difference.total_seconds() / 60)

                    print(f"🔍 Verificando {tank}:")
                    print(f"   • Última leitura: {last_reading_str}")
                    print(f"   • Atraso atual: {diff_minutos} minutos")

                    if diff_minutos > MINUTOS_OFFLINE_ALERTA:
                        print(f"   🚨 STATUS: OFFLINE (Limite de {MINUTOS_OFFLINE_ALERTA} min excedido!)")
                        message = (
                            f"⚠️ *Alerta: Sistema OFFLINE!* ⚠️\n\n"
                            f"*Tanque:* {tank}\n"
                            f"*Última leitura:* `{last_reading_str}`\n"
                            f"O sistema não registra dados há mais de {MINUTOS_OFFLINE_ALERTA} minutos."
                        )
                        send_telegram_message(message)
                        print("   ✅ Notificação enviada para o Telegram.")
                    else:
                        print("   🟢 STATUS: ONLINE (Dentro do limite)")
                
                except ValueError:
                    print(f"   ❌ Erro: Formato de timestamp inválido para o tanque {tank}: {last_reading_str}")
            else:
                print(f"🔍 Verificando {tank}: ❓ Sem leituras recentes encontradas.")
                send_telegram_message(f"❓ *Aviso:* Tanque {tank} cadastrado, mas sem leituras recentes.")

    except Exception as e:
        print(f"❌ Erro Inesperado no monitoramento offline: {e}")
    finally:
        if conn:
            conn.close()
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] --- Verificação Finalizada ---")

if __name__ == "__main__":
    # Para executar do root: python3 -m src.alerts.offline_check
    check_last_reading()
