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


from unittest.mock import patch, MagicMock
from datetime import date

@pytest.fixture
def auth_client(client):
    """Cria um cliente logado para testar rotas protegidas."""
    init_web_auth_db()
    # Efetuar login com as credenciais do .env.test
    user = os.environ.get("WEB_ADMIN_USER", "test_admin")
    pw = os.environ.get("WEB_ADMIN_PASS", "admin123")
    client.post('/login', data={'username': user, 'password': pw})
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


def test_lotes_page_loads(auth_client):
    """Garante que a página de lotes carrega para usuário autenticado."""
    response = auth_client.get('/lotes')
    assert response.status_code == 200
    assert b"Gest\xc3\xa3o de Lotes" in response.data or b"Lotes" in response.data


def test_settings_page_loads(auth_client):
    """Garante que a página de configurações carrega para usuário autenticado."""
    response = auth_client.get('/settings')
    assert response.status_code == 200
    assert b"Configura\xc3\xa7\xc3\xb5es" in response.data or b"Settings" in response.data


def test_api_get_lotes_route(auth_client):
    """Testa endpoint GET /api/lotes com mock do postgres."""
    with patch("src.web.app.get_postgres_connection") as mock_conn:
        mock_pg = MagicMock()
        mock_cur = MagicMock()
        mock_pg.cursor.return_value = mock_cur
        mock_conn.return_value = mock_pg

        # 1. lotes ativos, 2. biometria totais, 3. ultimo peso, 4. historico
        mock_cur.fetchall.side_effect = [
            [(1, "uid1", "Tanque 1", "LOTE-01", date(2026, 9, 20), 10000, 35.0, 1000.0, 10.0, "Desc")],
            []
        ]
        mock_cur.fetchone.side_effect = [
            (5, 50.0), # mort_tot, racao_tot
            (42.5,)    # last_peso
        ]

        response = auth_client.get('/api/lotes')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'ok'
        assert len(data['ativos']) == 1
        assert data['ativos'][0]['lote'] == 'LOTE-01'


def test_api_settings_db_status_route(auth_client):
    """Testa endpoint GET /api/settings/db/status com mock do postgres."""
    with patch("src.web.app.get_postgres_connection") as mock_conn:
        mock_pg = MagicMock()
        mock_cur = MagicMock()
        mock_pg.cursor.return_value = mock_cur
        mock_conn.return_value = mock_pg
        mock_cur.fetchone.return_value = (10,)

        response = auth_client.get('/api/settings/db/status')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'ok'
        assert 'counts' in data
        assert data['counts']['lotes'] == 10


def test_subpath_reverse_proxy_support(client):
    """Valida se o ProxyFix respeita o header X-Forwarded-Prefix: /psicultura do Caddy."""
    resp = client.get('/', headers={'X-Forwarded-Prefix': '/psicultura'})
    assert resp.status_code == 302
    assert '/psicultura/login' in resp.headers['Location']

    login_resp = client.get('/login', headers={'X-Forwarded-Prefix': '/psicultura'})
    assert login_resp.status_code == 200
    assert b'const APP_BASE_URL = "/psicultura";' in login_resp.data


def test_crud_contatos_whatsapp_dynamic(auth_client):
    """Testa listagem do seed (Dirceu/Joceli), adição, edição, teste WhatsApp e remoção de contatos."""
    with patch("src.services.database.get_postgres_connection", return_value=None):
        # 1. Listar contatos (deve conter o seed inicial no SQLite fallback)
        r_list = auth_client.get('/api/contatos')
        assert r_list.status_code == 200
        contatos = r_list.get_json()['contatos']
        nomes = [c['nome'] for c in contatos]
        assert "Dirceu Patel" in nomes
        assert "Joceli Patel" in nomes

        # 2. Adicionar novo contato dinâmico
        r_add = auth_client.post('/api/contatos', json={
            "nome": "Bruno Conter",
            "papel": "Genro / Admin",
            "telefone": "44997604925",
            "ativo": True,
            "receber_alertas": True,
            "receber_relatorios": True
        })
        assert r_add.status_code == 200
        novo = r_add.get_json()['contato']
        novo_id = novo['id']
        assert novo['nome'] == "Bruno Conter"
        assert novo['telefone'] == "44997604925"

        # 3. Testar disparo via Evolution API para esse contato
        with patch("src.web.app.send_whatsapp_message", return_value=True) as mock_wpp:
            r_test = auth_client.post(f'/api/contatos/{novo_id}/test')
            assert r_test.status_code == 200
            assert r_test.get_json()['status'] == 'ok'
            mock_wpp.assert_called_once()

        # 4. Excluir contato dinâmico
        r_del = auth_client.delete(f'/api/contatos/{novo_id}')
        assert r_del.status_code == 200
        assert r_del.get_json()['status'] == 'ok'


def test_mdm_uid_cascade_proprietario_and_propriedade(auth_client):
    """Valida que alterar CPF ou CADPRO migra o UID nas tabelas filhas e remove duplicatas antigas."""
    with patch("src.web.app.get_postgres_connection") as mock_conn:
        mock_pg = MagicMock()
        mock_cur = MagicMock()
        mock_pg.cursor.return_value = mock_cur
        mock_conn.return_value = mock_pg

        # 1. Salvar proprietário com novo CPF
        r_prop = auth_client.post('/api/mdm/proprietario', json={
            "nome": "Dirceu Patel",
            "cpf": "499.041.839-53"
        })
        assert r_prop.status_code == 200
        new_prop_uid = r_prop.get_json()['uid']

        executed_sqls = [call[0][0] for call in mock_cur.execute.call_args_list]
        assert any("INSERT INTO proprietarios" in s for s in executed_sqls)
        assert any("UPDATE propriedades SET proprietario_uid" in s for s in executed_sqls)
        assert any("DELETE FROM proprietarios WHERE uid <>" in s for s in executed_sqls)

        # 2. Salvar propriedade com novo CADPRO
        mock_cur.reset_mock()
        mock_cur.fetchone.return_value = (new_prop_uid,)
        r_rural = auth_client.post('/api/mdm/propriedade', json={
            "nome": "Sítio Patel",
            "endereco": "Linha São Carlos, Palotina-PR",
            "cadpro": "95105108-09"
        })
        assert r_rural.status_code == 200
        executed_rural_sqls = [call[0][0] for call in mock_cur.execute.call_args_list]
        assert any("INSERT INTO propriedades" in s for s in executed_rural_sqls)
        assert any("UPDATE estruturas SET propriedade_uid" in s for s in executed_rural_sqls)
        assert any("DELETE FROM propriedades WHERE uid <>" in s for s in executed_rural_sqls)



