import os
import sqlite3
import psycopg2
import logging
import hashlib
from dotenv import load_dotenv

# Configuração do logger
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente do arquivo .env
# Tenta carregar do diretório atual ou da raiz do projeto
env_path = os.path.join(os.getcwd(), ".env")
if not os.path.exists(env_path):
    # Procura na raiz se estiver em um subdiretório (src/services)
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

load_dotenv(env_path)

# --- Configurações do .env ---
SQLITE_DB_PATH = os.environ.get("SQLITE_DB_PATH", "data/piscicultura_dados.db")
PG_HOST = os.environ.get("PG_HOST")
PG_DBNAME = os.environ.get("PG_DBNAME")
PG_USER = os.environ.get("PG_USER")
PG_PASSWORD = os.environ.get("PG_PASSWORD")
PG_PORT = os.environ.get("PG_PORT", 5432)

def get_sqlite_connection():
    """Retorna uma conexão com o banco de dados SQLite."""
    try:
        # O check_same_thread=False é necessário se diferentes threads
        # no mesmo processo precisarem acessar o banco, o que pode
        # acontecer em algumas aplicações web ou com bots.
        conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
        return conn
    except sqlite3.Error as e:
        logger.error(f"Erro ao conectar ao SQLite: {e}")
        return None

def get_postgres_connection():
    """Retorna uma conexão com o banco de dados PostgreSQL."""
    if not all([PG_HOST, PG_DBNAME, PG_USER, PG_PASSWORD]):
        logger.warning("Configurações do PostgreSQL incompletas. Conexão não estabelecida.")
        return None
    
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            dbname=PG_DBNAME,
            user=PG_USER,
            password=PG_PASSWORD,
            port=PG_PORT
        )
        return conn
    except psycopg2.OperationalError as e:
        logger.error(f"Erro ao conectar ao PostgreSQL: {e}")
        return None

def generate_sha256(data_string: str) -> str:
    """Gera um hash SHA256 a partir de uma string."""
    return hashlib.sha256(data_string.encode('utf-8')).hexdigest()

def get_estrutura_uid(nome: str, pluscode: str) -> str:
    """Gera o UID para uma estrutura baseado no nome e pluscode."""
    return generate_sha256(nome + pluscode)

def get_all_estruturas_map() -> dict:
    """
    Retorna um dicionário mapeando o nome amigável da estrutura para o seu UID.
    Útil para o scraper resolver UIDs em tempo real.
    """
    conn = get_sqlite_connection()
    if not conn:
        return {}
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT nome, uid FROM estruturas")
        return {row[0]: row[1] for row in cursor.fetchall()}
    except Exception as e:
        logger.error(f"Erro ao buscar mapa de estruturas: {e}")
        return {}
    finally:
        conn.close()

def get_default_estrutura_info():
    """Retorna as informações da estrutura configurada no .env."""
    return {
        "nome": os.environ.get("STRUCT_NAME"),
        "pluscode": os.environ.get("STRUCT_PLUSCODE"),
        "type_id": os.environ.get("STRUCT_TYPE_ID")
    }

def salvar_parecer_ia(contexto: str, parecer: str):
    """Salva o parecer da IA no PostgreSQL de forma compacta."""
    conn = get_postgres_connection()
    if not conn:
        logger.warning("Falha ao conectar ao Postgres para salvar parecer.")
        return
    try:
        cur = conn.cursor()
        # Trunca para economizar espaço e obedecer o schema do banco
        contexto_trunc = (contexto or "Geral")[:100]
        # Trunca parecer para no máximo 250 caracteres no banco, ideal para contexto de prompt sem inflar tokens
        parecer_trunc = (parecer or "")[:250].strip()
        cur.execute(
            "INSERT INTO historico_pareceres_ia (contexto, parecer) VALUES (%s, %s)",
            (contexto_trunc, parecer_trunc)
        )
        conn.commit()
        logger.info("Parecer da IA salvo no Postgres com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao salvar parecer no Postgres: {e}")
        conn.rollback()
    finally:
        conn.close()

def obter_ultimos_pareceres(limite=3) -> list:
    """Busca os últimos pareceres da IA no PostgreSQL para serem usados como contexto."""
    conn = get_postgres_connection()
    if not conn:
        logger.warning("Falha ao conectar ao Postgres para obter últimos pareceres.")
        return []
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT data_registro, contexto, parecer FROM historico_pareceres_ia ORDER BY data_registro DESC LIMIT %s",
            (limite,)
        )
        rows = cur.fetchall()
        # Inverte para manter ordem cronológica no prompt (do mais antigo para o mais recente)
        return list(reversed(rows))
    except Exception as e:
        logger.error(f"Erro ao obter pareceres do Postgres: {e}")
        return []
    finally:
        conn.close()
