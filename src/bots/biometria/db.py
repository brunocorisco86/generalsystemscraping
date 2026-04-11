#!/usr/bin/env python3
"""
Acesso ao PostgreSQL com asyncpg para o bot de biometria.
"""
import os
import asyncpg
from datetime import date
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
PG_DSN = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DBNAME}"

_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """Cria (uma vez) e retorna o pool de conexões asyncpg."""
    global _pool
    if _pool is None:
        if not all([PG_HOST, PG_DBNAME, PG_USER, PG_PASSWORD]):
            raise ConnectionError("Configurações do banco de dados PostgreSQL estão incompletas no .env")
        _pool = await asyncpg.create_pool(dsn=PG_DSN, min_size=1, max_size=5)
    return _pool


async def get_tanques_ativos() -> list[str]:
    """Busca no banco de dados os tanques que possuem lotes ativos."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT DISTINCT tanque FROM lotes
            WHERE data_abate IS NULL
            ORDER BY tanque;
            """
        )
    return [r["tanque"] for r in rows]


async def get_todos_tanques() -> list[str]:
    """
    Retorna uma lista fixa dos tanques do sistema ou busca do banco.
    Como os tanques são físicos, usaremos uma lista padrão ou buscaremos as strings únicas.
    """
    # Você pode expandir esta lista conforme sua necessidade
    return ["Tanque 1", "Tanque 2"]


async def criar_lote(tanque: str, data_inicio: date, descricao: str = None) -> int:
    """Cria um novo lote para um tanque."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        lote_id = await conn.fetchval(
            """
            INSERT INTO lotes (tanque, data_inicio, descricao)
            VALUES ($1, $2, $3)
            RETURNING lote;
            """,
            tanque,
            data_inicio,
            descricao,
        )
    return lote_id


async def fechar_lote(tanque: str, data_abate: date) -> bool:
    """Fecha o lote ativo de um tanque setando a data de abate."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE lotes
            SET data_abate = $1
            WHERE tanque = $2 AND data_abate IS NULL;
            """,
            data_abate,
            tanque,
        )
    # Retorna True se algum registro foi atualizado
    return result == "UPDATE 1"


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


async def inserir_biometria(
    tanque: str,
    data_biometria: date,
    volume_peixes: int,
    peso_medio_g: float,
    consumo_racao_kg: float,
    lote: int,
) -> None:
    """
    Insere um novo registro de biometria na tabela correspondente.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO biometria
                (tanque, data_biometria, volume_peixes,
                 peso_medio_g, consumo_racao_kg, lote)
            VALUES ($1, $2, $3, $4, $5, $6);
            """,
            tanque,
            data_biometria,
            volume_peixes,
            peso_medio_g,
            consumo_racao_kg,
            lote,
        )

