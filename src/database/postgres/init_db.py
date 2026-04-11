import os
import sys
import asyncio
import asyncpg
import time
from dotenv import load_dotenv

# Adicionar a raiz do projeto ao sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.append(project_root)

# Carrega variáveis de ambiente
load_dotenv(os.path.join(project_root, ".env"))

PG_HOST = os.environ.get("PG_HOST")
PG_DBNAME = os.environ.get("PG_DBNAME")
PG_USER = os.environ.get("PG_USER")
PG_PASSWORD = os.environ.get("PG_PASSWORD")
PG_PORT = os.environ.get("PG_PORT", 5432)

PG_DSN = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DBNAME}"

async def init_postgres():
    """Cria as tabelas iniciais no PostgreSQL de forma resiliente."""
    print(f"--- Configurando Schema do PostgreSQL em '{PG_HOST}' ---")
    
    if not all([PG_HOST, PG_DBNAME, PG_USER, PG_PASSWORD]):
        print("❌ Erro: Configurações do PostgreSQL incompletas no .env")
        return

    conn = None
    max_retries = 5
    for i in range(max_retries):
        try:
            conn = await asyncpg.connect(dsn=PG_DSN)
            break
        except Exception as e:
            if i < max_retries - 1:
                print(f"⏳ Aguardando Postgres inicializar (tentativa {i+1}/{max_retries})...")
                await asyncio.sleep(5)
            else:
                print(f"❌ Não foi possível conectar ao Postgres após {max_retries} tentativas: {e}")
                return

    try:
        # 1. Tabela de Lotes (Schema C.VALE / PATEL)
        print("Criando/Sincronizando tabela 'lotes'...")
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS lotes (
                id SERIAL PRIMARY KEY,
                tanque VARCHAR(255) NOT NULL,
                lote VARCHAR(255) NOT NULL,
                data_alojamento DATE NOT NULL DEFAULT CURRENT_DATE,
                data_abate DATE,
                peixes_alojados INTEGER,
                peso_medio NUMERIC(10,2),
                area_acude NUMERIC(10,2),
                densidade NUMERIC(10,2),
                qtd_peixes_entregues INTEGER,
                peso_entregue NUMERIC(10,2),
                pct_rend_file NUMERIC(5,2),
                reais_por_peixe NUMERIC(10,2),
                descricao TEXT,
                CONSTRAINT uq_tanque_lote UNIQUE (tanque, lote)
            );
        ''')

        # Migração: Garante que todas as colunas novas existam e tipos estejam corretos
        print("Sincronizando colunas e tipos da tabela 'lotes'...")
        migracoes = [
            "ALTER TABLE lotes RENAME COLUMN data_inicio TO data_alojamento;",
            "ALTER TABLE lotes ALTER COLUMN lote TYPE VARCHAR(255);",
            "ALTER TABLE biometria ALTER COLUMN lote TYPE VARCHAR(255);",
            "ALTER TABLE lotes ADD COLUMN IF NOT EXISTS peixes_alojados INTEGER;",
            "ALTER TABLE lotes ADD COLUMN IF NOT EXISTS peso_medio NUMERIC(10,2);",
            "ALTER TABLE lotes ADD COLUMN IF NOT EXISTS area_acude NUMERIC(10,2);",
            "ALTER TABLE lotes ADD COLUMN IF NOT EXISTS densidade NUMERIC(10,2);",
            "ALTER TABLE lotes ADD COLUMN IF NOT EXISTS qtd_peixes_entregues INTEGER;",
            "ALTER TABLE lotes ADD COLUMN IF NOT EXISTS peso_entregue NUMERIC(10,2);",
            "ALTER TABLE lotes ADD COLUMN IF NOT EXISTS pct_rend_file NUMERIC(5,2);",
            "ALTER TABLE lotes ADD COLUMN IF NOT EXISTS reais_por_peixe NUMERIC(10,2);"
        ]

        for sql in migracoes:
            try:
                await conn.execute(sql)
            except Exception:
                pass # Ignora se a coluna já existir ou se o rename falhar (já renomeado)

        # 2. Tabela de Leituras
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS leituras (
                id INTEGER PRIMARY KEY,
                tanque TEXT,
                oxigenio REAL,
                temperatura REAL,
                timestamp_site TIMESTAMP,
                data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                aeradores_ativos INTEGER DEFAULT 0
            );
        ''')

        # 3. Tabela de Biometria
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS biometria (
                id SERIAL PRIMARY KEY,
                tanque TEXT NOT NULL,
                lote VARCHAR(255) NOT NULL,
                data_biometria DATE NOT NULL,
                volume_peixes INTEGER,
                peso_medio_g REAL,
                consumo_racao_kg REAL
            );
        ''')

        # 4. Tabela de Qualidade da Água
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS qualidade_agua (
                id SERIAL PRIMARY KEY,
                id_tanque TEXT NOT NULL,
                id_lote INTEGER,
                data_coleta DATE NOT NULL,
                hora_coleta TIME NOT NULL,
                ph REAL,
                amonia REAL,
                nitrito REAL,
                anotacao_manejo TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        await conn.execute('CREATE INDEX IF NOT EXISTS idx_leituras_tanque ON leituras(tanque);')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_biometria_lote ON biometria(lote);')

        await conn.close()
        print("✅ Schema do PostgreSQL validado/criado com sucesso!")

    except Exception as e:
        print(f"❌ Erro ao processar comandos SQL: {e}")
        if conn: await conn.close()

if __name__ == "__main__":
    asyncio.run(init_postgres())
