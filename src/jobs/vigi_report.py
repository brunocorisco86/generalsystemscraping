import os
import statistics
from datetime import datetime
from dotenv import load_dotenv

# Importar serviços centralizados do projeto
from src.services.database import get_sqlite_connection
from src.services.notification import send_telegram_message

# Carregar variáveis de ambiente
load_dotenv()

# Configurações via .env
LIMITE_OXIGENIO_CRITICO = float(os.getenv("LIMITE_OXIGENIO_CRITICO", 2.0))

def get_emoji_number(text):
    """Converte números em um texto para seus correspondentes em emoji."""
    mapping = {
        "0": "0️⃣", "1": "1️⃣", "2": "2️⃣", "3": "3️⃣", "4": "4️⃣",
        "5": "5️⃣", "6": "6️⃣", "7": "7️⃣", "8": "8️⃣", "9": "9️⃣"
    }
    for digit, emoji in mapping.items():
        text = text.replace(digit, emoji)
    return text

def get_vigi_report():
    """Gera um relatório ultra-sucinto para monitoramento noturno."""
    conn = None
    try:
        conn = get_sqlite_connection()
        if not conn:
            return "❌ Erro: DB indisponível"
            
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT tanque FROM leituras")
        tanques = [row[0] for row in cursor.fetchall()]
        
        relatorio_lista = []
        for tanque in sorted(tanques):
            # Busca as últimas 4 leituras para calcular média e tendência
            cursor.execute("""
                SELECT oxigenio FROM leituras 
                WHERE tanque = ? 
                ORDER BY data_coleta DESC LIMIT 4
            """, (tanque,))
            leituras = [r[0] for r in cursor.fetchall()]
            
            if not leituras: continue
            
            ox_atual = leituras[0]
            avg_ox = statistics.mean(leituras)
            
            # Emojis de Estado
            status = "🟢" if ox_atual >= LIMITE_OXIGENIO_CRITICO else "🔴"
            trend = "↑" if ox_atual >= avg_ox else "↓"
            
            # Cálculo de Confiança (CV < 15% é estável)
            confianca = "✅"
            if len(leituras) > 1:
                stdev = statistics.stdev(leituras)
                cv = (stdev / avg_ox) if avg_ox > 0 else 0
                if cv > 0.15: confianca = "⚠️"
            
            # Formatação UX: 🐟0️⃣1️⃣: 2.8↑🟢✅
            t_id = tanque.replace("Tanque ", "").strip()
            t_visual = f"🐟{get_emoji_number(t_id)}"

            relatorio_lista.append(f"{t_visual}:{ox_atual:.1f}{trend}{status}{confianca}")

        if not relatorio_lista:
            return "🌙 *Vigília:* Sem dados recentes."

        # Retorna os tanques separados por um pipe visual
        return " | ".join(relatorio_lista)

    except Exception as e:
        return f"❌ Erro Vigília: {e}"
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Para executar do root: python3 -m src.jobs.vigi_report
    msg = get_vigi_report()
    send_telegram_message(msg)
