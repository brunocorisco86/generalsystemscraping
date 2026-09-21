"""
Testes unitários e de integração para o módulo monitor_data refatorado para API GraphQL.
"""
import pytest
from unittest.mock import patch, MagicMock
from src.services.database import get_sqlite_connection
from src.scrape.monitor_data import collect_via_api, scrape_and_save


@pytest.fixture
def clean_db():
    conn = get_sqlite_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM leituras")
        conn.commit()
        conn.close()
    yield
    conn = get_sqlite_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM leituras")
        conn.commit()
        conn.close()


def test_collect_via_api_success(clean_db):
    mock_readings = {
        "Tanque 1": {
            "oxigenio": 5.4,
            "temperatura": 26.2,
            "aeradores_ativos": 2,
            "timestamp": "2026-09-20T19:30:00Z"
        },
        "Tanque 2": {
            "oxigenio": 4.1,
            "temperatura": 25.8,
            "aeradores_ativos": 0,
            "timestamp": "2026-09-20T19:30:00Z"
        }
    }

    with patch("src.scrape.monitor_data.NoctuaClient") as MockClient:
        instance = MockClient.return_value
        instance.get_latest_readings_by_tanque.return_value = mock_readings

        sucesso = collect_via_api()
        assert sucesso is True

    # Valida no SQLite
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nome_estrutura, oxigenio, temperatura, aeradores_ativos FROM leituras ORDER BY nome_estrutura")
    rows = cursor.fetchall()
    conn.close()

    assert len(rows) == 2
    assert rows[0][0] == "Tanque 1"
    assert rows[0][1] == 5.4
    assert rows[0][2] == 26.2
    assert rows[0][3] == 2

    assert rows[1][0] == "Tanque 2"
    assert rows[1][1] == 4.1
    assert rows[1][3] == 0


def test_collect_via_api_ignores_zeroed_and_invalid(clean_db):
    mock_readings = {
        "Tanque Invalido N/A": {
            "oxigenio": 5.0,
            "temperatura": 25.0,
            "aeradores_ativos": 0,
            "timestamp": None
        },
        "Tanque 1": {
            "oxigenio": 0.0,
            "temperatura": 0.0,
            "aeradores_ativos": 0,
            "timestamp": None
        }
    }

    with patch("src.scrape.monitor_data.NoctuaClient") as MockClient:
        instance = MockClient.return_value
        instance.get_latest_readings_by_tanque.return_value = mock_readings

        sucesso = collect_via_api()
        assert sucesso is False

    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM leituras")
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 0


def test_scrape_and_save_suspended():
    with patch("src.scrape.monitor_data.is_system_suspended", return_value=True), \
         patch("src.scrape.monitor_data.collect_via_api") as mock_collect:
        scrape_and_save()
        mock_collect.assert_not_called()
