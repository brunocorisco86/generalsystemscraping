import pytest
from src.web.app import app
from src.services.web_auth import init_web_auth_db, validate_user
import os

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

def test_login_page_loads(client):
    """Verifica se a página de login carrega corretamente."""
    response = client.get('/login')
    assert response.status_code == 200
    assert b"Acesso Restrito" in response.data

def test_dashboard_redirect_without_login(client):
    """Verifica se o dashboard redireciona para login se não autenticado."""
    response = client.get('/', follow_redirects=True)
    assert b"Acesso Restrito" in response.data

def test_web_auth_service():
    """Testa o serviço de autenticação web."""
    # Garante que a tabela existe
    init_web_auth_db()
    
    # Testa validação de usuário (usando defaults do .env ou padrão)
    user = os.environ.get("WEB_ADMIN_USER", "admin")
    pw = os.environ.get("WEB_ADMIN_PASS", "admin123")
    
    validated = validate_user(user, pw)
    assert validated is not None
    assert validated['username'] == user

def test_api_endpoints_protected(client):
    """Verifica se os endpoints de API estão protegidos sem autenticação."""
    response = client.post('/api/scrape')
    assert response.status_code == 302 # Redirect to login
    
    response = client.post('/api/sync')
    assert response.status_code == 302 # Redirect to login

    response = client.get('/api/endpoints')
    assert response.status_code == 302

    response = client.get('/api/endpoint/10:20:BA:66:2E:C8')
    assert response.status_code == 302

    response = client.post('/api/endpoint/10:20:BA:66:2E:C8/thresholds')
    assert response.status_code == 302


from unittest.mock import patch

@pytest.fixture
def auth_client(client):
    """Cria um cliente logado para testar rotas protegidas."""
    init_web_auth_db()
    client.post('/login', data={'username': 'test_admin', 'password': 'admin123'})
    return client


def test_api_endpoints_list(auth_client):
    response = auth_client.get('/api/endpoints')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert len(data['endpoints']) >= 2


def test_api_get_endpoint(auth_client):
    mock_ep = {
        "id": "10:20:BA:66:2E:C8",
        "name": "Tanque 1",
        "criticalO2": 2.0,
        "criticalO2Max": 4.5,
        "autoOn": True,
        "timer": '{"enabled": true}'
    }
    with patch("src.web.app.NoctuaClient.get_endpoint_config", return_value=mock_ep):
        response = auth_client.get('/api/endpoint/10:20:BA:66:2E:C8')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['endpoint']['criticalO2'] == 2.0


def test_api_update_thresholds(auth_client):
    mock_ret = {"id": "10:20:BA:66:2E:C8", "criticalO2": 2.5}
    with patch("src.web.app.NoctuaClient.update_endpoint_thresholds", return_value=mock_ret):
        response = auth_client.post(
            '/api/endpoint/10:20:BA:66:2E:C8/thresholds',
            json={"critical_o2": 2.5, "critical_o2_max": 5.0, "auto_on": True}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert "atualizados com sucesso" in data['message']


def test_api_update_timers(auth_client):
    mock_ret = {"id": "10:20:BA:66:2E:C8", "timer": '{"enabled": false}'}
    with patch("src.web.app.NoctuaClient.update_endpoint_timer", return_value=mock_ret):
        response = auth_client.post(
            '/api/endpoint/10:20:BA:66:2E:C8/timers',
            json={"timer": '{"enabled": false}'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'


def test_api_send_motor_command_success(auth_client):
    mock_ret = {"messageId": "msg-123", "status": "SENT"}
    with patch("src.web.app.NoctuaClient.send_motor_command", return_value=mock_ret):
        response = auth_client.post(
            '/api/endpoint/10:20:BA:66:2E:C8/command',
            json={"command": "MOTOR_ALL_ON"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert data['data']['status'] == "SENT"
