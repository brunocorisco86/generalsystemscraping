import pytest
import os
import concurrent.futures
from datetime import datetime, date
import psycopg2
from psycopg2 import pool
from dotenv import dotenv_values

# Obter credenciais do Postgres real diretamente do .env sem poluir os.environ
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
prod_env = dotenv_values(os.path.join(project_root, ".env"))

PG_HOST = prod_env.get("PG_HOST") or os.getenv("PG_HOST", "192.168.1.7")
PG_PORT = int(prod_env.get("PG_PORT") or os.getenv("PG_PORT", 5432))
PG_DBNAME = prod_env.get("PG_DBNAME") or os.getenv("PG_DBNAME", "piscicultura_history")
PG_USER = prod_env.get("PG_USER") or os.getenv("PG_USER", "brunoconter")
PG_PASSWORD = prod_env.get("PG_PASSWORD") or os.getenv("PG_PASSWORD", "blurbang")




@pytest.fixture(scope="module")
def pg_pool():
    """Pool de conexões thread-safe para testes de concorrência."""
    try:
        connection_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=30,
            host=PG_HOST,
            port=PG_PORT,
            dbname=PG_DBNAME,
            user=PG_USER,
            password=PG_PASSWORD,
            connect_timeout=5
        )
        yield connection_pool
        connection_pool.closeall()
    except Exception as e:
        pytest.skip(f"PostgreSQL não acessível em {PG_HOST}:{PG_PORT} ({e}). Pulando testes de concorrência.")


@pytest.fixture(scope="module")
def setup_test_structure_and_batch(pg_pool):
    """Cria uma estrutura e um lote temporários dedicados para os testes de estresse."""
    conn = pg_pool.getconn()
    cur = conn.cursor()
    
    test_struct_uid = "test_struct_concurrency_stress_01"
    test_lote_cod = "LOTE_TEST_CONC_99"

    # Garantir estrutura de teste
    cur.execute("""
        INSERT INTO estruturas (uid, nome, pluscode)
        VALUES (%s, %s, %s)
        ON CONFLICT (uid) DO UPDATE SET nome = EXCLUDED.nome;
    """, (test_struct_uid, "Tanque Stress Concurrency", "TEST+CODE"))

    # Garantir lote de teste ativo
    cur.execute("""
        INSERT INTO lotes (estrutura_uid, lote, data_alojamento, peixes_alojados, peso_medio)
        VALUES (%s, %s, CURRENT_DATE, 10000, 40.0)
        ON CONFLICT DO NOTHING;
    """, (test_struct_uid, test_lote_cod))


    conn.commit()
    pg_pool.putconn(conn)

    yield test_struct_uid, test_lote_cod

    # Limpeza pós-teste
    clean_conn = pg_pool.getconn()
    clean_cur = clean_conn.cursor()
    clean_cur.execute("DELETE FROM biometria WHERE lote = %s;", (test_lote_cod,))
    clean_cur.execute("DELETE FROM lotes WHERE lote = %s;", (test_lote_cod,))
    clean_cur.execute("DELETE FROM estruturas WHERE uid = %s;", (test_struct_uid,))
    clean_conn.commit()
    pg_pool.putconn(clean_conn)


class TestPostgresConcurrency:
    """Suíte de Testes de Concorrência, Leitura e Escrita sob Carga no PostgreSQL."""

    def test_concurrent_reads(self, pg_pool, setup_test_structure_and_batch):
        """Valida que múltiplas threads simultâneas realizam leituras sem contenção ou erros."""
        num_threads = 20

        def worker_read(thread_id):
            conn = pg_pool.getconn()
            try:
                cur = conn.cursor()
                cur.execute("SELECT id, lote, peixes_alojados FROM lotes LIMIT 10;")
                rows = cur.fetchall()
                cur.execute("SELECT COUNT(*) FROM estruturas;")
                count_est = cur.fetchone()[0]
                cur.close()
                return len(rows) >= 0 and count_est >= 1
            finally:
                pg_pool.putconn(conn)

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker_read, i) for i in range(num_threads)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert len(results) == num_threads
        assert all(results) is True

    def test_concurrent_writes_biometria(self, pg_pool, setup_test_structure_and_batch):
        """Valida inserções concorrentes de biometria e mortalidade para o mesmo lote sob isolamento ACID."""
        test_struct_uid, test_lote_cod = setup_test_structure_and_batch
        num_writers = 15
        mortos_por_thread = 2
        racao_por_thread = 10.5

        def worker_write(thread_id):
            conn = pg_pool.getconn()
            try:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO biometria (
                        estrutura_uid, lote, data_biometria, quantidade, peso_medio, mortalidade, consumo_racao
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """, (
                    test_struct_uid, test_lote_cod, date.today(),
                    50, 45.0 + thread_id, mortos_por_thread, racao_por_thread
                ))
                novo_id = cur.fetchone()[0]
                conn.commit()
                cur.close()
                return novo_id
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                pg_pool.putconn(conn)

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_writers) as executor:
            futures = [executor.submit(worker_write, i) for i in range(num_writers)]
            inserted_ids = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert len(inserted_ids) == num_writers

        # Verificar integridade e consistência da agregação
        verify_conn = pg_pool.getconn()
        verify_cur = verify_conn.cursor()
        verify_cur.execute("""
            SELECT SUM(mortalidade), SUM(consumo_racao), COUNT(*)
            FROM biometria
            WHERE lote = %s;
        """, (test_lote_cod,))
        total_mort, total_racao, total_linhas = verify_cur.fetchone()
        verify_conn.commit()
        pg_pool.putconn(verify_conn)

        assert total_linhas == num_writers
        assert total_mort == (num_writers * mortos_por_thread)
        assert abs(float(total_racao) - (num_writers * racao_por_thread)) < 0.01

    def test_concurrent_batch_state_atomic_closure(self, pg_pool, setup_test_structure_and_batch):
        """Testa tentativa de fechamento concorrente garantindo atomicidade sem deadlocks."""
        test_struct_uid, test_lote_cod = setup_test_structure_and_batch

        # Criar lote específico para despesca concorrente
        setup_conn = pg_pool.getconn()
        setup_cur = setup_conn.cursor()
        setup_cur.execute("""
            INSERT INTO lotes (estrutura_uid, lote, data_alojamento, peixes_alojados)
            VALUES (%s, 'LOTE_CONCURRENT_CLOSE', CURRENT_DATE, 5000)
            RETURNING id;
        """, (test_struct_uid,))
        target_lote_id = setup_cur.fetchone()[0]
        setup_conn.commit()
        pg_pool.putconn(setup_conn)

        num_threads = 5

        def worker_close(thread_id):
            conn = pg_pool.getconn()
            try:
                cur = conn.cursor()
                cur.execute("""
                    UPDATE lotes
                    SET data_abate = %s,
                        qtd_peixes_entregues = 4800,
                        peso_entregue = 4200.0
                    WHERE id = %s AND data_abate IS NULL;
                """, (date.today(), target_lote_id))
                rows_updated = cur.rowcount
                conn.commit()
                cur.close()
                return rows_updated
            finally:
                pg_pool.putconn(conn)

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker_close, i) for i in range(num_threads)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # Exatamente uma thread deve ter fechado o lote (atomicidade), as demais não afetam nada
        assert sum(results) == 1

        # Limpeza do lote específico
        clean_conn = pg_pool.getconn()
        clean_cur = clean_conn.cursor()
        clean_cur.execute("DELETE FROM lotes WHERE id = %s;", (target_lote_id,))
        clean_conn.commit()
        pg_pool.putconn(clean_conn)
