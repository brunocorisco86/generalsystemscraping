#!/usr/bin/env python3
"""
Acesso ao PostgreSQL com asyncpg para o bot unificado.
Centraliza biometria, qualidade de água e gestão de lotes.
"""
import os
import asyncpg
from datetime import date
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Prioriza PG_HOST do ambiente (Docker) ou do .env
PG_HOST = os.environ.get("PG_HOST", os.environ.get("PG_HOST_LOCAL", "localhost"))
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

async def get_estruturas_ativas() -> list[dict]:
    """Busca estruturas com lotes em aberto, incluindo tipo de exploração."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT DISTINCT e.uid, e.nome, e.tipo_exploracao_id, p.nome as propriedade
               FROM lotes l
               JOIN estruturas e ON l.estrutura_uid = e.uid
               JOIN propriedades p ON e.propriedade_uid = p.uid
               WHERE l.data_abate IS NULL ORDER BY e.nome"""
        )
    return [dict(r) for r in rows]

async def get_todas_estruturas() -> list[dict]:
    """Lista todas as estruturas configuradas."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT e.uid, e.nome, e.tipo_exploracao_id, p.nome as propriedade
               FROM estruturas e
               JOIN propriedades p ON e.propriedade_uid = p.uid
               ORDER BY e.nome"""
        )
    return [dict(r) for r in rows]

async def get_lote_por_estrutura(estrutura_uid: str) -> str | None:
    """Busca a string de identificação do lote ativo."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT lote FROM lotes WHERE estrutura_uid = $1 AND data_abate IS NULL LIMIT 1",
            estrutura_uid
        )
    return row["lote"] if row else None

# --- BIOMETRIA ---

async def criar_lote_completo(dados: dict) -> str:
    """Insere o alojamento."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Verifica duplicidade
        existe = await conn.fetchval(
            "SELECT lote FROM lotes WHERE estrutura_uid = $1 AND data_abate IS NULL",
            dados['estrutura_uid']
        )
        if existe:
            raise Exception(f"Já existe o Lote {existe} aberto para esta estrutura.")

        await conn.execute(
            """
            INSERT INTO lotes (
                estrutura_uid, lote, data_alojamento, peixes_alojados,
                peso_medio, area_acude, densidade, descricao
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            dados['estrutura_uid'], dados['lote'], dados['data_alojamento'],
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
            WHERE estrutura_uid = $6 AND data_abate IS NULL
            """,
            dados['data_abate'], dados['qtd_peixes_entregues'],
            dados['peso_entregue'], dados['pct_rend_file'],
            dados['reais_por_peixe'], dados['estrutura_uid']
        )
    return result == "UPDATE 1"

async def inserir_biometria(
    estrutura_uid: str,
    data_biometria: date,
    quantidade: int,
    peso_medio: float,
    mortalidade: int,
    consumo_racao: float,
    lote: str,
) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO biometria
                (estrutura_uid, data_biometria, quantidade,
                 peso_medio, mortalidade, consumo_racao, lote)
            VALUES ($1, $2, $3, $4, $5, $6, $7);
            """,
            estrutura_uid, data_biometria, quantidade,
            peso_medio, mortalidade, consumo_racao, lote
        )

async def get_ultimo_estoque(estrutura_uid: str, lote: str) -> int:
    """Busca o último estoque registrado para cálculo de mortalidade."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Tenta pegar da última biometria
        ultimo_bio = await conn.fetchval(
            "SELECT quantidade FROM biometria WHERE estrutura_uid = $1 AND lote = $2 ORDER BY data_biometria DESC, id DESC LIMIT 1",
            estrutura_uid, lote
        )
        if ultimo_bio is not None:
            return ultimo_bio
        
        # Se não houver biometria, pega do alojamento inicial no lote
        alojamento = await conn.fetchval(
            "SELECT peixes_alojados FROM lotes WHERE estrutura_uid = $1 AND lote = $2",
            estrutura_uid, lote
        )
        return alojamento or 0

# --- QUALIDADE DA ÁGUA ---

async def inserir_qualidade_limnologia(dados: dict):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO qualidade_agua_limnologia (
                estrutura_uid, data_coleta, hora_coleta, ph, amonia, nitrito, alcalinidade, transparencia
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            dados['estrutura_uid'], dados['data_coleta'], dados['hora_coleta'],
            dados['ph'], dados['amonia'], dados['nitrito'], dados['alcalinidade'], dados['transparencia']
        )

async def inserir_qualidade_consumo(dados: dict):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO qualidade_agua_consumo (
                estrutura_uid, data_coleta, hora_coleta, ph, sdt, orp, ppm_cloro
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            dados['estrutura_uid'], dados['data_coleta'], dados['hora_coleta'],
            dados['ph'], dados['sdt'], dados['orp'], dados['ppm_cloro']
        )
