import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import date
from src.bots.db import (
    verificar_lote_ativo,
    inserir_biometria,
    inserir_qualidade_limnologia,
    inserir_qualidade_consumo
)

@pytest.mark.asyncio
async def test_verificar_lote_ativo_com_lote_ativo():
    """Verifica que verificar_lote_ativo passa sem erro se houver lote ativo."""
    mock_conn = AsyncMock()
    # Simula COUNT(*) retornando 1 (lote ativo existente)
    mock_conn.fetchval.return_value = 1

    # Não deve levantar exceção
    await verificar_lote_ativo(mock_conn, "estrutura-ativa-123")
    mock_conn.fetchval.assert_called_once_with(
        "SELECT COUNT(*) FROM lotes WHERE estrutura_uid = $1 AND data_abate IS NULL",
        "estrutura-ativa-123"
    )

@pytest.mark.asyncio
async def test_verificar_lote_ativo_sem_lote_ativo():
    """Verifica que verificar_lote_ativo levanta ValueError se não houver lote ativo."""
    mock_conn = AsyncMock()
    # Simula COUNT(*) retornando 0 (nenhum lote ativo)
    mock_conn.fetchval.return_value = 0

    with pytest.raises(ValueError) as excinfo:
        await verificar_lote_ativo(mock_conn, "estrutura-inativa-123")
    
    assert "Operação bloqueada" in str(excinfo.value)

@pytest.mark.asyncio
async def test_inserir_biometria_lote_inativo():
    """Verifica se inserir_biometria levanta ValueError ao tentar salvar em lote inativo."""
    mock_conn = AsyncMock()
    mock_conn.fetchval.return_value = 0  # Lote inativo

    mock_pool = MagicMock()
    # Configura o gerenciador de contexto assíncrono para pool.acquire()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

    # Patch do get_pool para retornar nosso mock pool
    with patch("src.bots.db.get_pool", AsyncMock(return_value=mock_pool)):
        with pytest.raises(ValueError) as exc_info:
            await inserir_biometria(
                estrutura_uid="estrutura-inativa",
                data_biometria=date.today(),
                quantidade=1000,
                peso_medio=15.5,
                mortalidade=10,
                consumo_racao=50.0,
                lote="2026/01"
            )
        assert "Operação bloqueada" in str(exc_info.value)
        # O mock execute não deve ter sido chamado porque a validação bloqueou antes
        mock_conn.execute.assert_not_called()

@pytest.mark.asyncio
async def test_inserir_qualidade_limnologia_lote_inativo():
    """Verifica se inserir_qualidade_limnologia bloqueia se não houver lote ativo."""
    mock_conn = AsyncMock()
    mock_conn.fetchval.return_value = 0  # Lote inativo

    mock_pool = MagicMock()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

    dados_fake = {
        "estrutura_uid": "estrutura-inativa",
        "data_coleta": date.today(),
        "hora_coleta": "10:00",
        "ph": 7.0,
        "amonia": 0.1,
        "nitrito": 0.05,
        "alcalinidade": 120.0,
        "transparencia": 35.0
    }

    with patch("src.bots.db.get_pool", AsyncMock(return_value=mock_pool)):
        with pytest.raises(ValueError) as exc_info:
            await inserir_qualidade_limnologia(dados_fake)
        assert "Operação bloqueada" in str(exc_info.value)
        mock_conn.execute.assert_not_called()

@pytest.mark.asyncio
async def test_inserir_qualidade_consumo_lote_inativo():
    """Verifica se inserir_qualidade_consumo bloqueia se não houver lote ativo."""
    mock_conn = AsyncMock()
    mock_conn.fetchval.return_value = 0  # Lote inativo

    mock_pool = MagicMock()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

    dados_fake = {
        "estrutura_uid": "estrutura-inativa",
        "data_coleta": date.today(),
        "hora_coleta": "10:00",
        "ph": 6.8,
        "sdt": 150.0,
        "orp": 300.0,
        "ppm_cloro": 0.5
    }

    with patch("src.bots.db.get_pool", AsyncMock(return_value=mock_pool)):
        with pytest.raises(ValueError) as exc_info:
            await inserir_qualidade_consumo(dados_fake)
        assert "Operação bloqueada" in str(exc_info.value)
        mock_conn.execute.assert_not_called()
