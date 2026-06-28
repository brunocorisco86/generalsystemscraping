import sys
from unittest.mock import patch, MagicMock, AsyncMock


import pytest
from src.alerts.alert_check import check_alerts

def test_alert_check_filters_inactive_batches():
    """Garante que check_alerts não gera alertas de oxigênio para tanques sem lote ativo."""
    
    # 1. Mock do SQLite (retorna leituras com O2 baixo para ambos os tanques)
    # Tanque Ativo: O2 = 1.0 (crítico)
    # Tanque Inativo: O2 = 0.8 (crítico)
    mock_sqlite_conn = MagicMock()
    mock_sqlite_cur = MagicMock()
    mock_sqlite_conn.cursor.return_value = mock_sqlite_cur
    mock_sqlite_cur.fetchall.return_value = [
        ("Tanque Ativo", 1.0, 24.5),
        ("Tanque Inativo", 0.8, 25.1)
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

    # 4. Mock da chamada da IA (analyze_alert_data)
    mock_analyze = AsyncMock(return_value="🚨 *ALERTA:* O2 Crítico no Tanque Ativo!")

    # 5. Mock do envio de mensagem do Telegram
    mock_send_msg = MagicMock()

    # Patches
    with patch("src.alerts.alert_check.get_sqlite_connection", return_value=mock_sqlite_conn), \
         patch("src.alerts.alert_check.get_postgres_connection", return_value=mock_pg_conn), \
         patch("src.alerts.alert_check.get_all_estruturas_map", return_value=mock_estruturas_map), \
         patch("src.alerts.alert_check.analyze_alert_data", mock_analyze), \
         patch("src.alerts.alert_check.send_telegram_message", mock_send_msg):
         
        check_alerts()

        # 6. Asserts
        # analyze_alert_data só deve ser chamado uma vez (para o Tanque Ativo)
        mock_analyze.assert_called_once_with("Tanque Ativo", 1.0, 24.5)
        # send_telegram_message deve enviar a mensagem gerada pela IA
        mock_send_msg.assert_called_once_with("🚨 *ALERTA:* O2 Crítico no Tanque Ativo!")



