import os
import sys
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Adicionar o caminho do projeto ao sys.path para permitir importações do src
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

from src.services.database import get_postgres_connection  # noqa: E402
from src.services.notification import send_telegram_photo, send_telegram_message  # noqa: E402

from dotenv import load_dotenv
load_dotenv()

os.makedirs('logs', exist_ok=True)
os.makedirs('reports', exist_ok=True)

# --- CONFIGURAÇÕES DE LOGGING ---
LOG_FILE = os.path.join(os.environ.get("LOGS_DIR", "logs"), "bot_query_curva_peso.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- CONFIGURAÇÕES DO SCRIPT ---
REPORT_DIR = os.environ.get("REPORTS_DIR", "reports")
CHAT_ID_FROM_ARGS = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("TELEGRAM_CHAT_ID")

# Parâmetros de projeção
PESO_ALVO = 950  # Peso-alvo em gramas
DIAS_PROJECAO_MAX = 350  # Limite máximo de projeção (dias)

def ajustar_reta(x, y):
    """
    Ajuste linear simples: y = a*x + b
    Retorna coeficientes a, b.
    """
    a, b = np.polyfit(x, y, 1)
    return a, b

def metricas_reta(x, y, a, b):
    y_hat = a * x + b
    resid = y - y_hat
    ss_res = np.sum(resid ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
    rmse = np.sqrt(ss_res / len(y))
    return r2, rmse

def gerar_curva_peso():
    logger.info("Iniciando geração de relatório de projeção de curva de peso.")
    
    conn = None
    try:
        conn = get_postgres_connection()
        if conn is None:
            logger.error("Erro: Não foi possível conectar ao banco de dados PostgreSQL.")
            send_telegram_message("❌ Erro ao gerar curva de peso: falha na conexão com o BD.", chat_id=CHAT_ID_FROM_ARGS)
            return

        # Query buscando dados de biometria de lotes ativos (data_abate IS NULL)
        query = """
            SELECT 
                e.nome AS estrutura, 
                b.lote, 
                b.data_biometria, 
                b.peso_medio 
            FROM biometria b
            JOIN estruturas e ON b.estrutura_uid = e.uid
            WHERE b.lote::text IN (
                SELECT lote::text 
                FROM lotes 
                WHERE data_abate IS NULL
            )
            AND b.peso_medio IS NOT NULL
            ORDER BY e.nome, b.data_biometria ASC;
        """

        df = pd.read_sql_query(query, conn)

        if df.empty:
            logger.info("Nenhum dado de biometria encontrado para lotes ativos.")
            send_telegram_message("ℹ️ Nenhum dado de biometria encontrado para lotes ativos.", chat_id=CHAT_ID_FROM_ARGS)
            return

        # Garante o tipo datetime para cálculos
        df["data_biometria"] = pd.to_datetime(df["data_biometria"])
        
        estruturas = df["estrutura"].unique()
        plt.style.use('seaborn-v0_8-darkgrid')
        plt.figure(figsize=(12, 7))

        relatorio_texto = (
            "📊 *Relatório de Projeção de Crescimento*\n\n"
            f"🎯 Peso-alvo: *{PESO_ALVO} g*\n"
            "📐 Modelo principal: *Linear (y = a·dias + b)*\n\n"
        )

        resultados_parametros = []
        cores = plt.cm.tab10.colors

        for i, estrutura in enumerate(estruturas):
            cor = cores[i % len(cores)]
            df_e = df[df["estrutura"] == estrutura].copy()

            data_inicial = df_e["data_biometria"].min()
            df_e["dias"] = (df_e["data_biometria"] - data_inicial).dt.days

            x_data = df_e["dias"].values.astype(float)
            y_data = df_e["peso_medio"].values.astype(float)

            try:
                if len(x_data) >= 2:
                    # Ajuste Linear
                    a, b = ajustar_reta(x_data, y_data)
                    r2, rmse = metricas_reta(x_data, y_data, a, b)

                    # Projeção linear para plotagem
                    x_proj = np.arange(0, DIAS_PROJECAO_MAX + 1)
                    y_proj = a * x_proj + b
                    datas_proj = [data_inicial + timedelta(days=int(d)) for d in x_proj]

                    # Plot dos pontos reais
                    plt.scatter(
                        df_e["data_biometria"],
                        y_data,
                        label=f"Real: {estrutura}",
                        s=60,
                        color=cor,
                    )
                    # Plot da linha de projeção
                    plt.plot(
                        datas_proj,
                        y_proj,
                        "--",
                        alpha=0.7,
                        label=f"Proj (linear): {estrutura}",
                        color=cor,
                    )

                    # Estimativa de data para atingir o peso-alvo
                    if a > 0:
                        dia_alvo = (PESO_ALVO - b) / a
                        if 0 <= dia_alvo <= DIAS_PROJECAO_MAX:
                            dia_alvo_int = int(round(dia_alvo))
                            data_alvo = data_inicial + timedelta(days=dia_alvo_int)
                            data_str = data_alvo.strftime("%d/%m/%Y")
                        else:
                            data_str = f"Acima de {DIAS_PROJECAO_MAX} dias"
                    else:
                        dia_alvo = np.nan
                        data_str = "Tendência estável/negativa"

                    data_ult = df_e["data_biometria"].max()

                    relatorio_texto += (
                        f"🔹 *{estrutura}* (Lote {df_e['lote'].iloc[0]})\n"
                        f"├ Peso atual: {y_data[-1]:.0f} g ({data_ult:%d/%m/%Y})\n"
                        f"├ Previsão {PESO_ALVO}g: *{data_str}*\n"
                        f"└ Ganho: {a:.2f} g/dia | $R^2$: {r2:.3f}\n\n"
                    )

                    resultados_parametros.append({
                        "estrutura": estrutura,
                        "dias_para_alvo": dia_alvo if a > 0 else np.nan,
                        "data_inicial": data_inicial
                    })

                else:
                    plt.scatter(df_e["data_biometria"], y_data, label=f"{estrutura} (Insuficiente)", s=40, color=cor)
                    relatorio_texto += f"🔹 *{estrutura}*: Dados insuficientes para projetar.\n\n"

            except Exception as e:
                logger.error(f"Erro ao processar estrutura {estrutura}: {e}")
                continue

        # Linha horizontal do alvo
        plt.axhline(y=PESO_ALVO, color="red", linestyle=":", label=f"Alvo: {PESO_ALVO}g", alpha=0.6)

        # Configuração dos limites do eixo X (Zoom no período relevante)
        datas_alvo = []
        for r in resultados_parametros:
            if not np.isnan(r["dias_para_alvo"]) and r["dias_para_alvo"] > 0:
                data_alvo_est = r["data_inicial"] + timedelta(days=int(round(r["dias_para_alvo"])))
                datas_alvo.append(data_alvo_est)
        
        x_min = df["data_biometria"].min()
        if datas_alvo:
            x_max = max(datas_alvo) + timedelta(days=20)
        else:
            x_max = df["data_biometria"].max() + timedelta(days=45)
        
        plt.xlim(x_min, x_max)
        plt.title("Projeção de Crescimento (Peso Médio)", fontsize=14)
        plt.xlabel("Data")
        plt.ylabel("Peso Médio (g)")
        plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Salva o arquivo de imagem
        plot_path = os.path.join(REPORT_DIR, f"curva_peso_{datetime.now().strftime('%Y%m%d_%H%M')}.png")
        plt.savefig(plot_path, dpi=120)
        plt.close()
        
        logger.info(f"Gráfico de curva de peso salvo em {plot_path}")

        # Envia para o Telegram
        send_telegram_photo(relatorio_texto, plot_path, chat_id=CHAT_ID_FROM_ARGS)
        logger.info("Relatório enviado para o Telegram com sucesso.")

    except Exception as e:
        logger.error(f"ERRO CRÍTICO no script de curva de peso: {e}", exc_info=True)
        send_telegram_message(f"❌ Erro crítico ao gerar curva de peso: {e}", chat_id=CHAT_ID_FROM_ARGS)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    gerar_curva_peso()