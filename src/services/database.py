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

from datetime import datetime, timezone, timedelta
try:
    from zoneinfo import ZoneInfo
    TIMEZONE_LOCAL = ZoneInfo("America/Sao_Paulo")
except Exception:
    TIMEZONE_LOCAL = timezone(timedelta(hours=-3))

def get_local_now() -> datetime:
    """Retorna datetime ingênuo representando o horário local de Brasília (America/Sao_Paulo)."""
    try:
        return datetime.now(TIMEZONE_LOCAL).replace(tzinfo=None)
    except Exception:
        return datetime.now()

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
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
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
        # Trunca parecer para no máximo 500 caracteres no banco, ideal para contexto de prompt sem inflar tokens
        parecer_trunc = (parecer or "")[:500].strip()
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

def is_system_suspended() -> bool:
    """Verifica se o arquivo de flag de suspensão existe."""
    proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    flag_path = os.path.join(proj_root, "data", "suspended.flag")
    return os.path.exists(flag_path)

def set_system_suspended(suspended: bool):
    """Ativa ou desativa a suspensão criando/removendo o arquivo de flag."""
    proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    data_dir = os.path.join(proj_root, "data")
    os.makedirs(data_dir, exist_ok=True)
    flag_path = os.path.join(data_dir, "suspended.flag")
    if suspended:
        with open(flag_path, "w", encoding="utf-8") as f:
            f.write("suspended")
    else:
        if os.path.exists(flag_path):
            os.remove(flag_path)


# ==============================================================================
# GESTÃO DINÂMICA DE CONTATOS WHATSAPP (EVOLUTION API)
# ==============================================================================

DEFAULT_WHATSAPP_SEED = [
    ("Dirceu Patel", "Sogro / Gestor", "", False, True, True),
    ("Joceli Patel", "Sogra / Gestora", "", False, True, True),
]

