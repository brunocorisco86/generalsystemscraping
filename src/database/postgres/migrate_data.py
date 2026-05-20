import os
import sys
import logging
import psycopg2
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

# Adicionar a raiz do projeto ao sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

from src.services.database import get_sqlite_connection, get_postgres_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_data():
    """Migra dados do SQLite para o PostgreSQL."""
    sq_conn = get_sqlite_connection()
    pg_conn = get_postgres_connection()

    if not sq_conn or not pg_conn:
        logger.error("Falha ao conectar aos bancos de dados.")
        return

    try:
        sq_cur = sq_conn.cursor()
        pg_cur = pg_conn.cursor()

        status_msg = ""

        # --- MIGRAÇÃO DE LEITURAS ---
        pg_cur.execute("SELECT MAX(id) FROM leituras")
        ultimo_id = pg_cur.fetchone()[0] or 0
        logger.info("Último ID de leituras no PostgreSQL: %d", ultimo_id)

        sq_cur.execute("SELECT id, estrutura_uid, nome_estrutura, oxigenio, temperatura, timestamp_site, data_coleta, aeradores_ativos FROM leituras WHERE id > ?", (ultimo_id,))
        novas_leituras = sq_cur.fetchall()

        if novas_leituras:
            logger.info("Encontrados %d novas leituras para migrar.", len(novas_leituras))
            insert_query = """
                INSERT INTO leituras (id, estrutura_uid, nome_estrutura, oxigenio, temperatura, timestamp_site, data_coleta, aeradores_ativos)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            pg_cur.executemany(insert_query, novas_leituras)
            pg_conn.commit()
            status_msg += f" {len(novas_leituras)} leituras migradas."

        # --- MIGRAÇÃO DE CLIMA_HISTORICO ---
        pg_cur.execute("SELECT MAX(id) FROM clima_historico")
        ultimo_id_clima = pg_cur.fetchone()[0] or 0
        logger.info("Último ID de clima no PostgreSQL: %d", ultimo_id_clima)

        sq_cur.execute("SELECT id, data_coleta, temperatura, umidade, pressao, cloud_cover FROM clima_historico WHERE id > ?", (ultimo_id_clima,))
        novos_climas = sq_cur.fetchall()

        if novos_climas:
            logger.info("Encontrados %d novos registros de clima para migrar.", len(novos_climas))
            insert_clima = """
                INSERT INTO clima_historico (id, data_coleta, temperatura, umidade, pressao, cloud_cover)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            pg_cur.executemany(insert_clima, novos_climas)
            pg_conn.commit()
            status_msg += f" {len(novos_climas)} registros de clima migrados."

        if not novas_leituras and not novos_climas:
            status_msg = "Migração concluída: Nenhum dado novo encontrado."
        else:
            status_msg = "Sucesso!" + status_msg
        
        logger.info(status_msg)

    except Exception as e:
        logger.error(f"Erro na migração de dados: {str(e)}")
        if pg_conn:
            pg_conn.rollback()
    finally:
        if sq_conn: sq_conn.close()
        if pg_conn: pg_conn.close()

if __name__ == "__main__":
    migrate_data()
