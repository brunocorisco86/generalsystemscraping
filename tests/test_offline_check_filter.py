import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from src.alerts.offline_check import check_last_reading

def test_offline_check_filters_inactive_batches():
    """Garante que check_last_reading não gera alertas offline para tanques sem lote ativo."""
    
    # 1. Mock do SQLite (retorna leituras antigas - offline - para ambos os tanques)
    # Tanque Ativo: última leitura há 60 minutos (offline)
    # Tanque Inativo: última leitura há 90 minutos (offline)
    mock_sqlite_conn = MagicMock()
    mock_sqlite_cur = MagicMock()
    mock_sqlite_conn.cursor.return_value = mock_sqlite_cur
    
    tempo_ativo = (datetime.now() - timedelta(minutes=60)).strftime('%Y-%m-%d %H:%M:%S')
    tempo_inativo = (datetime.now() - timedelta(minutes=90)).strftime('%Y-%m-%d %H:%M:%S')
    
    mock_sqlite_cur.fetchall.return_value = [
        ("Tanque Ativo", tempo_ativo),
        ("Tanque Inativo", tempo_inativo)
    ]

    # 2. Mock do PostgreSQL (retorna apenas o UID do Tanque Ativo como lote ativo)
    mock_pg_conn = MagicMock()
    mock_pg_cur = MagicMock()
    mock_pg_conn.cursor.return_value = mock_pg_cur
    mock_pg_cur.fetchall.return_value = [("uid-ativo-123",)]

    # 3. Mock do get_all_estruturas_map
    mock_estruturas_map = {
        "Tanque Ativo": "uid-ativo-123",
        "Tanque Inativo": "uid-inativo-456"
    }

    # 4. Mock do envio de mensagem do Telegram
    mock_send_msg = MagicMock()

    # Patches
    with patch("src.alerts.offline_check.get_sqlite_connection", return_value=mock_sqlite_conn), \
         patch("src.alerts.offline_check.get_postgres_connection", return_value=mock_pg_conn), \
         patch("src.alerts.offline_check.get_all_estruturas_map", return_value=mock_estruturas_map), \
         patch("src.alerts.offline_check.send_telegram_message", mock_send_msg):
         
        check_last_reading()

        # 5. Asserts
        # Deve ter enviado mensagem apenas para o Tanque Ativo
        assert mock_send_msg.call_count == 1
        call_args = mock_send_msg.call_args[0][0]
        assert "Tanque Ativo" in call_args
        assert "Tanque Inativo" not in call_args
