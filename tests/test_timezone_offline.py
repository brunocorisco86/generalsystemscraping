import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from src.services.database import get_local_now

def test_get_local_now_returns_datetime():
    """Valida se get_local_now retorna datetime ingênuo e coerente."""
    now_local = get_local_now()
    assert isinstance(now_local, datetime)
    assert now_local.tzinfo is None

def test_dashboard_offline_calculation():
    """Simula o cálculo do dashboard para leituras recentes vs antigas."""
    now_local = get_local_now()
    
    # 1. Leitura recente (2 minutos atrás)
    recent_ts = (now_local - timedelta(minutes=2)).strftime('%Y-%m-%d %H:%M:%S')
    dt_ts = datetime.strptime(recent_ts, '%Y-%m-%d %H:%M:%S')
    diff_min = int((now_local - dt_ts).total_seconds() / 60)
    is_offline = diff_min > 30
    
    assert diff_min == 2
    assert is_offline is False

    # 2. Leitura antiga (45 minutos atrás)
    old_ts = (now_local - timedelta(minutes=45)).strftime('%Y-%m-%d %H:%M:%S')
    dt_ts_old = datetime.strptime(old_ts, '%Y-%m-%d %H:%M:%S')
    diff_min_old = int((now_local - dt_ts_old).total_seconds() / 60)
    is_offline_old = diff_min_old > 30

    assert diff_min_old == 45
    assert is_offline_old is True

def test_offline_check_timezone_resilience():
    """Valida se offline_check usa get_local_now sem gerar falsos positivos para leituras recentes."""
    from src.alerts.offline_check import check_last_reading
    
    now_local = get_local_now()
    recent_reading = (now_local - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
    
    mock_sqlite = MagicMock()
    mock_cursor = MagicMock()
    # Retorna uma leitura recente para Tanque 1
    mock_cursor.fetchall.return_value = [("Tanque 1", recent_reading)]
    mock_sqlite.cursor.return_value = mock_cursor

    with patch("src.alerts.offline_check.get_sqlite_connection", return_value=mock_sqlite), \
         patch("src.alerts.offline_check.get_postgres_connection", return_value=None), \
         patch("src.services.database.is_system_suspended", return_value=False), \
         patch("src.alerts.offline_check.send_telegram_message") as mock_telegram:
        
        check_last_reading()
        
        # Como o atraso foi de apenas 5 minutos, NÃO deve enviar mensagem de offline
        for call_arg in mock_telegram.call_args_list:
            msg = call_arg[0][0]
            assert "⚠️ *Alerta: Sistema OFFLINE!*" not in msg
