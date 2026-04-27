import os
import logging
import sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from dotenv import load_dotenv

# Adicionar o caminho do projeto ao sys.path para permitir importações do src
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

from src.services.database import get_postgres_connection
from src.services.notification import send_telegram_photo, send_telegram_message

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

os.makedirs('logs', exist_ok=True)
os.makedirs('reports', exist_ok=True)

# --- CONFIGURAÇÕES DE LOGGING ---
LOG_FILE = os.path.join(os.environ.get("LOGS_DIR", "logs"), "plot_curva.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler() # Para também mostrar no console/stdout
    ]
)
logger = logging.getLogger(__name__)

# --- CONFIGURAÇÕES GERAIS ---
REPORT_DIR = os.environ.get("REPORTS_DIR", "reports")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID") # Para mensagens de erro
PESO_ALVO = 950  # g
DIAS_PROJECAO_MAX = 350  # limite de projeção (dias)

if not os.path.exists(REPORT_DIR):
    os.makedirs(REPORT_DIR)


# --- MODELO GOMPERTZ (OPCIONAL, NÃO USADO NA PROJEÇÃO) ---
def modelo_gompertz(t, Winf, k, ti):
    return Winf * np.exp(-np.exp(-k * (t - ti)))


def ajustar_gompertz(x, y):
    Winf0 = max(y) * 1.5
    k0 = 0.01
    ti0 = np.median(x)
    p0 = [Winf0, k0, ti0]

    bounds = (
        [max(y), 0.0001, 0],
        [3000, 0.1, DIAS_PROJECAO_MAX],
    )

    popt, pcov = curve_fit(
        modelo_gompertz,
        x,
        y,
        p0=p0,
        bounds=bounds,
        maxfev=20000,
    )
    return popt, pcov


# --- AJUSTE LINEAR (PRINCIPAL) ---
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


