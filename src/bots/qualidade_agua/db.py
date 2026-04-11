#!/usr/bin/env python3
"""
Acesso ao PostgreSQL com asyncpg para o bot de qualidade de água.
"""
import os
import asyncpg
from datetime import date, time
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

PG_HOST = os.environ.get("PG_HOST")
PG_DBNAME = os.environ.get("PG_DBNAME")
PG_USER = os.environ.get("PG_USER")
PG_PASSWORD = os.environ.get("PG_PASSWORD")
PG_PORT = os.environ.get("PG_PORT", 5432)

PG_DSN = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DBNAME}"

_pool: asyncpg.Pool | None = None

async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        if not all([PG_DBNAME, PG_USER, PG_PASSWORD]):
            raise ConnectionError("Configurações do banco de dados PostgreSQL estão incompletas no .env")
        _pool = await asyncpg.create_pool(dsn=PG_DSN, min_size=1, max_size=5)
    return _pool

async def get_tanques_ativos() -> list[str]:
    """Busca tanques que possuem lotes abertos."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT DISTINCT tanque FROM lotes WHERE data_abate IS NULL ORDER BY tanque"
        )
    return [r["tanque"] for r in rows]

async def get_lote_por_tanque(tanque: str) -> str | None:
    """Busca o identificador do lote ativo (VARCHAR)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT lote FROM lotes WHERE tanque = $1 AND data_abate IS NULL LIMIT 1",
            tanque
        )
    return row["lote"] if row else None

async def inserir_qualidade_agua(dados: dict) -> None:
    """Insere registro de qualidade da água."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO qualidade_agua
              (id_tanque, id_lote, data_coleta, hora_coleta,
               ph, amonia, nitrito, anotacao_manejo)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8);
            """,
            dados['tanque'], dados['lote'], dados['data_coleta'], dados['hora_coleta'],
            dados.get('ph'), dados.get('amonia'), dados.get('nitrito'), dados.get('anotacao')
        )
