#!/usr/bin/env python3
"""
Acesso ao PostgreSQL com asyncpg para o bot de biometria.
Schema atualizado: C.VALE / PATEL
"""
import os
import asyncpg
from datetime import date
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
            raise ConnectionError("Configurações do PostgreSQL incompletas no .env")
        _pool = await asyncpg.create_pool(dsn=PG_DSN, min_size=1, max_size=5)
    return _pool

async def get_tanques_ativos() -> list[str]:
    """Busca tanques com lotes em aberto."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT DISTINCT e.nome FROM lotes l JOIN estruturas e ON l.estrutura_uid = e.uid WHERE l.data_abate IS NULL ORDER BY e.nome"
        )
    return [r["nome"] for r in rows]

async def get_todos_tanques() -> list[str]:
    """Lista física de tanques configurados."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT nome FROM estruturas WHERE tipo_exploracao_id = 1 ORDER BY nome"
        )
    return [r["nome"] for r in rows]

async def get_lote_por_tanque(tanque: str) -> str | None:
    """Busca a string de identificação do lote ativo."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT l.lote FROM lotes l
               JOIN estruturas e ON l.estrutura_uid = e.uid
               WHERE e.nome = $1 AND l.data_abate IS NULL LIMIT 1""",
            tanque
        )
    return row["lote"] if row else None

async def criar_lote_completo(dados: dict) -> str:
    """Insere o alojamento conforme Ficha Verde."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Busca UID da estrutura pelo nome
        struct_uid = await conn.fetchval("SELECT uid FROM estruturas WHERE nome = $1", dados['tanque'])

        # Verifica duplicidade
        existe = await conn.fetchval(
            "SELECT lote FROM lotes WHERE estrutura_uid = $1 AND data_abate IS NULL",
            struct_uid
        )
        if existe:
            raise Exception(f"Já existe o Lote {existe} aberto para este tanque.")

        await conn.execute(
            """
            INSERT INTO lotes (
                estrutura_uid, lote, data_alojamento, peixes_alojados,
                peso_medio, area_acude, densidade, descricao
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            struct_uid, dados['lote'], dados['data_alojamento'],
            dados['peixes_alojados'], dados['peso_medio'],
            dados['area_acude'], dados['densidade'], dados.get('descricao')
        )
    return dados['lote']

async def finalizar_lote_abate(dados: dict) -> bool:
    """Atualiza dados de abate e fecha o lote."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        struct_uid = await conn.fetchval("SELECT uid FROM estruturas WHERE nome = $1", dados['tanque'])
        result = await conn.execute(
            """
            UPDATE lotes 
            SET data_abate = $1, qtd_peixes_entregues = $2,
                peso_entregue = $3, pct_rend_file = $4, reais_por_peixe = $5
            WHERE estrutura_uid = $6 AND data_abate IS NULL
            """,
            dados['data_abate'], dados['qtd_peixes_entregues'],
            dados['peso_entregue'], dados['pct_rend_file'],
            dados['reais_por_peixe'], struct_uid
        )
    return result == "UPDATE 1"

async def inserir_biometria(
    tanque: str,
    data_biometria: date,
    volume_peixes: int,
    peso_medio_g: float,
    consumo_racao_kg: float,
    lote: str,
) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        struct_uid = await conn.fetchval("SELECT uid FROM estruturas WHERE nome = $1", tanque)
        await conn.execute(
            """
            INSERT INTO biometria
                (estrutura_uid, data_biometria, volume_peixes,
                 peso_medio_g, consumo_racao_kg, lote)
            VALUES ($1, $2, $3, $4, $5, $6);
            """,
            struct_uid, data_biometria, volume_peixes,
            peso_medio_g, consumo_racao_kg, lote
        )
