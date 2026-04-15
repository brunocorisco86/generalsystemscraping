import os
import logging
import sys

# Adicionar o caminho do projeto ao sys.path para permitir importações do src
# Agora que o script está em src/database/postgres/, subimos 3 níveis.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.services.database import get_sqlite_connection, get_postgres_connection  # noqa: E402
from src.services.notification import send_telegram_message  # noqa: E402

SQLITE_TABELA_ORIGEM = 'leituras' 

# Configuração do logger
logger = logging.getLogger(__name__)

def migrate_data():
    """
    Migra dados incrementais da base SQLite para a base PostgreSQL.
    Busca o último ID migrado no PostgreSQL e copia todos os registros
    mais recentes do SQLite.
    """
    pg_conn = None
    sq_conn = None
    status_msg = ""
    
    try:
        logger.info("Iniciando migração de dados...")
        
        # Conectar aos bancos de dados usando o serviço
        pg_conn = get_postgres_connection()
        sq_conn = get_sqlite_connection()

        if not pg_conn or not sq_conn:
            raise Exception("Falha ao conectar a um dos bancos de dados.")

        pg_cur = pg_conn.cursor()
        sq_cur = sq_conn.cursor()

        # 1. Verifica último ID no PostgreSQL
        pg_cur.execute("SELECT MAX(id) FROM leituras")
        ultimo_id = pg_cur.fetchone()[0] or 0
        logger.info("Último ID no PostgreSQL: %d", ultimo_id)

        # 2. Busca novos dados no SQLite
        query_sq = f"""
            SELECT id, estrutura_uid, nome_estrutura, oxigenio, temperatura, timestamp_site, data_coleta, aeradores_ativos 
            FROM {SQLITE_TABELA_ORIGEM} 
            WHERE id > ?
        """
        sq_cur.execute(query_sq, (ultimo_id,))
        novos_dados = sq_cur.fetchall()

        if novos_dados:
            # 3. Insere no Postgres
            logger.info("Encontrados %d novos registros para migrar.", len(novos_dados))
            insert_query = """
                INSERT INTO leituras (id, estrutura_uid, nome_estrutura, oxigenio, temperatura, timestamp_site, data_coleta, aeradores_ativos) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            pg_cur.executemany(insert_query, novos_dados)
            pg_conn.commit()
            status_msg = f"Sucesso! {len(novos_dados)} novos registros migrados."
        else:
            status_msg = "Migração concluída: Nenhum dado novo encontrado no SQLite."

    except Exception as e:
        status_msg = f"Erro na migração de dados: {str(e)}"
        if pg_conn:
            pg_conn.rollback()
    
    finally:
        if pg_conn:
            pg_conn.close()
        if sq_conn:
            sq_conn.close()
        
        if "Erro" in status_msg:
            logger.error(status_msg)
        else:
            logger.info(status_msg)

        send_telegram_message(status_msg)

if __name__ == "__main__":
    from dotenv import load_dotenv
    # Carrega .env do root
    load_dotenv(os.path.join(project_root, '.env'))
    # Configuração básica de logging para execução direta
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    migrate_data()
