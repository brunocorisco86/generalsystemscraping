import pytest
from unittest.mock import patch, MagicMock
from src.services.notification import send_ntfy_message, send_telegram_message

def test_send_ntfy_message_success():
    """Valida se o payload e headers do ntfy.sh são montados e enviados corretamente."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch("requests.post", return_value=mock_response) as mock_post:
        success = send_ntfy_message(
            message="Oxigênio Crítico em Tanque 1!",
            title="Alerta Urgente",
            priority="urgent",
            tags=["warning", "fish"]
        )
        assert success is True
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://ntfy.sh/piscicultura-patel-palotina"
        assert kwargs["headers"]["Priority"] == "urgent"
        assert kwargs["headers"]["Tags"] == "warning,fish"
        assert kwargs["data"] == "Oxigênio Crítico em Tanque 1!".encode("utf-8")

def test_send_telegram_mirrors_to_ntfy():
    """Valida se alertas do Telegram disparam automaticamente push para o ntfy.sh."""
    with patch("src.services.notification.send_ntfy_message") as mock_ntfy, \
         patch("requests.post") as mock_tg_post:
        
        mock_tg_resp = MagicMock()
        mock_tg_resp.raise_for_status.return_value = None
        mock_tg_post.return_value = mock_tg_resp

        send_telegram_message("🚨 *ALERTA:* Oxigênio baixo no Tanque 2 (0.9 mg/L)", chat_id="123")
        
        mock_ntfy.assert_called_once()
        args, kwargs = mock_ntfy.call_args
        assert "🚨" in args[0]
        assert kwargs["priority"] == "urgent"
        assert "rotating_light" in kwargs["tags"]


def test_send_whatsapp_message_evolution_api():
    """Valida se o envio via Evolution API formata o número (DDI 55) e chama o endpoint correto."""
    from src.services.notification import send_whatsapp_message, normalize_whatsapp_number

    assert normalize_whatsapp_number("(44) 99760-4925") == "5544997604925"
    assert normalize_whatsapp_number("5544997604925") == "5544997604925"

    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None

    with patch("requests.post", return_value=mock_resp) as mock_post:
        ok = send_whatsapp_message("Teste Piscicultura", phone="44997604925")
        assert ok is True
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert "/message/sendText/" in args[0]
        assert kwargs["json"]["number"] == "5544997604925"
        assert kwargs["json"]["text"] == "Teste Piscicultura"


def test_send_whatsapp_message_brazilian_ninth_digit_fallback_and_error():
    """Valida fallback de 9º dígito (13 -> 12 dígitos) e mensagem clara quando exists=false."""
    from src.services.notification import send_whatsapp_message, get_brazilian_phone_variants

    assert get_brazilian_phone_variants("44999440454") == ["5544999440454", "554499440454"]
    assert get_brazilian_phone_variants("554499440454") == ["554499440454", "5544999440454"]

    resp_400 = MagicMock()
    resp_400.status_code = 400
    resp_400.json.return_value = {
        "status": 400,
        "error": "Bad Request",
        "response": {"message": [{"jid": "554499047476@s.whatsapp.net", "exists": False, "number": "554499047476"}]}
    }

    with patch("requests.post", return_value=resp_400) as mock_post:
        ok, err = send_whatsapp_message("Teste", phone="554499047476", return_error=True)
        assert ok is False
        assert "exists: false" in err
        assert mock_post.call_count == 2


