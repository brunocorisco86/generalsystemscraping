import os
import sqlite3
import psycopg2
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

# Adiciona a raiz do projeto ao sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Carrega .env da raiz do projeto
load_dotenv(project_root / ".env")

from src.services.database import get_sqlite_connection, get_postgres_connection

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate_sqlite():
    logger.info("Verificando necessidade de migração no SQLite...")
    conn = get_sqlite_connection()
    if not conn:
        logger.error("Falha ao conectar ao SQLite.")
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(clima_historico)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'cloud_cover' not in columns:
            logger.info("Adicionando coluna 'cloud_cover' à tabela 'clima_historico' no SQLite...")
            cursor.execute("ALTER TABLE clima_historico ADD COLUMN cloud_cover REAL")
            conn.commit()
            logger.info("✅ SQLite atualizado com sucesso!")
        else:
            logger.info("Coluna 'cloud_cover' já existe no SQLite.")
            
    except Exception as e:
        logger.error(f"Erro ao migrar SQLite: {e}")
    finally:
        conn.close()

def migrate_postgres():
    logger.info("Verificando necessidade de migração no PostgreSQL...")
    conn = get_postgres_connection()
    if not conn:
        logger.warning("PostgreSQL não configurado ou inacessível. Pulando migração Postgres.")
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='clima_historico' AND column_name='cloud_cover'
        """)
        exists = cursor.fetchone()
        
        if not exists:
            logger.info("Adicionando coluna 'cloud_cover' à tabela 'clima_historico' no PostgreSQL...")
            cursor.execute("ALTER TABLE clima_historico ADD COLUMN cloud_cover REAL")
            conn.commit()
            logger.info("✅ PostgreSQL atualizado com sucesso!")
        else:
            logger.info("Coluna 'cloud_cover' já existe no PostgreSQL.")
            
    except Exception as e:
        logger.error(f"Erro ao migrar PostgreSQL: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_sqlite()
    migrate_postgres()
