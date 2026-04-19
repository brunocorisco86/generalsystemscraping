import os
import statistics
from datetime import datetime
from dotenv import load_dotenv

# Importar serviços centralizados do projeto
from src.services.database import get_sqlite_connection
from src.services.notification import send_telegram_message

# Carregar variáveis de ambiente
load_dotenv()

# Configurações via .env com fallbacks
LIMITE_OXIGENIO_CRITICO = float(os.getenv("LIMITE_OXIGENIO_CRITICO", 2.0))

def get_hourly_report():
    """Gera o relatório estatístico das últimas leituras para cada tanque."""
    conn = None
    try:
        conn = get_sqlite_connection()
        if not conn:
            return "❌ Erro: Não foi possível conectar ao banco de dados SQLite."
            
        cursor = conn.cursor()
        
        # Consulta otimizada: busca as últimas 4 leituras de todos os tanques em uma única query
        # utilizando Window Functions (ROW_NUMBER) para evitar o padrão N+1.
        cursor.execute("""
            WITH ranked_leituras AS (
                SELECT
                    nome_estrutura,
                    oxigenio,
                    temperatura,
                    timestamp_site,
                    aeradores_ativos,
                    ROW_NUMBER() OVER (PARTITION BY nome_estrutura ORDER BY data_coleta DESC) as rn
                FROM leituras
                WHERE nome_estrutura IS NOT NULL AND nome_estrutura != ''
            )
            SELECT
                nome_estrutura,
                oxigenio,
                temperatura,
                timestamp_site,
                aeradores_ativos
            FROM ranked_leituras
            WHERE rn <= 4
            ORDER BY nome_estrutura, rn ASC
        """)

        all_rows = cursor.fetchall()

        if not all_rows:
            return "📊 *Relatório Horário*\nSem dados recentes para reportar."

        # Agrupa os dados por tanque em Python
        grouped_data = {}
        for row in all_rows:
            tanque = row[0]
            if tanque not in grouped_data:
                grouped_data[tanque] = []
            grouped_data[tanque].append(row[1:])

        relatorio = f"📊 *Relatório das {datetime.now().strftime('%H')} horas*\n"

        for tanque, leituras in grouped_data.items():
            # Extração de listas para cálculos estatísticos
            lista_ox = [r[0] for r in leituras]
            lista_temp = [r[1] for r in leituras]

            # Atribuição da leitura mais recente (rn=1 foi o primeiro de cada grupo devido ao ORDER BY rn ASC)
            ox_atual, temp_atual, ts_site, aeradores_atuais = leituras[0]
            
            avg_ox = statistics.mean(lista_ox)
            avg_temp = statistics.mean(lista_temp)

            # --- CÁLCULO DE CONFIANÇA ---
            # Coeficiente de Variação (CV) para medir estabilidade dos dados
            if len(lista_ox) > 1:
                stdev_ox = statistics.stdev(lista_ox)
                cv = (stdev_ox / avg_ox) if avg_ox > 0 else 0
                confianca_emoji = "🛡️" if cv < 0.15 else "⚠️"
            else:
                confianca_emoji = "❓"

            # Determinação de Tendências e Status
            trend_ox = "📈" if ox_atual >= avg_ox else "📉"
            trend_temp = "📈" if temp_atual >= avg_temp else "📉"
            status_ox = "🟢" if ox_atual >= LIMITE_OXIGENIO_CRITICO else "🔴"

            # Formata hora do timestamp (ex: 14:30)
            hora_ts = ts_site.split()[-1][:5] if ts_site else "--:--"

            # Montagem do bloco de texto do tanque
            relatorio += f"\n📍 *{tanque}*\n"
            relatorio += f"Oxigênio: `{ox_atual:.2f}` {trend_ox} {status_ox}\n"
            relatorio += f"Temperatura: `{temp_atual:.1f}ºC` {trend_temp}\n"
            relatorio += f"Aeradores: `{aeradores_atuais}` 🌀\n"
            relatorio += f"⌚ {hora_ts} {confianca_emoji}\n"

        return relatorio

    except Exception as e:
        return f"❌ Erro ao gerar relatório: {e}"
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Para executar do root: python3 -m src.jobs.hourly_report
    mensagem_final = get_hourly_report()
    send_telegram_message(mensagem_final)
