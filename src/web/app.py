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
from src.services.database import get_sqlite_connection, get_postgres_connection, get_local_now
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
                        diff_min = int((get_local_now() - dt_ts).total_seconds() / 60)
                        minutos_atraso = max(0, diff_min)
                        if diff_min > 30:
                            is_offline = True
                    except Exception:
                        pass
                leituras.append((nome, ox, temp, ts_str, aer, is_offline, minutos_atraso))

            # 2. Obter Histórico de 24h para os Gráficos
            yesterday = (get_local_now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
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
        yesterday = (get_local_now() - timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
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

# ==============================================================================
# --- ROTAS DE GESTÃO DE LOTES (BATCH MANAGEMENT / FICHA VERDE) ---
# ==============================================================================

@app.route('/lotes')
@login_required
def lotes_view():
    """Renderiza a interface de gestão de lotes e Ficha Verde."""
    return render_template('lotes.html')

@app.route('/api/lotes', methods=['GET'])
@login_required
def api_get_lotes():
    """Retorna lista de lotes ativos e histórico com métricas zootécnicas."""
    pg = get_postgres_connection()
    if not pg:
        return jsonify({"status": "error", "message": "Falha na conexão com PostgreSQL."}), 500

    try:
        cur = pg.cursor()
        # 1. Lotes Ativos (data_abate IS NULL)
        cur.execute("""
            SELECT l.id, l.estrutura_uid, e.nome as nome_estrutura, l.lote, 
                   l.data_alojamento, l.peixes_alojados, l.peso_medio, l.area_acude, 
                   l.densidade, l.descricao
            FROM lotes l
            JOIN estruturas e ON l.estrutura_uid = e.uid
            WHERE l.data_abate IS NULL
            ORDER BY l.data_alojamento DESC, l.id DESC;
        """)
        ativos_rows = cur.fetchall()
        
        ativos = []
        for r in ativos_rows:
            lote_id = r[0]
            lote_cod = r[3]
            data_aloj = r[4]
            peixes_aloj = r[5] or 0
            peso_inicial_g = float(r[6] or 35.0)
            
            # Dias de cultivo
            hoje = get_local_now().date()
            dias_cultivo = (hoje - data_aloj).days if data_aloj else 0

            # Totais de biometria e mortalidade acumulada
            cur.execute("""
                SELECT COALESCE(SUM(mortalidade), 0), COALESCE(SUM(consumo_racao), 0)
                FROM biometria
                WHERE lote = %s;
            """, (lote_cod,))
            mort_tot, racao_tot = cur.fetchone()

            # Último peso médio amostrado
            cur.execute("""
                SELECT peso_medio
                FROM biometria
                WHERE lote = %s AND peso_medio IS NOT NULL
                ORDER BY data_biometria DESC, id DESC
                LIMIT 1;
            """, (lote_cod,))
            last_peso_row = cur.fetchone()
            peso_atual_g = float(last_peso_row[0]) if last_peso_row else peso_inicial_g

            # Conversão alimentar (CA): Ração consumida / Biomassa produzida
            peixes_vivos = max(0, peixes_aloj - mort_tot)
            biomassa_atual_kg = (peixes_vivos * peso_atual_g) / 1000.0
            biomassa_inicial_kg = (peixes_aloj * peso_inicial_g) / 1000.0
            ganho_biomassa_kg = max(0.01, biomassa_atual_kg - biomassa_inicial_kg)
            ca = (racao_tot / ganho_biomassa_kg) if (racao_tot > 0 and ganho_biomassa_kg > 0) else None

            ativos.append({
                "id": lote_id,
                "estrutura_uid": r[1],
                "nome_estrutura": r[2],
                "lote": lote_cod,
                "data_alojamento": data_aloj.strftime("%d/%m/%Y") if data_aloj else "--",
                "dias_cultivo": max(0, dias_cultivo),
                "peixes_alojados": peixes_aloj,
                "mortalidade_acumulada": int(mort_tot or 0),
                "racao_acumulada_kg": float(racao_tot or 0.0),
                "peso_atual_g": peso_atual_g,
                "densidade": float(r[8]) if r[8] else None,
                "conversao_alimentar": ca,
                "descricao": r[9]
            })

        # 2. Histórico de Safras (data_abate IS NOT NULL)
        cur.execute("""
            SELECT l.id, l.estrutura_uid, e.nome as nome_estrutura, l.lote, 
                   l.data_alojamento, l.data_abate, l.peixes_alojados, 
                   l.qtd_peixes_entregues, l.peso_entregue, l.pct_rend_file, 
                   l.reais_por_peixe, l.descricao
            FROM lotes l
            JOIN estruturas e ON l.estrutura_uid = e.uid
            WHERE l.data_abate IS NOT NULL
            ORDER BY l.data_abate DESC, l.id DESC;
        """)
        hist_rows = cur.fetchall()
        historico = []
        for r in hist_rows:
            d_aloj = r[4]
            d_abate = r[5]
            duracao = (d_abate - d_aloj).days if (d_aloj and d_abate) else 0
            historico.append({
                "id": r[0],
                "estrutura_uid": r[1],
                "nome_estrutura": r[2],
                "lote": r[3],
                "data_alojamento": d_aloj.strftime("%d/%m/%Y") if d_aloj else "--",
                "data_abate": d_abate.strftime("%d/%m/%Y") if d_abate else "--",
                "dias_cultivo": max(0, duracao),
                "peixes_alojados": r[6],
                "qtd_peixes_entregues": r[7],
                "peso_entregue": float(r[8]) if r[8] else None,
                "pct_rend_file": float(r[9]) if r[9] else None,
                "reais_por_peixe": float(r[10]) if r[10] else None,
                "descricao": r[11]
            })

        pg.close()
        return jsonify({"status": "ok", "ativos": ativos, "historico": historico})

    except Exception as e:
        logger.error(f"Erro ao consultar lotes: {e}")
        if pg: pg.close()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/lotes', methods=['POST'])
@login_required
def api_criar_lote():
    """Cria um novo lote (ativo ou histórico) no PostgreSQL."""
    data = request.get_json() or {}
    estrutura_uid = data.get('estrutura_uid')
    lote = (data.get('lote') or '').strip()
    data_alojamento = data.get('data_alojamento')
    data_abate = data.get('data_abate') or None
    peixes_alojados = data.get('peixes_alojados') or 0
    peso_medio = data.get('peso_medio') or 0.0
    area_acude = data.get('area_acude') or None
    densidade = data.get('densidade')
    descricao = data.get('descricao') or ''

    # Campos de fechamento caso seja inserção histórica
    qtd_peixes_entregues = data.get('qtd_peixes_entregues') or None
    peso_entregue = data.get('peso_entregue') or None
    pct_rend_file = data.get('pct_rend_file') or None
    reais_por_peixe = data.get('reais_por_peixe') or None

    if not estrutura_uid or not lote or not data_alojamento:
        return jsonify({"status": "error", "message": "Estrutura, lote e data de alojamento são obrigatórios."}), 400

    pg = get_postgres_connection()
    if not pg:
        return jsonify({"status": "error", "message": "Falha na conexão com PostgreSQL."}), 500

    try:
        cur = pg.cursor()
        cur.execute("""
            INSERT INTO lotes (
                estrutura_uid, lote, data_alojamento, data_abate, peixes_alojados,
                peso_medio, area_acude, densidade, qtd_peixes_entregues, peso_entregue,
                pct_rend_file, reais_por_peixe, descricao
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            estrutura_uid, lote, data_alojamento, data_abate, int(peixes_alojados or 0),
            float(peso_medio or 0), float(area_acude) if area_acude else None,
            float(densidade) if (densidade and densidade != '--') else None,
            int(qtd_peixes_entregues) if qtd_peixes_entregues else None,
            float(peso_entregue) if peso_entregue else None,
            float(pct_rend_file) if pct_rend_file else None,
            float(reais_por_peixe) if reais_por_peixe else None,
            descricao
        ))
        novo_id = cur.fetchone()[0]
        pg.commit()
        pg.close()
        logger.info(f"Novo lote '{lote}' cadastrado com sucesso (ID: {novo_id}).")
        return jsonify({"status": "ok", "message": "Lote criado com sucesso!", "id": novo_id})

    except Exception as e:
        logger.error(f"Erro ao criar lote: {e}")
        if pg: pg.close()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/lotes/<int:lote_id>/fechar', methods=['POST'])
@login_required
def api_fechar_lote(lote_id):
    """Realiza o fechamento/despesca de um lote ativo no PostgreSQL."""
    data = request.get_json() or {}
    data_abate = data.get('data_abate')
    qtd_peixes_entregues = data.get('qtd_peixes_entregues')
    peso_entregue = data.get('peso_entregue')
    pct_rend_file = data.get('pct_rend_file') or None
    reais_por_peixe = data.get('reais_por_peixe') or None

    if not data_abate or not qtd_peixes_entregues or not peso_entregue:
        return jsonify({"status": "error", "message": "Data de abate, quantidade e peso entregues são obrigatórios."}), 400

    pg = get_postgres_connection()
    if not pg:
        return jsonify({"status": "error", "message": "Falha na conexão com PostgreSQL."}), 500

    try:
        cur = pg.cursor()
        cur.execute("""
            UPDATE lotes
            SET data_abate = %s,
                qtd_peixes_entregues = %s,
                peso_entregue = %s,
                pct_rend_file = %s,
                reais_por_peixe = %s
            WHERE id = %s;
        """, (
            data_abate, int(qtd_peixes_entregues), float(peso_entregue),
            float(pct_rend_file) if pct_rend_file else None,
            float(reais_por_peixe) if reais_por_peixe else None,
            lote_id
        ))
        pg.commit()
        pg.close()
        logger.info(f"Lote ID {lote_id} encerrado com sucesso.")
        return jsonify({"status": "ok", "message": "Lote encerrado com sucesso!"})

    except Exception as e:
        logger.error(f"Erro ao encerrar lote {lote_id}: {e}")
        if pg: pg.close()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/lotes/<int:lote_id>/biometria', methods=['POST'])
@login_required
def api_salvar_biometria(lote_id):
    """Registra lançamento de biometria, mortalidade e/ou ração na tabela biometria."""
    data = request.get_json() or {}
    data_biometria = data.get('data_biometria') or data.get('data_registro') or get_local_now().date().isoformat()
    peso_medio = data.get('peso_medio')
    quantidade = data.get('quantidade') or None
    mortalidade = data.get('mortalidade') or 0
    consumo_racao = data.get('consumo_racao') or 0.0

    pg = get_postgres_connection()
    if not pg:
        return jsonify({"status": "error", "message": "Falha na conexão com PostgreSQL."}), 500

    try:
        cur = pg.cursor()
        # Buscar dados do lote (estrutura_uid e código do lote)
        cur.execute("SELECT estrutura_uid, lote FROM lotes WHERE id = %s;", (lote_id,))
        row = cur.fetchone()
        if not row:
            pg.close()
            return jsonify({"status": "error", "message": "Lote não encontrado."}), 404

        estrutura_uid, lote_cod = row

        cur.execute("""
            INSERT INTO biometria (
                estrutura_uid, lote, data_biometria, quantidade, peso_medio, mortalidade, consumo_racao
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            estrutura_uid, lote_cod, data_biometria,
            int(quantidade) if quantidade else None,
            float(peso_medio) if peso_medio else None,
            int(mortalidade or 0),
            float(consumo_racao or 0.0)
        ))
        novo_id = cur.fetchone()[0]
        pg.commit()
        pg.close()
        logger.info(f"Biometria/Mortalidade inserida para lote {lote_cod} (ID: {novo_id}).")
        return jsonify({"status": "ok", "message": "Lançamento registrado com sucesso!", "id": novo_id})

    except Exception as e:
        logger.error(f"Erro ao inserir biometria para lote {lote_id}: {e}")
        if pg: pg.close()
        return jsonify({"status": "error", "message": str(e)}), 500

# ==============================================================================
# --- ROTAS DE CONFIGURAÇÕES, MDM E CRUD DE BANCO ---
# ==============================================================================

@app.route('/settings')
@login_required
def settings_view():
    """Renderiza a interface de Configurações, MDM e CRUD de Banco de Dados."""
    return render_template('settings.html')

@app.route('/api/mdm/estruturas', methods=['GET', 'POST'])
@login_required
def api_mdm_estruturas():
    """Lista ou cadastra estruturas físicas."""
    pg = get_postgres_connection()
    if not pg:
        return jsonify([] if request.method == 'GET' else {"status": "error", "message": "PostgreSQL indisponível."}), 500

    try:
        cur = pg.cursor()
        if request.method == 'GET':
            cur.execute("""
                SELECT e.uid, e.nome, e.pluscode, l.lote as lote_ativo
                FROM estruturas e
                LEFT JOIN lotes l ON e.uid = l.estrutura_uid AND l.data_abate IS NULL
                ORDER BY e.nome;
            """)
            rows = cur.fetchall()
            estruturas = []
            for r in rows:
                mac_vinculado = KNOWN_ENDPOINTS.get(r[1]) or None
                estruturas.append({
                    "uid": r[0],
                    "nome": r[1],
                    "pluscode": r[2],
                    "lote_ativo": r[3],
                    "mac": mac_vinculado
                })
            pg.close()
            return jsonify(estruturas)

        elif request.method == 'POST':
            data = request.get_json() or {}
            nome = (data.get('nome') or '').strip()
            pluscode = (data.get('pluscode') or '87G8+H6 Toledo').strip()
            mac = (data.get('mac') or '').strip().upper()

            if not nome:
                pg.close()
                return jsonify({"status": "error", "message": "Nome da estrutura é obrigatório."}), 400

            # Gerar UID consistente via SHA256(nome + pluscode)
            import hashlib
            uid = hashlib.sha256(f"{nome}{pluscode}".encode('utf-8')).hexdigest()

            # Buscar primeira propriedade
            cur.execute("SELECT uid FROM propriedades LIMIT 1;")
            p_row = cur.fetchone()
            prop_uid = p_row[0] if p_row else None

            cur.execute("""
                INSERT INTO estruturas (uid, propriedade_uid, tipo_exploracao_id, nome, pluscode)
                VALUES (%s, %s, 1, %s, %s)
                ON CONFLICT (uid) DO UPDATE SET nome = EXCLUDED.nome, pluscode = EXCLUDED.pluscode;
            """, (uid, prop_uid, nome, pluscode))
            pg.commit()

            # Se informou MAC, vincula em tempo de execução
            if mac:
                KNOWN_ENDPOINTS[mac] = nome

            pg.close()
            return jsonify({"status": "ok", "message": f"Estrutura '{nome}' salva com sucesso!", "uid": uid})

    except Exception as e:
        logger.error(f"Erro em /api/mdm/estruturas: {e}")
        if pg: pg.close()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/mdm/dados', methods=['GET'])
@login_required
def api_mdm_dados():
    """Retorna dados consolidados de Proprietário, Propriedade e Estruturas."""
    pg = get_postgres_connection()
    if not pg:
        return jsonify({"status": "error", "message": "PostgreSQL indisponível."}), 500

    try:
        cur = pg.cursor()
        cur.execute("SELECT uid, nome, cpf FROM proprietarios LIMIT 1;")
        p_row = cur.fetchone()
        proprietario = {"uid": p_row[0], "nome": p_row[1], "cpf": p_row[2]} if p_row else None

        cur.execute("SELECT uid, proprietario_uid, nome, endereco, cadpro FROM propriedades LIMIT 1;")
        prop_row = cur.fetchone()
        propriedade = {
            "uid": prop_row[0], "proprietario_uid": prop_row[1], "nome": prop_row[2],
            "endereco": prop_row[3], "cadpro": prop_row[4]
        } if prop_row else None

        cur.execute("""
            SELECT e.uid, e.nome, e.pluscode, l.lote as lote_ativo
            FROM estruturas e
            LEFT JOIN lotes l ON e.uid = l.estrutura_uid AND l.data_abate IS NULL
            ORDER BY e.nome;
        """)
        est_rows = cur.fetchall()
        estruturas = []
        for r in est_rows:
            # Buscar MAC correspondente no KNOWN_ENDPOINTS
            mac = None
            for m, name in KNOWN_ENDPOINTS.items():
                if name.lower() == r[1].lower():
                    mac = m
                    break
            estruturas.append({
                "uid": r[0], "nome": r[1], "pluscode": r[2], "lote_ativo": r[3], "mac": mac
            })

        pg.close()
        return jsonify({
            "status": "ok",
            "proprietario": proprietario,
            "propriedade": propriedade,
            "estruturas": estruturas
        })

    except Exception as e:
        logger.error(f"Erro ao carregar dados MDM: {e}")
        if pg: pg.close()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/mdm/proprietario', methods=['POST'])
@login_required
def api_mdm_salvar_proprietario():
    """Atualiza ou insere o registro do produtor (proprietário)."""
    data = request.get_json() or {}
    nome = (data.get('nome') or '').strip()
    cpf = (data.get('cpf') or '').strip()

    if not nome or not cpf:
        return jsonify({"status": "error", "message": "Nome e CPF são obrigatórios."}), 400

    import hashlib
    uid = hashlib.sha256(f"{nome}{cpf}".encode('utf-8')).hexdigest()

    pg = get_postgres_connection()
    if not pg:
        return jsonify({"status": "error", "message": "PostgreSQL indisponível."}), 500

    try:
        cur = pg.cursor()
        cur.execute("""
            INSERT INTO proprietarios (uid, nome, cpf)
            VALUES (%s, %s, %s)
            ON CONFLICT (uid) DO UPDATE SET nome = EXCLUDED.nome, cpf = EXCLUDED.cpf;
        """, (uid, nome, cpf))
        pg.commit()
        pg.close()
        return jsonify({"status": "ok", "message": "Produtor salvo com sucesso!", "uid": uid})
    except Exception as e:
        if pg: pg.close()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/mdm/propriedade', methods=['POST'])
@login_required
def api_mdm_salvar_propriedade():
    """Atualiza ou insere o registro da propriedade rural."""
    data = request.get_json() or {}
    nome = (data.get('nome') or '').strip()
    endereco = (data.get('endereco') or '').strip()
    cadpro = (data.get('cadpro') or '').strip()

    if not nome or not endereco or not cadpro:
        return jsonify({"status": "error", "message": "Nome, endereço e CADPRO são obrigatórios."}), 400

    import hashlib
    uid = hashlib.sha256(f"{endereco}{cadpro}".encode('utf-8')).hexdigest()

    pg = get_postgres_connection()
    if not pg:
        return jsonify({"status": "error", "message": "PostgreSQL indisponível."}), 500

    try:
        cur = pg.cursor()
        cur.execute("SELECT uid FROM proprietarios LIMIT 1;")
        p_row = cur.fetchone()
        prop_uid = p_row[0] if p_row else None

        cur.execute("""
            INSERT INTO propriedades (uid, proprietario_uid, nome, endereco, cadpro)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (uid) DO UPDATE SET nome = EXCLUDED.nome, endereco = EXCLUDED.endereco, cadpro = EXCLUDED.cadpro;
        """, (uid, prop_uid, nome, endereco, cadpro))
        pg.commit()
        pg.close()
        return jsonify({"status": "ok", "message": "Propriedade salva com sucesso!", "uid": uid})
    except Exception as e:
        if pg: pg.close()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/settings/db/status', methods=['GET'])
@login_required
def api_settings_db_status():
    """Testa a conectividade com o PostgreSQL e retorna volumetria."""
    import time
    start = time.time()
    pg = get_postgres_connection()
    if not pg:
        return jsonify({"status": "error", "message": "Não foi possível conectar ao PostgreSQL."}), 500

    try:
        latencia_ms = round((time.time() - start) * 1000, 2)
        cur = pg.cursor()
        counts = {}
        for tbl in ['lotes', 'biometria', 'leituras', 'estruturas']:
            cur.execute(f"SELECT COUNT(*) FROM {tbl};")
            counts[tbl] = cur.fetchone()[0]

        pg.close()
        return jsonify({
            "status": "ok",
            "latencia_ms": latencia_ms,
            "host": os.environ.get("PG_HOST", "localhost"),
            "port": os.environ.get("PG_PORT", 5432),
            "database": os.environ.get("PG_DBNAME", "piscicultura_history"),
            "counts": counts
        })
    except Exception as e:
        if pg: pg.close()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/settings/db/table/<nome_tabela>', methods=['GET'])
@login_required
def api_settings_db_table(nome_tabela):
    """Inspeciona os registros de uma tabela com allowlist estrita."""
    allowlist = [
        'lotes', 'biometria', 'estruturas', 'leituras', 
        'qualidade_agua_limnologia', 'qualidade_agua_consumo', 
        'clima_historico', 'historico_pareceres_ia'
    ]
    if nome_tabela not in allowlist:
        return jsonify({"status": "error", "message": "Tabela não permitida para inspeção."}), 400

    pg = get_postgres_connection()
    if not pg:
        return jsonify({"status": "error", "message": "PostgreSQL indisponível."}), 500

    try:
        cur = pg.cursor()
        cur.execute(f"SELECT * FROM {nome_tabela} ORDER BY 1 DESC LIMIT 50;")
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        
        # Converter para strings/formatos serializáveis
        serializable_rows = []
        for row in rows:
            formatted_row = []
            for item in row:
                if isinstance(item, (datetime, timedelta)):
                    formatted_row.append(str(item))
                elif item is None:
                    formatted_row.append(None)
                else:
                    formatted_row.append(str(item))
            serializable_rows.append(formatted_row)

        pg.close()
        return jsonify({"status": "ok", "tabela": nome_tabela, "columns": columns, "rows": serializable_rows})
    except Exception as e:
        if pg: pg.close()
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Inicializa banco de usuários
    init_web_auth_db()
    
    web_host = os.environ.get("WEB_HOST", "0.0.0.0")
    web_port = int(os.environ.get("WEB_PORT", 5000))
    app.run(host=web_host, port=web_port, debug=False)

