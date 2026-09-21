import os
import sys
import logging
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
import pandas as pd

# Adicionar o caminho do projeto ao sys.path para permitir importações do src
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.services.web_auth import init_web_auth_db, validate_user, get_user_by_id
from src.services.database import get_sqlite_connection, get_postgres_connection
from src.services.weather import get_weather_forecast
from src.services.noctua_client import (
    NoctuaClient,
    KNOWN_ENDPOINTS,
    NoctuaClientException,
    NoctuaReadOnlyException
)
# Importar funções adaptadas para modo silencioso
from src.scrape.monitor_data import scrape_and_save
from src.database.postgres.migrate_data import migrate_data
from src.bots.agent import analyze_custom_report_sync

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-piscicultura")

# Configuração do Logging
LOG_FILE = os.path.join(os.environ.get("LOGS_DIR", "logs"), "web_dashboard.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuração do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Garantir tabela e usuário admin criados (tanto em standalone quanto sob Gunicorn)
init_web_auth_db()


class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.username = user_data['username']

@login_manager.user_loader
def load_user(user_id):
    user_data = get_user_by_id(int(user_id))
    if user_data:
        return User(user_data)
    return None

# --- ROTAS DE AUTENTICAÇÃO ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user_data = validate_user(username, password)
        if user_data:
            user = User(user_data)
            login_user(user)
            logger.info(f"Usuário {username} logado com sucesso.")
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha inválidos.', 'error')
            logger.warning(f"Tentativa de login falha para usuário: {username}")
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- ROTA PRINCIPAL (DASHBOARD) ---

@app.route('/')
@login_required
def dashboard():
    # 1. Obter últimas leituras (SQLite como fonte primária)
    conn = get_sqlite_connection()
    leituras = []
    
    # Estruturas separadas para os dois gráficos
    chart_data_ox = {"labels": [], "datasets": []}
    chart_data_temp = {"labels": [], "datasets": []}
    
    if conn:
        try:
            cursor = conn.cursor()
            # Pega a última leitura de cada estrutura (garante exatamente 1 card por estrutura)
            cursor.execute('''
                SELECT nome_estrutura, oxigenio, temperatura, timestamp_site, aeradores_ativos
                FROM leituras
                WHERE id IN (
                    SELECT MAX(id)
                    FROM leituras
                    GROUP BY nome_estrutura
                )
                ORDER BY nome_estrutura ASC
            ''')
            leituras_raw = cursor.fetchall()
            leituras = []
            for row in leituras_raw:
                nome, ox, temp, ts_str, aer = row
                is_offline = False
                minutos_atraso = 0
                if ts_str:
                    try:
                        dt_ts = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
                        diff_min = int((datetime.now() - dt_ts).total_seconds() / 60)
                        minutos_atraso = max(0, diff_min)
                        if diff_min > 30:
                            is_offline = True
                    except Exception:
                        pass
                leituras.append((nome, ox, temp, ts_str, aer, is_offline, minutos_atraso))

            # 2. Obter Histórico de 24h para os Gráficos
            yesterday = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
                SELECT nome_estrutura, oxigenio, temperatura, timestamp_site
                FROM leituras
                WHERE timestamp_site >= ?
                ORDER BY timestamp_site ASC
            ''', (yesterday,))
            history = cursor.fetchall()
            
            # Formatar dados para os dois gráficos
            data_ox = {}
            data_temp = {}
            labels_dict = {} # ts -> label
            for row in history:
                struct, ox, temp, ts = row
                time_label = ts[11:16] # HH:MM
                if ts not in labels_dict:
                    labels_dict[ts] = time_label
                
                if struct not in data_ox:
                    data_ox[struct] = {}
                    data_temp[struct] = {}
                
                data_ox[struct][ts] = ox
                data_temp[struct][ts] = temp
            
            # Montar chart_data_ox e chart_data_temp preservando ordem cronológica (YYYY-MM-DD HH:MM:SS)
            sorted_ts = sorted(labels_dict.keys())
            chart_data_ox["labels"] = [labels_dict[ts] for ts in sorted_ts]
            chart_data_temp["labels"] = [labels_dict[ts] for ts in sorted_ts]
            
            colors_ox = ['#3b82f6', '#10b981'] # Azul e Verde para Oxigênio
            colors_temp = ['#f59e0b', '#ef4444'] # Laranja e Vermelho para Temp
            
            for i, struct in enumerate(data_ox.keys()):
                chart_data_ox["datasets"].append({
                    "label": struct,
                    "data": [data_ox[struct].get(ts) for ts in sorted_ts], 
                    "borderColor": colors_ox[i % len(colors_ox)],
                    "tension": 0.3,
                    "spanGaps": True
                })
                chart_data_temp["datasets"].append({
                    "label": struct,
                    "data": [data_temp[struct].get(ts) for ts in sorted_ts], 
                    "borderColor": colors_temp[i % len(colors_temp)],
                    "tension": 0.3,
                    "spanGaps": True
                })

        finally:
            conn.close()

    # 3. Obter Previsão do Tempo
    weather_data = None
    try:
        weather_data = get_weather_forecast()
        if weather_data:
            # Converter DataFrames para dicionários para evitar erros no Jinja2
            if hasattr(weather_data.get('hourly'), 'to_dict'):
                weather_data['hourly'] = weather_data['hourly'].to_dict(orient='list')
            if hasattr(weather_data.get('daily'), 'to_dict'):
                weather_data['daily'] = weather_data['daily'].to_dict(orient='list')
    except Exception as e:
        logger.error(f"Erro ao carregar previsão do tempo: {e}")

    return render_template('dashboard.html', 
                           leituras=leituras, 
                           weather=weather_data, 
                           chart_data_ox=json.dumps(chart_data_ox),
                           chart_data_temp=json.dumps(chart_data_temp))

# --- ENDPOINTS DE API (AÇÕES) ---

@app.route('/api/agent', methods=['POST'])
@login_required
def api_agent():
    logger.info("Solicitando análise da IA via Web...")
    conn = get_sqlite_connection()
    if not conn:
        return jsonify({"status": "error", "message": "Erro ao conectar ao banco."}), 500
    
    try:
        yesterday = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
        df = pd.read_sql_query("SELECT * FROM leituras WHERE timestamp_site >= ?", conn, params=(yesterday,))
        
        if df.empty:
            return jsonify({"status": "error", "message": "Sem dados suficientes para análise."})

        parecer = analyze_custom_report_sync(
            "Análise do Dashboard Web (Últimas 24h)",
            "Usuário solicitou análise manual via painel de controle.",
            df.to_csv(index=False)
        )
        return jsonify({"status": "success", "parecer": parecer})
    except Exception as e:
        logger.error(f"Erro na análise da IA via Web: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/scrape', methods=['POST'])
@login_required
def api_scrape():
    logger.info("Iniciando coleta de dados (Scraping) via Web...")
    try:
        scrape_and_save()
        return jsonify({"status": "success", "message": "Coleta concluída com sucesso!"})
    except Exception as e:
        logger.error(f"Erro no scraping via Web: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/sync', methods=['POST'])
@login_required
def api_sync():
    logger.info("Iniciando sincronização de banco via Web...")
    try:
        migrate_data(silent=True)
        return jsonify({"status": "success", "message": "Sincronização concluída!"})
    except Exception as e:
        logger.error(f"Erro na sincronização via Web: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/endpoints', methods=['GET'])
@login_required
def api_endpoints_list():
    """Lista os endpoints conhecidos e seus nomes amigáveis."""
    return jsonify({
        "status": "success",
        "endpoints": [
            {"mac": mac, "nome": nome} for mac, nome in KNOWN_ENDPOINTS.items()
        ]
    })

@app.route('/api/endpoint/<mac>', methods=['GET'])
@login_required
def api_get_endpoint(mac):
    """Consulta os dados atuais de configuração de um endpoint (thresholds, timers, autoOn)."""
    client = NoctuaClient()
    try:
        data = client.get_endpoint_config(mac)
        return jsonify({"status": "success", "endpoint": data})
    except NoctuaClientException as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        logger.error(f"Erro ao buscar endpoint {mac}: {e}")
        return jsonify({"status": "error", "message": "Falha de comunicação com a API Noctua"}), 500

@app.route('/api/endpoint/<mac>/thresholds', methods=['POST'])
@login_required
def api_update_thresholds(mac):
    """Atualiza criticalO2, criticalO2Max e autoOn de um endpoint."""
    client = NoctuaClient()
    payload = request.get_json() or {}
    
    crit_o2 = payload.get('critical_o2')
    crit_o2_max = payload.get('critical_o2_max')
    auto_on = payload.get('auto_on')

    try:
        crit_o2_val = float(crit_o2) if crit_o2 is not None else None
        crit_o2_max_val = float(crit_o2_max) if crit_o2_max is not None else None
        auto_on_val = bool(auto_on) if auto_on is not None else None

        updated = client.update_endpoint_thresholds(
            endpoint_id=mac,
            critical_o2=crit_o2_val,
            critical_o2_max=crit_o2_max_val,
            auto_on=auto_on_val
        )
        return jsonify({"status": "success", "message": "Thresholds atualizados com sucesso!", "data": updated})
    except NoctuaReadOnlyException as e:
        return jsonify({"status": "error", "message": str(e)}), 403
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        logger.error(f"Erro ao atualizar thresholds do endpoint {mac}: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/endpoint/<mac>/timers', methods=['POST'])
@login_required
def api_update_timers(mac):
    """Atualiza a programação horária (timer) de um endpoint."""
    client = NoctuaClient()
    payload = request.get_json() or {}
    timer_data = payload.get('timer')

    if timer_data is None:
        return jsonify({"status": "error", "message": "Campo 'timer' obrigatório."}), 400

    try:
        updated = client.update_endpoint_timer(endpoint_id=mac, timer_data=timer_data)
        return jsonify({"status": "success", "message": "Programação de timers atualizada com sucesso!", "data": updated})
    except NoctuaReadOnlyException as e:
        return jsonify({"status": "error", "message": str(e)}), 403
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        logger.error(f"Erro ao atualizar timer do endpoint {mac}: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/endpoint/<mac>/command', methods=['POST'])
@login_required
def api_send_motor_command(mac):
    """Envia comando de motor para o endpoint respeitando travas de segurança."""
    client = NoctuaClient()
    payload = request.get_json() or {}
    command = payload.get('command')
    message = payload.get('message', 'Acionamento manual via Web Dashboard')

    if not command:
        return jsonify({"status": "error", "message": "Comando não informado."}), 400

    try:
        result = client.send_motor_command(endpoint_id=mac, command=command, message=message)
        return jsonify({"status": "success", "message": "Comando transmitido com sucesso!", "data": result})
    except NoctuaReadOnlyException as e:
        return jsonify({"status": "error", "message": str(e)}), 403
    except NoctuaClientException as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        logger.error(f"Erro ao enviar comando para o endpoint {mac}: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Inicializa banco de usuários
    init_web_auth_db()
    
    web_host = os.environ.get("WEB_HOST", "0.0.0.0")
    web_port = int(os.environ.get("WEB_PORT", 5000))
    app.run(host=web_host, port=web_port, debug=False)