def ensure_contatos_whatsapp_table():
    """
    Garante a criação da tabela contatos_whatsapp no PostgreSQL (primário)
    e no SQLite (fallback local/testes), inserindo o seed inicial (Dirceu e Joceli)
    apenas quando a tabela está completamente vazia (COUNT(*) == 0).
    """
    # 1. Garantir no SQLite local (para fallback e testes isolados)
    sq_conn = get_sqlite_connection()
    if sq_conn:
        try:
            cur = sq_conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS contatos_whatsapp (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    papel TEXT DEFAULT 'Familiar / Gestor',
                    telefone TEXT NOT NULL DEFAULT '',
                    ativo INTEGER DEFAULT 1,
                    receber_alertas INTEGER DEFAULT 1,
                    receber_relatorios INTEGER DEFAULT 1,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.execute("SELECT COUNT(*) FROM contatos_whatsapp;")
            if cur.fetchone()[0] == 0:
                for nome, papel, tel, ativo, alertas, rels in DEFAULT_WHATSAPP_SEED:
                    cur.execute("""
                        INSERT INTO contatos_whatsapp (nome, papel, telefone, ativo, receber_alertas, receber_relatorios)
                        VALUES (?, ?, ?, ?, ?, ?);
                    """, (nome, papel, tel, int(ativo), int(alertas), int(rels)))
            sq_conn.commit()
        except Exception as e:
            logger.error(f"Erro ao inicializar contatos_whatsapp no SQLite: {e}")
        finally:
            sq_conn.close()

    # 2. Garantir no PostgreSQL (SSOT de produção)
    pg_conn = get_postgres_connection()
    if pg_conn:
        try:
            cur = pg_conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS contatos_whatsapp (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(150) NOT NULL,
                    papel VARCHAR(100) DEFAULT 'Familiar / Gestor',
                    telefone VARCHAR(30) NOT NULL DEFAULT '',
                    ativo BOOLEAN DEFAULT TRUE,
                    receber_alertas BOOLEAN DEFAULT TRUE,
                    receber_relatorios BOOLEAN DEFAULT TRUE,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.execute("SELECT COUNT(*) FROM contatos_whatsapp;")
            if cur.fetchone()[0] == 0:
                for nome, papel, tel, ativo, alertas, rels in DEFAULT_WHATSAPP_SEED:
                    cur.execute("""
                        INSERT INTO contatos_whatsapp (nome, papel, telefone, ativo, receber_alertas, receber_relatorios)
                        VALUES (%s, %s, %s, %s, %s, %s);
                    """, (nome, papel, tel, ativo, alertas, rels))
            pg_conn.commit()
        except Exception as e:
            logger.error(f"Erro ao inicializar contatos_whatsapp no PostgreSQL: {e}")
            pg_conn.rollback()
        finally:
            pg_conn.close()


def listar_contatos_whatsapp(
    apenas_ativos: bool = False,
    apenas_alertas: bool = False,
    apenas_relatorios: bool = False
) -> list:
    """Retorna lista de contatos WhatsApp do PostgreSQL (ou SQLite em fallback)."""
    ensure_contatos_whatsapp_table()
    pg_conn = get_postgres_connection()
    if pg_conn:
        try:
            cur = pg_conn.cursor()
            query = """
                SELECT id, nome, papel, telefone, ativo, receber_alertas, receber_relatorios
                FROM contatos_whatsapp
                WHERE 1=1
            """
            if apenas_ativos:
                query += " AND ativo = TRUE AND TRIM(telefone) <> ''"
            if apenas_alertas:
                query += " AND receber_alertas = TRUE"
            if apenas_relatorios:
                query += " AND receber_relatorios = TRUE"
            query += " ORDER BY id ASC;"
            cur.execute(query)
            rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "nome": r[1],
                    "papel": r[2] or "",
                    "telefone": r[3] or "",
                    "ativo": bool(r[4]),
                    "receber_alertas": bool(r[5]),
                    "receber_relatorios": bool(r[6]),
                }
                for r in rows
            ]
        except Exception as e:
            logger.error(f"Erro ao listar contatos_whatsapp no Postgres: {e}")
        finally:
            pg_conn.close()

    sq_conn = get_sqlite_connection()
    if not sq_conn:
        return []
    try:
        cur = sq_conn.cursor()
        query = """
            SELECT id, nome, papel, telefone, ativo, receber_alertas, receber_relatorios
            FROM contatos_whatsapp
            WHERE 1=1
        """
        if apenas_ativos:
            query += " AND ativo = 1 AND TRIM(telefone) <> ''"
        if apenas_alertas:
            query += " AND receber_alertas = 1"
        if apenas_relatorios:
            query += " AND receber_relatorios = 1"
        query += " ORDER BY id ASC;"
        cur.execute(query)
        rows = cur.fetchall()
        return [
            {
                "id": r[0],
                "nome": r[1],
                "papel": r[2] or "",
                "telefone": r[3] or "",
                "ativo": bool(r[4]),
                "receber_alertas": bool(r[5]),
                "receber_relatorios": bool(r[6]),
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"Erro ao listar contatos_whatsapp no SQLite: {e}")
        return []
    finally:
        sq_conn.close()


def obter_contato_whatsapp(contato_id: int) -> dict | None:
    """Busca um contato WhatsApp específico pelo ID."""
    todos = listar_contatos_whatsapp(apenas_ativos=False)
    for c in todos:
        if c["id"] == int(contato_id):
            return c
    return None


def salvar_contato_whatsapp(dados: dict) -> dict:
    """Cria ou atualiza um contato WhatsApp no PostgreSQL e SQLite."""
    ensure_contatos_whatsapp_table()
    contato_id = dados.get("id")
    nome = (dados.get("nome") or "").strip()
    papel = (dados.get("papel") or "Familiar / Gestor").strip()
    telefone = "".join(ch for ch in str(dados.get("telefone") or "") if ch.isdigit())
    ativo = bool(dados.get("ativo", True))
    receber_alertas = bool(dados.get("receber_alertas", True))
    receber_relatorios = bool(dados.get("receber_relatorios", True))

    if not nome:
        raise ValueError("O nome do contato é obrigatório.")

    pg_conn = get_postgres_connection()
    if pg_conn:
        try:
            cur = pg_conn.cursor()
            if contato_id:
                cur.execute("""
                    UPDATE contatos_whatsapp
                    SET nome = %s, papel = %s, telefone = %s, ativo = %s,
                        receber_alertas = %s, receber_relatorios = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    RETURNING id;
                """, (nome, papel, telefone, ativo, receber_alertas, receber_relatorios, int(contato_id)))
                row = cur.fetchone()
                novo_id = row[0] if row else int(contato_id)
            else:
                cur.execute("""
                    INSERT INTO contatos_whatsapp (nome, papel, telefone, ativo, receber_alertas, receber_relatorios)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """, (nome, papel, telefone, ativo, receber_alertas, receber_relatorios))
                novo_id = cur.fetchone()[0]
            pg_conn.commit()
            return {
                "id": novo_id, "nome": nome, "papel": papel, "telefone": telefone,
                "ativo": ativo, "receber_alertas": receber_alertas, "receber_relatorios": receber_relatorios
            }
        except Exception as e:
            pg_conn.rollback()
            logger.error(f"Erro ao salvar contato_whatsapp no Postgres: {e}")
            raise
        finally:
            pg_conn.close()

    sq_conn = get_sqlite_connection()
    if not sq_conn:
        raise RuntimeError("Nenhum banco de dados disponível para salvar o contato.")
    try:
        cur = sq_conn.cursor()
        if contato_id:
            cur.execute("""
                UPDATE contatos_whatsapp
                SET nome = ?, papel = ?, telefone = ?, ativo = ?,
                    receber_alertas = ?, receber_relatorios = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?;
            """, (nome, papel, telefone, int(ativo), int(receber_alertas), int(receber_relatorios), int(contato_id)))
            novo_id = int(contato_id)
        else:
            cur.execute("""
                INSERT INTO contatos_whatsapp (nome, papel, telefone, ativo, receber_alertas, receber_relatorios)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (nome, papel, telefone, int(ativo), int(receber_alertas), int(receber_relatorios)))
            novo_id = cur.lastrowid
        sq_conn.commit()
        return {
            "id": novo_id, "nome": nome, "papel": papel, "telefone": telefone,
            "ativo": ativo, "receber_alertas": receber_alertas, "receber_relatorios": receber_relatorios
        }
    finally:
        sq_conn.close()


def excluir_contato_whatsapp(contato_id: int) -> bool:
    """Remove um contato WhatsApp pelo ID."""
    ensure_contatos_whatsapp_table()
    pg_conn = get_postgres_connection()
    if pg_conn:
        try:
            cur = pg_conn.cursor()
            cur.execute("DELETE FROM contatos_whatsapp WHERE id = %s;", (int(contato_id),))
            deleted = cur.rowcount > 0
            pg_conn.commit()
            return deleted
        except Exception as e:
            pg_conn.rollback()
            logger.error(f"Erro ao excluir contato_whatsapp no Postgres: {e}")
            return False
        finally:
            pg_conn.close()

    sq_conn = get_sqlite_connection()
    if not sq_conn:
        return False
    try:
        cur = sq_conn.cursor()
        cur.execute("DELETE FROM contatos_whatsapp WHERE id = ?;", (int(contato_id),))
        deleted = cur.rowcount > 0
        sq_conn.commit()
        return deleted
    finally:
        sq_conn.close()


