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
    chart_data = {"labels": [], "datasets": []}
    
    if conn:
        try:
            cursor = conn.cursor()
            # Pega a última leitura de cada estrutura
            cursor.execute('''
                SELECT l1.nome_estrutura, l1.oxigenio, l1.temperatura, l1.timestamp_site, l1.aeradores_ativos
                FROM leituras l1
                INNER JOIN (
                    SELECT nome_estrutura, MAX(timestamp_site) as max_ts
                    FROM leituras
                    GROUP BY nome_estrutura
                ) l2 ON l1.nome_estrutura = l2.nome_estrutura AND l1.timestamp_site = l2.max_ts
            ''')
            leituras = cursor.fetchall()

            # 2. Obter Histórico de 24h para o Gráfico
            yesterday = (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
                SELECT nome_estrutura, oxigenio, timestamp_site
                FROM leituras
                WHERE timestamp_site >= ?
                ORDER BY timestamp_site ASC
            ''', (yesterday,))
            history = cursor.fetchall()
            
            # Formatar dados para o Chart.js
            temp_sets = {}
            labels = set()
            for row in history:
                struct, ox, ts = row
                time_label = ts[11:16] # HH:MM
                labels.add(time_label)
                if struct not in temp_sets:
                    temp_sets[struct] = []
                temp_sets[struct].append({"x": time_label, "y": ox})
            
            chart_data["labels"] = sorted(list(labels))
            colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
            for i, (struct, data) in enumerate(temp_sets.items()):
                chart_data["datasets"].append({
                    "label": struct,
                    "data": [d["y"] for d in data], 
                    "borderColor": colors[i % len(colors)],
                    "tension": 0.3
                })

        finally:
            conn.close()

    # 3. Obter Previsão do Tempo
    weather_data = None
    try:
        weather_data = get_weather_forecast()
    except Exception as e:
        logger.error(f"Erro ao carregar previsão do tempo: {e}")

    return render_template('dashboard.html', 
                           leituras=leituras, 
                           weather=weather_data, 
                           chart_data=json.dumps(chart_data))

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

if __name__ == '__main__':
    # Inicializa banco de usuários
    init_web_auth_db()
    
    # Rodar em 0.0.0.0 para ser acessível na rede local
    app.run(host='0.0.0.0', port=5000, debug=False)
