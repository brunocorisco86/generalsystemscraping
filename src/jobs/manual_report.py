"""
Relatório manual (disparado pelo botão do painel) com leitura atual, médias 1h/6h
e taxa de variação por hora de O2 e temperatura.

Tudo é calculado sob demanda a partir das leituras já existentes no SQLite,
sem criar tabelas, caches ou dependências novas (apenas `statistics` da stdlib).
"""
import os
import logging
import statistics
from datetime import datetime, timedelta

from src.services.database import (
    get_sqlite_connection,
    get_postgres_connection,
    get_all_estruturas_map,
    get_local_now,
)

logger = logging.getLogger(__name__)

LIMITE_OXIGENIO_CRITICO = float(os.getenv("LIMITE_OXIGENIO_CRITICO", 1.5))
OX_LIMITE_SEGURANCA = float(os.getenv("OX_LIMITE_SEGURANCA", 2.0))
DEADBAND_OX = 0.1    # mg/L por hora
DEADBAND_TEMP = 0.1  # °C por hora
TS_FMT = "%Y-%m-%d %H:%M:%S"


def br(value, casas=1) -> str:
    """Formata número no padrão brasileiro (vírgula decimal)."""
    if value is None:
        return "--"
    return f"{value:.{casas}f}".replace(".", ",")


def taxa_por_hora(pontos):
    """Calcula (último - primeiro) / horas entre eles. pontos = [(datetime, valor)]."""
    if len(pontos) < 2:
        return None
    (t0, v0), (t1, v1) = pontos[0], pontos[-1]
    horas = (t1 - t0).total_seconds() / 3600
    if horas <= 0:
        return None
    return (v1 - v0) / horas


def seta(taxa, deadband) -> str:
    if taxa is None:
        return "→"
    if taxa > deadband:
        return "↗"
    if taxa < -deadband:
        return "↘"
    return "→"


def fmt_taxa(taxa, casas=2) -> str:
    if taxa is None:
        return "s/ tendência"
    sinal = "+" if taxa > 0 else ""
    return f"{sinal}{br(taxa, casas)}/h"


def status_ox(ox) -> str:
    if ox < LIMITE_OXIGENIO_CRITICO:
        return "🔴"
    if ox < OX_LIMITE_SEGURANCA:
        return "🟡"
    return "🟢"


def _estruturas_ativas():
    """Retorna set de UIDs com lote ativo, ou None se o Postgres estiver indisponível."""
    pg = get_postgres_connection()
    if not pg:
        return None
    try:
        cur = pg.cursor()
        cur.execute("SELECT estrutura_uid FROM lotes WHERE data_abate IS NULL")
        return {r[0] for r in cur.fetchall()}
    except Exception as e:
        logger.error("Erro ao buscar estruturas ativas para relatório manual: %s", e)
        return None
    finally:
        pg.close()


def build_manual_report(coleta_ok: bool = True) -> str:
    """Monta o texto do relatório manual para envio no WhatsApp."""
    agora = get_local_now()
    conn = get_sqlite_connection()
    if not conn:
        return "❌ Não foi possível acessar o banco local para gerar o relatório."

    try:
        cur = conn.cursor()
        desde_6h = (agora - timedelta(hours=6)).strftime(TS_FMT)
        cur.execute(
            """
            SELECT nome_estrutura, oxigenio, temperatura, aeradores_ativos, timestamp_site
            FROM leituras
            WHERE timestamp_site >= ? AND nome_estrutura IS NOT NULL AND nome_estrutura != ''
            ORDER BY nome_estrutura, timestamp_site ASC
            """,
            (desde_6h,),
        )
        rows = cur.fetchall()

        clima = None
        try:
            cur.execute(
                "SELECT temperatura, umidade, pressao FROM clima_historico ORDER BY data_coleta DESC LIMIT 1"
            )
            clima = cur.fetchone()
        except Exception:
            clima = None
    finally:
        conn.close()

    linhas = [f"🐟 *Piscicultura Patel — Leitura agora ({agora.strftime('%H:%M')})*"]
    if clima and all(v is not None for v in clima):
        linhas.append(f"🌤️ {br(clima[0])}°C · 💧 {br(clima[1], 0)}% · ⏲️ {br(clima[2], 0)} hPa")
    if not coleta_ok:
        linhas.append("⚠️ Coleta falhou, exibindo última leitura disponível")

    # Agrupa por tanque
    por_tanque = {}
    for nome, ox, temp, aer, ts in rows:
        try:
            dt = datetime.strptime(ts, TS_FMT)
        except Exception:
            continue
        por_tanque.setdefault(nome, []).append((dt, ox, temp, aer))

    ativos = _estruturas_ativas()
    mapa = get_all_estruturas_map()

    exibiu = False
    limite_1h = agora - timedelta(hours=1)
    for nome in sorted(por_tanque):
        uid = mapa.get(nome)
        if ativos is not None and (not uid or uid not in ativos):
            continue
        dados = por_tanque[nome]
        if not dados:
            continue
        exibiu = True

        ult_dt, ox_atual, temp_atual, aer_atual = dados[-1]
        ultima_1h = [d for d in dados if d[0] >= limite_1h]
        base = ultima_1h if len(ultima_1h) >= 2 else dados

        med_ox_1h = statistics.mean(d[1] for d in ultima_1h) if ultima_1h else None
        med_ox_6h = statistics.mean(d[1] for d in dados)
        med_temp_6h = statistics.mean(d[2] for d in dados)

        tx_ox = taxa_por_hora([(d[0], d[1]) for d in base])
        tx_temp = taxa_por_hora([(d[0], d[2]) for d in base])

        linhas.append("")
        linhas.append(f"📍 *{nome}* {status_ox(ox_atual)}")
        linhas.append(f"O₂: *{br(ox_atual, 2)}* mg/L {seta(tx_ox, DEADBAND_OX)} {fmt_taxa(tx_ox)}")
        linhas.append(f"   méd 1h {br(med_ox_1h, 2)} · 6h {br(med_ox_6h, 2)}")
        linhas.append(
            f"Temp: *{br(temp_atual)}*°C {seta(tx_temp, DEADBAND_TEMP)} {fmt_taxa(tx_temp, 1)} (méd 6h {br(med_temp_6h)})"
        )
        linhas.append(f"Aeradores: {aer_atual or 0} 🌀 · leitura {ult_dt.strftime('%H:%M')}")

    if not exibiu:
        linhas.append("")
        linhas.append("⚠️ Nenhuma leitura recente (6h) de tanque com lote ativo.")

    linhas.append("")
    linhas.append("_Enviado manualmente pelo painel_")
    return "\n".join(linhas)
