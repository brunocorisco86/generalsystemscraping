import os
import sys
import hashlib
import sqlite3
import asyncio
import asyncpg
import logging
from pathlib import Path
from dotenv import load_dotenv

# Adiciona a raiz do projeto ao sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Carrega .env
load_dotenv(project_root / ".env")

from src.services.database import SQLITE_DB_PATH  # noqa: E402

# Configuração de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configurações Postgres (Reaproveitadas do init_db ou .env direto)
PG_HOST = os.environ.get("PG_HOST")
PG_DBNAME = os.environ.get("PG_DBNAME")
PG_USER = os.environ.get("PG_USER")
PG_PASSWORD = os.environ.get("PG_PASSWORD")
PG_PORT = os.environ.get("PG_PORT", 5432)
PG_DSN = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DBNAME}"

def generate_sha256(data_string: str) -> str:
    """Gera um hash SHA256 a partir de uma string."""
    return hashlib.sha256(data_string.encode('utf-8')).hexdigest()

def get_env_data():
    """Recupera e valida dados de cadastro do .env."""
    data = {
        "owner": {
            "name": os.environ.get("OWNER_NAME"),
            "cpf": os.environ.get("OWNER_CPF"),
        },
        "property": {
            "name": os.environ.get("PROP_NAME"),
            "address": os.environ.get("PROP_ADDRESS"),
            "cadpro": os.environ.get("PROP_CADPRO"),
        },
        "structure": {
            "name": os.environ.get("STRUCT_NAME"),
            "pluscode": os.environ.get("STRUCT_PLUSCODE"),
            "type_id": os.environ.get("STRUCT_TYPE_ID"),
        }
    }

    # Validação simples
    if not all([data["owner"]["name"], data["owner"]["cpf"], data["property"]["address"], data["structure"]["pluscode"]]):
        logger.error("Dados de cadastro incompletos no .env. Verifique OWNER_*, PROP_* e STRUCT_*")
        return None

    return data

async def populate_postgres(data):
    """Popula o Postgres com os dados do .env."""
    if not all([PG_HOST, PG_DBNAME, PG_USER, PG_PASSWORD]):
        logger.warning("Postgres não configurado. Pulando população do Postgres.")
        return

    try:
        conn = await asyncpg.connect(dsn=PG_DSN)

        # Gera Hashes
        owner_uid = generate_sha256(data["owner"]["name"] + data["owner"]["cpf"])
        prop_uid = generate_sha256(data["property"]["address"] + data["property"]["cadpro"])
        struct_uid = generate_sha256(data["structure"]["name"] + data["structure"]["pluscode"])

        # Insere Proprietário
        await conn.execute('''
            INSERT INTO proprietarios (uid, nome, cpf) VALUES ($1, $2, $3)
            ON CONFLICT (uid) DO UPDATE SET nome = EXCLUDED.nome, cpf = EXCLUDED.cpf;
        ''', owner_uid, data["owner"]["name"], data["owner"]["cpf"])

        # Insere Propriedade
        await conn.execute('''
            INSERT INTO propriedades (uid, proprietario_uid, nome, endereco, cadpro) VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (uid) DO UPDATE SET nome = EXCLUDED.nome, endereco = EXCLUDED.endereco;
        ''', prop_uid, owner_uid, data["property"]["name"], data["property"]["address"], data["property"]["cadpro"])

        # Insere Estrutura
        type_id = int(data["structure"]["type_id"]) if data["structure"]["type_id"] else 1
        await conn.execute('''
            INSERT INTO estruturas (uid, propriedade_uid, tipo_exploracao_id, nome, pluscode) VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (uid) DO UPDATE SET
                nome = EXCLUDED.nome,
                pluscode = EXCLUDED.pluscode,
                tipo_exploracao_id = EXCLUDED.tipo_exploracao_id;
        ''', struct_uid, prop_uid, type_id, data["structure"]["name"], data["structure"]["pluscode"])

        await conn.close()
        logger.info("✅ Dados iniciais populados no Postgres com sucesso!")
    except Exception as e:
        logger.error(f"❌ Erro ao popular Postgres: {e}")

def populate_sqlite(data):
    """Popula o SQLite com os dados do .env."""
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()

        # Gera Hashes
        owner_uid = generate_sha256(data["owner"]["name"] + data["owner"]["cpf"])
        prop_uid = generate_sha256(data["property"]["address"] + data["property"]["cadpro"])
        struct_uid = generate_sha256(data["structure"]["name"] + data["structure"]["pluscode"])

        # Insere Proprietário
        cursor.execute('''
            INSERT OR REPLACE INTO proprietarios (uid, nome, cpf) VALUES (?, ?, ?)
        ''', (owner_uid, data["owner"]["name"], data["owner"]["cpf"]))

        # Insere Propriedade
        cursor.execute('''
            INSERT OR REPLACE INTO propriedades (uid, proprietario_uid, nome, endereco, cadpro) VALUES (?, ?, ?, ?, ?)
        ''', (prop_uid, owner_uid, data["property"]["name"], data["property"]["address"], data["property"]["cadpro"]))

        # Insere Estrutura
        cursor.execute('''
            INSERT OR REPLACE INTO estruturas (uid, propriedade_uid, tipo_exploracao_id, nome, pluscode) VALUES (?, ?, ?, ?, ?)
        ''', (struct_uid, prop_uid, int(data["structure"]["type_id"]), data["structure"]["name"], data["structure"]["pluscode"]))

        conn.commit()
        conn.close()
        logger.info("✅ Dados iniciais populados no SQLite com sucesso!")
    except Exception as e:
        logger.error(f"❌ Erro ao popular SQLite: {e}")

async def main():
    logger.info("--- Iniciando População de Dados Cadastrais ---")
    data = get_env_data()
    if data:
        populate_sqlite(data)
        await populate_postgres(data)
    else:
        logger.error("Falha ao obter dados do .env. Abortando.")

if __name__ == "__main__":
    asyncio.run(main())
