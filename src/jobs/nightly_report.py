import os
import glob
import logging
from datetime import datetime, timedelta
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from dotenv import load_dotenv

# Importar serviços centralizados do projeto
from src.services.database import get_sqlite_connection
from src.services.notification import send_telegram_photo

# Configuração do logger
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# --- CONFIGURAÇÕES VIA .ENV ---
REPORT_DIR = os.environ.get("REPORTS_DIR", "reports")
LIMITE_CRITICO = float(os.environ.get("LIMITE_OXIGENIO_CRITICO", 2.0))

def generate_nightly_report():
    """
    Gera um relatório do período noturno (18h às 08h) com um gráfico 
    do nível de oxigênio e envia para o Telegram.
    """
    # Garante a existência da pasta de relatórios
    if not os.path.exists(REPORT_DIR):
        os.makedirs(REPORT_DIR, exist_ok=True)
    
    # Limpa relatórios noturnos antigos
    for f in glob.glob(os.path.join(REPORT_DIR, 'nightly_*')):
        try:
            os.remove(f)
        except OSError as e:
            logger.error("Erro ao remover arquivo antigo %s: %s", f, e)

    # Definição do intervalo: Ontem 18:00 até Hoje 08:00
    now = datetime.now()
    end_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
    start_time = (end_time - timedelta(days=1)).replace(hour=18, minute=0, second=0, microsecond=0)

    conn = None
    try:
        # Conexão via serviço centralizado
        conn = get_sqlite_connection()
        if conn is None:
            logger.error("Erro: Não foi possível conectar ao banco de dados SQLite.")
            return

        query = f"""
            SELECT tanque, oxigenio, temperatura, timestamp_site 
            FROM leituras 
            WHERE timestamp_site BETWEEN '{start_time.strftime('%Y-%m-%d %H:%M:%S')}' 
            AND '{end_time.strftime('%Y-%m-%d %H:%M:%S')}'
            ORDER BY timestamp_site ASC
        """
        
        df = pd.read_sql_query(query, conn)

        if df.empty:
            logger.warning("Sem dados encontrados entre %s e %s", start_time, end_time)
            return

        # Converter para datetime e garantir ordenação
        df['timestamp_site'] = pd.to_datetime(df['timestamp_site'])

        # --- GERAÇÃO DO GRÁFICO ---
        plt.style.use('seaborn-v0_8-darkgrid')
        plt.figure(figsize=(12, 6))
        
        # Linha de Limite Crítico
        plt.axhline(y=LIMITE_CRITICO, color='red', linestyle='--', linewidth=2, label=f'Limite Crítico ({LIMITE_CRITICO} mg/L)')
        
        analysis_text = f"📊 *Relatório Noturno: {start_time.strftime('%d/%m')} ➔ {end_time.strftime('%d/%m')}*\n\n"
        
        # Plotar uma curva para cada tanque
        for tank in sorted(df['tanque'].unique()):
            tank_data = df[df['tanque'] == tank]
            plt.plot(tank_data['timestamp_site'], tank_data['oxigenio'], label=f'{tank}', marker='.', markersize=4)
            
            # Análise estatística por tanque
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
        plt.savefig(plot_path, dpi=100)
        plt.close()

        # Enviar para o Telegram via serviço centralizado
        send_telegram_photo(analysis_text, plot_path)
        logger.info("Relatório noturno gerado e enviado com sucesso para %s.", plot_path)

    except Exception as e:
        logger.error("Ocorreu um erro no processamento do relatório noturno: %s", e)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # Configuração básica de logging para execução direta
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    # Para executar do root: python3 -m src.jobs.nightly_report
    generate_nightly_report()
