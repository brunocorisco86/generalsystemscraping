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

def get_default_estrutura_info():
    """Retorna as informações da estrutura configurada no .env."""
    return {
        "nome": os.environ.get("STRUCT_NAME"),
        "pluscode": os.environ.get("STRUCT_PLUSCODE"),
        "type_id": os.environ.get("STRUCT_TYPE_ID")
    }
