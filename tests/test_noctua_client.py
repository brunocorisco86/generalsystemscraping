"""
Testes unitários para o cliente Noctua IoT GraphQL (AWS AppSync).
Valida queries, mutations, tratamento de erros e travas de segurança de leitura/escrita.
"""
import pytest
from unittest.mock import MagicMock, patch
import requests

from src.services.noctua_client import (
    NoctuaClient,
    NoctuaClientException,
    NoctuaReadOnlyException,
    DEFAULT_GATEWAY_ID,
    KNOWN_ENDPOINTS
)


@pytest.fixture
def client_readonly():
    return NoctuaClient(
        api_url="https://mock-appsync.example.com/graphql",
        api_key="da2-mock-key",
        gateway_id=DEFAULT_GATEWAY_ID,
        read_only=True
    )


@pytest.fixture
def client_writable():
    return NoctuaClient(
        api_url="https://mock-appsync.example.com/graphql",
        api_key="da2-mock-key",
        gateway_id=DEFAULT_GATEWAY_ID,
        read_only=False
    )


def test_test_connection_success(client_readonly):
    mock_payload = {
        "data": {
            "listSensorDataByGatewayIdAndUpdatedAt": {
                "items": [{"id": "item1", "o2": 5.2, "temperature": 26.0}]
            }
        }
    }
    with patch.object(client_readonly.session, "post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_payload
        mock_post.return_value = mock_resp

        res = client_readonly.test_connection()
        assert res["status"] == "success"
        assert res["items_count"] == 1


def test_test_connection_failure(client_readonly):
    with patch.object(client_readonly.session, "post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"
        mock_post.return_value = mock_resp

        res = client_readonly.test_connection()
        assert res["status"] == "error"
        assert "401" in res["message"]


def test_get_latest_readings_by_tanque(client_readonly):
    mock_payload = {
        "data": {
            "listSensorDataByGatewayIdAndUpdatedAt": {
                "items": [
                    {
                        "id": "1",
                        "endpointId": "10:20:BA:66:2E:C8",
                        "gatewayId": DEFAULT_GATEWAY_ID,
                        "o2": 4.8,
                        "temperature": 25.5,
                        "sat": 92.1,
                        "engines": "01000",
                        "ts": "2026-09-20T18:00:00Z"
                    },
                    {
                        "id": "2",
                        "endpointId": "10:20:BA:6A:90:00",
                        "gatewayId": DEFAULT_GATEWAY_ID,
                        "o2": 3.2,
                        "temperature": 25.0,
                        "sat": 78.5,
                        "engines": "00000",
                        "ts": "2026-09-20T18:00:00Z"
                    }
                ]
            }
        }
    }
    with patch.object(client_readonly.session, "post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_payload
        mock_post.return_value = mock_resp

        readings = client_readonly.get_latest_readings_by_tanque()
        assert "Tanque 1" in readings
        assert "Tanque 2" in readings
        assert readings["Tanque 1"]["oxigenio"] == 4.8
        assert readings["Tanque 1"]["temperatura"] == 25.5
        assert readings["Tanque 1"]["aeradores_ativos"] == 1
        assert readings["Tanque 2"]["oxigenio"] == 3.2
        assert readings["Tanque 2"]["aeradores_ativos"] == 0


def test_get_endpoint_config(client_readonly):
    mock_payload = {
        "data": {
            "getEndpoint": {
                "id": "10:20:BA:66:2E:C8",
                "name": "Tanque 1",
                "autoOn": True,
                "criticalO2": 2.0,
                "criticalO2Max": 4.0,
                "timer": '{"enabled": true}'
            }
        }
    }
    with patch.object(client_readonly.session, "post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_payload
        mock_post.return_value = mock_resp

        cfg = client_readonly.get_endpoint_config("10:20:BA:66:2E:C8")
        assert cfg["name"] == "Tanque 1"
        assert cfg["criticalO2"] == 2.0
        assert cfg["autoOn"] is True


def test_update_thresholds_readonly_blocked(client_readonly):
    with pytest.raises(NoctuaReadOnlyException):
        client_readonly.update_endpoint_thresholds(
            endpoint_id="10:20:BA:66:2E:C8",
            critical_o2=2.5
        )


def test_update_thresholds_invalid_values(client_writable):
    with pytest.raises(ValueError, match="fora da faixa de segurança"):
        client_writable.update_endpoint_thresholds(
            endpoint_id="10:20:BA:66:2E:C8",
            critical_o2=0.5  # abaixo de 1.0
        )

    with pytest.raises(ValueError, match="fora da faixa de segurança"):
        client_writable.update_endpoint_thresholds(
            endpoint_id="10:20:BA:66:2E:C8",
            critical_o2=15.0  # acima de 10.0
        )


def test_update_thresholds_success(client_writable):
    mock_payload = {
        "data": {
            "updateEndpoint": {
                "id": "10:20:BA:66:2E:C8",
                "criticalO2": 3.0,
                "criticalO2Max": 5.0,
                "autoOn": True
            }
        }
    }
    with patch.object(client_writable.session, "post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_payload
        mock_post.return_value = mock_resp

        updated = client_writable.update_endpoint_thresholds(
            endpoint_id="10:20:BA:66:2E:C8",
            critical_o2=3.0,
            critical_o2_max=5.0,
            auto_on=True
        )
        assert updated["criticalO2"] == 3.0
        assert updated["autoOn"] is True


def test_update_timer_readonly_blocked(client_readonly):
    with pytest.raises(NoctuaReadOnlyException):
        client_readonly.update_endpoint_timer(
            endpoint_id="10:20:BA:66:2E:C8",
            timer_data={"enabled": False}
        )


def test_update_timer_success(client_writable):
    mock_payload = {
        "data": {
            "updateEndpoint": {
                "id": "10:20:BA:66:2E:C8",
                "timer": '{"enabled": false}'
            }
        }
    }
    with patch.object(client_writable.session, "post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_payload
        mock_post.return_value = mock_resp

        updated = client_writable.update_endpoint_timer(
            endpoint_id="10:20:BA:66:2E:C8",
            timer_data={"enabled": False}
        )
        assert "timer" in updated


def test_send_motor_command_readonly_blocked(client_readonly):
    with pytest.raises(NoctuaReadOnlyException):
        client_readonly.send_motor_command(
            endpoint_id="10:20:BA:66:2E:C8",
            command="MOTOR_1_ON"
        )


def test_send_motor_command_unknown_endpoint(client_writable):
    with pytest.raises(NoctuaClientException, match="não autorizado na allowlist"):
        client_writable.send_motor_command(
            endpoint_id="99:99:99:99:99:99",
            command="MOTOR_1_ON"
        )


def test_send_motor_command_success(client_writable):
    mock_payload = {
        "data": {
            "createCommandMessages": {
                "messageId": "dummy-uuid",
                "endpointId": "10:20:BA:66:2E:C8",
                "status": "SENT"
            }
        }
    }
    with patch.object(client_writable.session, "post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_payload
        mock_post.return_value = mock_resp

        result = client_writable.send_motor_command(
            endpoint_id="10:20:BA:66:2E:C8",
            command="MOTOR_1_ON"
        )
        assert result["status"] == "SENT"
        assert result["endpointId"] == "10:20:BA:66:2E:C8"
