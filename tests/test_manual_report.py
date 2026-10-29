import sqlite3
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from src.jobs import manual_report
from src.jobs.manual_report import build_manual_report, taxa_por_hora, seta

NOW = datetime(2026, 10, 28, 21, 0, 0)


def _make_conn():
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    cur.execute("""CREATE TABLE leituras (id INTEGER PRIMARY KEY, estrutura_uid TEXT, nome_estrutura TEXT,
                   oxigenio REAL, temperatura REAL, timestamp_site TEXT, data_coleta TEXT, aeradores_ativos INTEGER)""")
    cur.execute("CREATE TABLE clima_historico (data_coleta TEXT, temperatura REAL, umidade REAL, pressao REAL)")
    cur.execute("INSERT INTO clima_historico VALUES ('x', 19.3, 85, 977.6)")
    # Tanque 1: O2 caindo 1 mg/L por hora na última hora (9 -> 8)
    for i, ox in enumerate([9.0, 8.5, 8.0]):
        ts = (NOW - timedelta(minutes=60 - i * 30)).strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("INSERT INTO leituras (nome_estrutura, oxigenio, temperatura, timestamp_site, aeradores_ativos) VALUES (?,?,?,?,?)",
                    ("Tanque 1", ox, 25.0, ts, 0))
    # Tanque 2: inativo
    cur.execute("INSERT INTO leituras (nome_estrutura, oxigenio, temperatura, timestamp_site, aeradores_ativos) VALUES (?,?,?,?,?)",
                ("Tanque 2", 7.0, 25.0, NOW.strftime("%Y-%m-%d %H:%M:%S"), 0))
    conn.commit()
    return conn


class _NoCloseConn:
    def __init__(self, conn):
        self._c = conn
    def cursor(self):
        return self._c.cursor()
    def close(self):
        pass


def _pg_with(uids):
    pg = MagicMock()
    cur = MagicMock()
    cur.fetchall.return_value = [(u,) for u in uids]
    pg.cursor.return_value = cur
    return pg


def test_taxa_e_seta():
    t0 = NOW - timedelta(hours=1)
    assert taxa_por_hora([(t0, 9.0), (NOW, 8.0)]) == -1.0
    assert taxa_por_hora([(NOW, 8.0)]) is None
    assert seta(-1.0, 0.1) == "↘"
    assert seta(0.05, 0.1) == "→"
    assert seta(0.5, 0.1) == "↗"


def test_build_manual_report_filtra_lote_inativo_e_calcula_tendencia():
    conn = _NoCloseConn(_make_conn())
    with patch.object(manual_report, "get_local_now", return_value=NOW), \
         patch.object(manual_report, "get_sqlite_connection", return_value=conn), \
         patch.object(manual_report, "get_postgres_connection", return_value=_pg_with(["uid1"])), \
         patch.object(manual_report, "get_all_estruturas_map", return_value={"Tanque 1": "uid1", "Tanque 2": "uid2"}):
        txt = build_manual_report()

    assert "Tanque 1" in txt
    assert "Tanque 2" not in txt
    assert "*8,00* mg/L ↘ -1,00/h" in txt
    assert "méd 1h 8,50" in txt
    assert "19,3°C" in txt


def test_build_manual_report_postgres_fora_nao_filtra():
    conn = _NoCloseConn(_make_conn())
    with patch.object(manual_report, "get_local_now", return_value=NOW), \
         patch.object(manual_report, "get_sqlite_connection", return_value=conn), \
         patch.object(manual_report, "get_postgres_connection", return_value=None), \
         patch.object(manual_report, "get_all_estruturas_map", return_value={}):
        txt = build_manual_report(coleta_ok=False)

    assert "Tanque 1" in txt and "Tanque 2" in txt
    assert "Coleta falhou" in txt
