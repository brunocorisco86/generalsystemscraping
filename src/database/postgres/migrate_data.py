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

def migrate_data(silent=False):
    """Migra dados do SQLite para o PostgreSQL."""
    if silent:
        # Se for silencioso, podemos ajustar o nível de log localmente se necessário
        # ou apenas aceitar o parâmetro para compatibilidade.
        pass
        
    sq_conn = get_sqlite_connection()
    pg_conn = get_postgres_connection()

    if not sq_conn or not pg_conn:
        logger.error("Falha ao conectar aos bancos de dados.")
        return

    try:
        sq_cur = sq_conn.cursor()
        pg_cur = pg_conn.cursor()

        status_msg = ""

        # --- CONTROLE DE MIGRAÇÃO (Tabela de Controle) ---
        pg_cur.execute("""
            CREATE TABLE IF NOT EXISTS controle_migracao (
                chave VARCHAR(50) PRIMARY KEY,
                valor_int INTEGER
            )
        """)
        pg_conn.commit()

        # --- MIGRAÇÃO DE LEITURAS ---
        pg_cur.execute("SELECT valor_int FROM controle_migracao WHERE chave = 'ultimo_id_leituras'")
        row = pg_cur.fetchone()
        if row is not None:
            ultimo_id = row[0]
        else:
            pg_cur.execute("SELECT MAX(id) FROM leituras")
            ultimo_id = pg_cur.fetchone()[0] or 0
        
        logger.info("Último ID de leituras processado no SQLite: %d", ultimo_id)

        # Buscar UIDs das estruturas que têm lotes ativos no PostgreSQL
        pg_cur.execute("SELECT estrutura_uid FROM lotes WHERE data_abate IS NULL")
        estruturas_ativas = {r[0] for r in pg_cur.fetchall()}

        # Buscar novas leituras no SQLite
        sq_cur.execute("SELECT id, estrutura_uid, nome_estrutura, oxigenio, temperatura, timestamp_site, data_coleta, aeradores_ativos FROM leituras WHERE id > ?", (ultimo_id,))
        novas_leituras_sqlite = sq_cur.fetchall()

        if novas_leituras_sqlite:
            max_sqlite_id = max(r[0] for r in novas_leituras_sqlite)
            
            # Filtrar leituras mantendo apenas as que pertencem a estruturas ativas
            leituras_filtradas = [
                r for r in novas_leituras_sqlite if r[1] in estruturas_ativas
            ]

            if leituras_filtradas:
                logger.info("Encontradas %d novas leituras para migrar (de %d totais no SQLite).", len(leituras_filtradas), len(novas_leituras_sqlite))
                insert_query = """
                    INSERT INTO leituras (id, estrutura_uid, nome_estrutura, oxigenio, temperatura, timestamp_site, data_coleta, aeradores_ativos)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                pg_cur.executemany(insert_query, leituras_filtradas)
                status_msg += f" {len(leituras_filtradas)} leituras migradas."
            else:
                logger.info("Nenhuma leitura nova de lote ativo encontrada entre as %d novas do SQLite.", len(novas_leituras_sqlite))
                status_msg += " Nenhuma leitura nova de lote ativo."

            # Atualiza a tabela de controle com o maior ID lido do SQLite
            pg_cur.execute("""
                INSERT INTO controle_migracao (chave, valor_int)
                VALUES ('ultimo_id_leituras', %s)
                ON CONFLICT (chave) DO UPDATE SET valor_int = EXCLUDED.valor_int
            """, (max_sqlite_id,))
            
            pg_conn.commit()
        else:
            # Garante que novas_leituras seja definido para as verificações posteriores
            leituras_filtradas = []

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

        if not novas_leituras_sqlite and not novos_climas:
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