# --- SCRIPT PRINCIPAL ---
def gerar_curva():
    logger.info("Iniciando geração da curva de crescimento e projeção.")
    conn = None
    try:
        conn = get_postgres_connection()
        if conn is None:
            logger.error("Erro: Não foi possível conectar ao banco de dados PostgreSQL.")
            send_telegram_message(f"❌ Erro ao gerar curva de crescimento: falha na conexão com o BD.")
            return

        query = """
            SELECT tanque, lote, data_biometria, peso_medio_g 
            FROM biometria 
            WHERE lote::text IN (
                SELECT lote::text 
                FROM lotes 
                WHERE data_abate IS NULL
            )
            ORDER BY tanque, data_biometria ASC;
        """

        df = pd.read_sql(query, conn)

        if df.empty:
            logger.info("Nenhum dado de biometria encontrado para lotes ativos.")
            send_telegram_message("ℹ️ Nenhum dado de biometria encontrado para gerar a curva de crescimento.")
            return

        tanques = df["tanque"].unique()
        plt.style.use('seaborn-v0_8-darkgrid')
        plt.figure(figsize=(12, 7))

        relatorio_texto = (
            "📊 *Relatório de Projeção de Crescimento*\n\n"
            f"🎯 Peso-alvo: *{PESO_ALVO} g*\n"
            "📐 Modelo principal: *Linear (y = a·dias + b)*\n\n"
        )

        resultados_parametros = []
        cores = plt.cm.tab10.colors

        for i, tanque in enumerate(tanques):
            cor = cores[i % len(cores)]
            df_t = df[df["tanque"] == tanque].copy()
            df_t["data_biometria"] = pd.to_datetime(df_t["data_biometria"])

            data_inicial = df_t["data_biometria"].min()
            df_t["dias"] = (df_t["data_biometria"] - data_inicial).dt.days

            x_data = df_t["dias"].values.astype(float)
            y_data = df_t["peso_medio_g"].values.astype(float)

            try:
                if len(x_data) >= 2:
                    # --- AJUSTE LINEAR ---
                    a, b = ajustar_reta(x_data, y_data)
                    r2, rmse = metricas_reta(x_data, y_data, a, b)

                    # projeção linear
                    x_proj = np.arange(0, DIAS_PROJECAO_MAX + 1)
                    y_proj = a * x_proj + b

                    datas_proj = [
                        data_inicial + timedelta(days=int(d)) for d in x_proj
                    ]

                    # scatter pontos reais
                    plt.scatter(
                        df_t["data_biometria"],
                        y_data,
                        label=f"Real: {tanque}",
                        s=60,
                        color=cor,
                    )
                    # linha da reta
                    plt.plot(
                        datas_proj,
                        y_proj,
                        "--",
                        alpha=0.9,
                        label=f"Proj (linear): {tanque}",
                        color=cor,
                    )

                    # dia em que atinge PESO_ALVO: PESO_ALVO = a*d + b  => d = (PESO_ALVO - b)/a
                    if a > 0:
                        dia_alvo = (PESO_ALVO - b) / a
                        if 0 <= dia_alvo <= DIAS_PROJECAO_MAX:
                            dia_alvo_int = int(round(dia_alvo))
                            data_alvo = data_inicial + timedelta(days=dia_alvo_int)
                            data_str = data_alvo.strftime("%d/%m/%Y")
                        else:
                            data_str = "Não atinge alvo ≤350 dias"
                    else:
                        dia_alvo = np.nan
                        data_str = "Tendência sem ganho de peso"

                    data_ult = df_t["data_biometria"].max()

                    relatorio_texto += (
                        f"🐟 *{tanque}* (Lote {df_t['lote'].iloc[0]})\n"
                        f"├ Peso atual: {y_data[-1]:.0f} g em {data_ult:%d/%m/%Y}\n"
                        f"├ Previsão {PESO_ALVO} g (reta): *{data_str}*\n"
                        f"└ a: {a:.3f} g/dia | R²: {r2:.3f} | RMSE: {rmse:.1f} g\n\n"
                    )

                    resultados_parametros.append(
                        {
                            "tanque": tanque,
                            "lote": df_t["lote"].iloc[0],
                            "modelo": "linear",
                            "a_g_dia": a,
                            "b_intercepto": b,
                            "r2": r2,
                            "rmse": rmse,
                            "dias_para_alvo": (PESO_ALVO - b) / a if a > 0 else np.nan,
                            "data_inicial": data_inicial,
                        }
                    )

                else:
                    plt.scatter(
                        df_t["data_biometria"],
                        y_data,
                        label=f"{tanque} (Poucos pontos)",
                        s=60,
                        color=cor,
                    )
                    relatorio_texto += (
                        f"🐟 *{tanque}*: Dados insuficientes para projetar curva.\n\n"
                    )

            except Exception as e:
                logger.error(f"[ERRO] Tanque {tanque}: {e}", exc_info=True)
                plt.scatter(
                    df_t["data_biometria"],
                    y_data,
                    label=f"{tanque} (Erro no ajuste)",
                    s=60,
                    color=cor,
                )
                relatorio_texto += (
                    f"🐟 *{tanque}*: Erro no ajuste da curva.\n\n"
                )
                continue

        # linha de alvo
        plt.axhline(
            y=PESO_ALVO,
            color="red",
            linestyle=":",
            label=f"Alvo: {PESO_ALVO} g",
        )

        # --- ajuste do xlim: até 30 dias após o último cruzamento do alvo ---
        datas_alvo = []
        for r in resultados_parametros:
            dias_para_alvo = r["dias_para_alvo"]
            if not np.isnan(dias_para_alvo) and dias_para_alvo > 0:
                data_inicial_tanque = r["data_inicial"]
                data_alvo_tanque = data_inicial_tanque + timedelta(
                    days=int(round(dias_para_alvo))
                )
                datas_alvo.append(data_alvo_tanque)

        x_min = df["data_biometria"].min()
        if datas_alvo:
            data_alvo_max = max(datas_alvo)
            x_max = data_alvo_max + timedelta(days=30)
        else:
            # se nenhum tanque atinge o alvo, usa 30 dias após última biometria
            x_max = df["data_biometria"].max() + timedelta(days=30)

        plt.xlim(x_min, x_max)

        plt.title("Crescimento de Tilápia - Projeção Linear", fontsize=14)
        plt.xlabel("Data")
        plt.ylabel("Peso Médio (g)")
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left') # Mover legenda para fora
        plt.grid(True, which="both", linestyle="--", alpha=0.5)
        plt.xticks(rotation=45)
        plt.tight_layout(rect=[0, 0, 0.85, 1]) # Ajustar layout para caber a legenda

        nome_arquivo = (
            f"crescimento_linear_{datetime.now().strftime('%Y%m%d_%H%M')}.png"
        )
        caminho_completo = os.path.join(REPORT_DIR, nome_arquivo)
        if not os.path.exists(REPORT_DIR):
            os.makedirs(REPORT_DIR)
        plt.savefig(caminho_completo, dpi=100)
        plt.close()
        logger.info(f"Gráfico de curva de crescimento salvo em {caminho_completo}")

        # salva parâmetros da reta
        if resultados_parametros:
            df_param = pd.DataFrame(resultados_parametros)
            csv_name = f"parametros_lineares_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            csv_path = os.path.join(REPORT_DIR, csv_name)
            df_param.to_csv(csv_path, index=False)
            logger.info(f"Parâmetros da reta salvos em {csv_path}")

        send_telegram_photo(relatorio_texto, caminho_completo, chat_id=TELEGRAM_CHAT_ID)
        logger.info("Relatório de curva de crescimento enviado para o Telegram.")

    except Exception as e:
        logger.error(f"Erro geral ao gerar curva de crescimento: {e}", exc_info=True)
        send_telegram_message(f"❌ Erro crítico ao gerar curva de crescimento: {e}", chat_id=TELEGRAM_CHAT_ID)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    gerar_curva()
