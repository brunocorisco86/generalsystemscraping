import os
import sys
import asyncio
import asyncpg
import logging
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

# Configuração do logger
logger = logging.getLogger(__name__)

async def init_postgres():
    """Cria as tabelas do novo MER no PostgreSQL."""
    logger.info("--- Configurando Schema do PostgreSQL em '%s' ---", PG_HOST)
    
    if not all([PG_HOST, PG_DBNAME, PG_USER, PG_PASSWORD]):
        logger.error("Configurações do PostgreSQL incompletas no .env")
        return

    conn = None
    max_retries = 5
    for i in range(max_retries):
        try:
            conn = await asyncpg.connect(dsn=PG_DSN)
            break
        except Exception as e:
            if i < max_retries - 1:
                logger.info("Aguardando Postgres inicializar (tentativa %d/%d)...", i+1, max_retries)
                await asyncio.sleep(5)
            else:
                logger.error("Não foi possível conectar ao Postgres após %d tentativas: %s", max_retries, e)
                return

    try:
        # 1. Tabelas de Cadastro (Base)
        logger.info("Criando tabelas de cadastro...")

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS proprietarios (
                uid VARCHAR(64) PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                cpf VARCHAR(20) NOT NULL
            );
        ''')

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS propriedades (
                uid VARCHAR(64) PRIMARY KEY,
                proprietario_uid VARCHAR(64) REFERENCES proprietarios(uid),
                nome VARCHAR(255) NOT NULL,
                endereco TEXT NOT NULL,
                cadpro VARCHAR(50) NOT NULL
            );
        ''')

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS tipos_exploracao (
                id INTEGER PRIMARY KEY,
                nome VARCHAR(100) NOT NULL
            );
        ''')

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS estruturas (
                uid VARCHAR(64) PRIMARY KEY,
                propriedade_uid VARCHAR(64) REFERENCES propriedades(uid),
                tipo_exploracao_id INTEGER REFERENCES tipos_exploracao(id),
                nome VARCHAR(255) NOT NULL,
                pluscode VARCHAR(50) NOT NULL
            );
        ''')

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS usuarios_telegram (
                telegram_id BIGINT PRIMARY KEY,
                proprietario_uid VARCHAR(64) REFERENCES proprietarios(uid),
                username VARCHAR(255),
                nome_completo VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # 2. Tabelas de Operação e Monitoramento
        logger.info("Criando tabelas de operação e monitoramento...")

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS lotes (
                id SERIAL PRIMARY KEY,
                estrutura_uid VARCHAR(64) REFERENCES estruturas(uid),
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
                descricao TEXT
            );
        ''')

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS leituras (
                id SERIAL PRIMARY KEY,
                estrutura_uid VARCHAR(64) REFERENCES estruturas(uid),
                nome_estrutura VARCHAR(255),
                oxigenio REAL,
                temperatura REAL,
                timestamp_site TIMESTAMP,
                data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                aeradores_ativos INTEGER DEFAULT 0
            );
        ''')

        # Migração Postgres: Tenta adicionar a coluna caso não exista
        try:
            await conn.execute("ALTER TABLE leituras ADD COLUMN IF NOT EXISTS nome_estrutura VARCHAR(255);")
        except:
            pass

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS biometria (
                id SERIAL PRIMARY KEY,
                estrutura_uid VARCHAR(64) REFERENCES estruturas(uid),
                lote VARCHAR(255) NOT NULL,
                data_biometria DATE NOT NULL,
                quantidade INTEGER,
                peso_medio REAL,
                mortalidade INTEGER DEFAULT 0,
                consumo_racao REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # 3. Tabelas de Qualidade da Água (Específicas)
        logger.info("Criando tabelas de qualidade da água...")

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS qualidade_agua_limnologia (
                id SERIAL PRIMARY KEY,
                estrutura_uid VARCHAR(64) REFERENCES estruturas(uid),
                data_coleta DATE NOT NULL,
                hora_coleta TIME NOT NULL,
                ph REAL,
                amonia REAL,
                nitrito REAL,
                alcalinidade REAL,
                transparencia REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        await conn.execute('''
            CREATE TABLE IF NOT EXISTS qualidade_agua_consumo (
                id SERIAL PRIMARY KEY,
                estrutura_uid VARCHAR(64) REFERENCES estruturas(uid),
                data_coleta DATE NOT NULL,
                hora_coleta TIME NOT NULL,
                ph REAL,
                sdt REAL,
                orp REAL,
                ppm_cloro REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # Índices para performance
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_leituras_estrutura ON leituras(estrutura_uid);')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_lotes_estrutura ON lotes(estrutura_uid);')

        # Popula catálogo de tipos de exploração
        tipos = [
            (1, 'Piscicultura'),
            (2, 'Avicultura'),
            (3, 'Suinocultura'),
            (4, 'Bovinocultura de Leite'),
            (5, 'Bovinocultura de Corte'),
            (6, 'Caprinocultura'),
            (7, 'Ovinocultura')
        ]

        for tid, nome in tipos:
            await conn.execute('''
                INSERT INTO tipos_exploracao (id, nome)
                VALUES ($1, $2)
                ON CONFLICT (id) DO UPDATE SET nome = EXCLUDED.nome;
            ''', tid, nome)

        await conn.close()
        logger.info("Schema do PostgreSQL (Novo MER) validado/criado com sucesso!")

    except Exception as e:
        logger.error("Erro ao processar comandos SQL: %s", e)
        if conn:
            await conn.close()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(init_postgres())
