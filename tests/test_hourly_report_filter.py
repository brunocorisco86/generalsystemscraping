import pytest
from unittest.mock import patch, MagicMock
from src.jobs.hourly_report import get_hourly_report

def test_hourly_report_filters_inactive_batches():
    """Garante que get_hourly_report exclui dados de tanques sem lote ativo no Postgres."""
    
    # 1. Mock do SQLite (retorna leituras para Tanque Ativo e Tanque Inativo)
    mock_sqlite_conn = MagicMock()
    mock_sqlite_cur = MagicMock()
    mock_sqlite_conn.cursor.return_value = mock_sqlite_cur
    
    # Simula retorno das leituras (nome_estrutura, oxigenio, temperatura, timestamp_site, aeradores_ativos)
    mock_sqlite_cur.fetchall.return_value = [
        # Primeiro fetchall: RankedLeituras (4 leituras para cada tanque)
        ("Tanque Ativo", 5.5, 24.5, "2026-06-11 20:00:00", 1),
        ("Tanque Ativo", 5.4, 24.6, "2026-06-11 19:00:00", 1),
        ("Tanque Inativo", 4.2, 25.1, "2026-06-11 20:00:00", 0),
        ("Tanque Inativo", 4.1, 25.2, "2026-06-11 19:00:00", 0),
    ]
    # Segundo fetchall: clima_historico (temperatura, umidade, pressao)
    mock_sqlite_cur.fetchone.return_value = (25.0, 60.0, 1012.0)
    
    # 2. Mock do PostgreSQL (retorna apenas o UID do Tanque Ativo como lote ativo)
    mock_pg_conn = MagicMock()
    mock_pg_cur = MagicMock()
    mock_pg_conn.cursor.return_value = mock_pg_cur
    
    # SELECT estrutura_uid FROM lotes WHERE data_abate IS NULL
    mock_pg_cur.fetchall.return_value = [("uid-ativo-123",)]
    
    # 3. Mock do get_all_estruturas_map
    mock_estruturas_map = {
        "Tanque Ativo": "uid-ativo-123",
        "Tanque Inativo": "uid-inativo-456"
    }

    # Aplicando os patches
    with patch("src.jobs.hourly_report.get_sqlite_connection", return_value=mock_sqlite_conn), \
         patch("src.jobs.hourly_report.get_postgres_connection", return_value=mock_pg_conn), \
         patch("src.jobs.hourly_report.get_all_estruturas_map", return_value=mock_estruturas_map):
         
        report = get_hourly_report()
        
        # 4. Asserts
        assert "Tanque Ativo" in report
        assert "Tanque Inativo" not in report
        assert "Oxigênio: `5.50`" in report
        assert "Temperatura: `24.5ºC`" in report
        assert "Aeradores: `1` 🌀" in report
        assert "Nenhuma estrutura com lote ativo" not in report
