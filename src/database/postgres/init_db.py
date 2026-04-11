import os
import sys
import asyncio
import asyncpg
from dotenv import load_dotenv

# Adicionar a raiz do projeto ao sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.append(project_root)

# Carrega variáveis de ambiente
load_dotenv()

PG_HOST = os.environ.get("PG_HOST")
PG_DBNAME = os.environ.get("PG_DBNAME")
PG_USER = os.environ.get("PG_USER")
PG_PASSWORD = os.environ.get("PG_PASSWORD")
PG_PORT = os.environ.get("PG_PORT", 5432)

PG_DSN = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DBNAME}"

async def init_postgres():
    """Cria as tabelas iniciais no PostgreSQL."""
    print(f"--- Iniciando configuração do PostgreSQL em '{PG_HOST}' ---")
    
    if not all([PG_HOST, PG_DBNAME, PG_USER, PG_PASSWORD]):
        print("❌ Erro: Configurações do PostgreSQL incompletas no .env")
        return

    try:
        conn = await asyncpg.connect(dsn=PG_DSN)
        
        # 1. Tabela de Leituras (Histórico de monitoramento)
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

        # 2. Tabela de Lotes
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS lotes (
                lote SERIAL PRIMARY KEY,
                tanque TEXT NOT NULL,
                data_inicio DATE NOT NULL,
                data_abate DATE,
                descricao TEXT
            );
        ''')

        # 3. Tabela de Biometria
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS biometria (
                id SERIAL PRIMARY KEY,
                tanque TEXT NOT NULL,
                lote INTEGER NOT NULL,
                data_biometria DATE NOT NULL,
                volume_peixes INTEGER,
                peso_medio_g REAL,
                consumo_racao_kg REAL
            );
        ''')

        # 4. Tabela de Qualidade da Água (Lançamentos manuais)
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

        await conn.close()
        print("✅ Tabelas do PostgreSQL criadas com sucesso!")

    except Exception as e:
        print(f"❌ Erro ao inicializar o PostgreSQL: {e}")

if __name__ == "__main__":
    asyncio.run(init_postgres())
