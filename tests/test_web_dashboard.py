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
    """Verifica se os endpoints de API estão protegidos."""
    response = client.post('/api/scrape')
    assert response.status_code == 302 # Redirect to login
    
    response = client.post('/api/sync')
    assert response.status_code == 302 # Redirect to login
