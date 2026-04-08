#!/usr/bin/env python3
"""
Acesso ao PostgreSQL com asyncpg para o bot de qualidade de água.
"""
import os
import asyncpg
from datetime import date, time
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# --- Configurações do Banco de Dados a partir do .env ---
PG_HOST = os.environ.get("PG_HOST")
PG_DBNAME = os.environ.get("PG_DBNAME")
PG_USER = os.environ.get("PG_USER")
PG_PASSWORD = os.environ.get("PG_PASSWORD")
PG_PORT = os.environ.get("PG_PORT", 5432)

# Constrói a DSN a partir das variáveis de ambiente
# Nota: 'host.docker.internal' é um bom fallback para containers Docker
# que precisam acessar a máquina host. Usaremos o PG_HOST do .env como prioridade.
if not PG_HOST:
    PG_HOST = "host.docker.internal"

PG_DSN = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DBNAME}"

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """Cria (uma vez) e retorna o pool de conexões asyncpg."""
    global _pool
    if _pool is None:
        if not all([PG_DBNAME, PG_USER, PG_PASSWORD]):
            raise ConnectionError("Configurações do banco de dados PostgreSQL estão incompletas no .env")
        _pool = await asyncpg.create_pool(dsn=PG_DSN, min_size=1, max_size=5)
    return _pool


async def get_tanques_ativos() -> list[str]:
    """
    Busca no banco de dados os tanques que possuem lotes ativos (sem data de abate).
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT DISTINCT tanque
            FROM lotes
            WHERE data_abate IS NULL
            ORDER BY tanque;
            """
        )
    return [r["tanque"] for r in rows]


async def get_lote_por_tanque(tanque: str) -> str | None:
    """
    Busca o número do lote ativo para um determinado tanque.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT lote
            FROM lotes
            WHERE tanque = $1 AND data_abate IS NULL
            LIMIT 1;
            """,
            tanque,
        )
    return row["lote"] if row else None


async def inserir_qualidade_agua(
    id_tanque: str,
    id_lote: int | None,
    data_coleta: date,
    hora_coleta: time,
    ph: float | None,
    amonia: float | None,
    nitrito: float | None,
    anotacao_manejo: str | None,
) -> None:
    """
    Insere um novo registro de qualidade da água na tabela correspondente.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO public.qualidade_agua
              (id_tanque, id_lote, data_coleta, hora_coleta,
               ph, amonia, nitrito, anotacao_manejo)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8);
            """,
            id_tanque,
            id_lote,
            data_coleta,
            hora_coleta,
            ph,
            amonia,
            nitrito,
            anotacao_manejo,
        )

