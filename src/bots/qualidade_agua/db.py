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

async def get_todos_tanques() -> list[str]:
    """Lista física de tanques configurados."""
    return ["Tanque 1", "Tanque 2"]

async def criar_lote_completo(dados: dict) -> str:
    """Insere o alojamento conforme Ficha Verde."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Verifica duplicidade
        existe = await conn.fetchval(
            "SELECT lote FROM lotes WHERE tanque = $1 AND data_abate IS NULL",
            dados['tanque']
        )
        if existe:
            raise Exception(f"Já existe o Lote {existe} aberto para este tanque.")

        await conn.execute(
            """
            INSERT INTO lotes (
                tanque, lote, data_alojamento, peixes_alojados, 
                peso_medio, area_acude, densidade, descricao
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            dados['tanque'], dados['lote'], dados['data_alojamento'],
            dados['peixes_alojados'], dados['peso_medio'],
            dados['area_acude'], dados['densidade'], dados.get('descricao')
        )
    return dados['lote']

async def finalizar_lote_abate(dados: dict) -> bool:
    """Atualiza dados de abate e fecha o lote."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE lotes 
            SET data_abate = $1, qtd_peixes_entregues = $2,
                peso_entregue = $3, pct_rend_file = $4, reais_por_peixe = $5
            WHERE tanque = $6 AND data_abate IS NULL
            """,
            dados['data_abate'], dados['qtd_peixes_entregues'],
            dados['peso_entregue'], dados['pct_rend_file'],
            dados['reais_por_peixe'], dados['tanque']
        )
    return result == "UPDATE 1"

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
