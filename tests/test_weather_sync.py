import pytest
import sqlite3
import os
from datetime import datetime
from src.jobs.hourly_weather_sync import sync_hourly_weather
from src.jobs.hourly_report import get_hourly_report
from src.services.database import get_sqlite_connection

def test_clima_historico_table_exists():
    """Verifica se a tabela clima_historico foi criada no SQLite."""
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clima_historico'")
    assert cursor.fetchone() is not None
    conn.close()

def test_sync_hourly_weather_persistence():
    """Verifica se o job de sincronização salva dados no banco."""
    # Executa a sincronização (usa mock da API via cache se possível, ou real)
    sync_hourly_weather()
    
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT temperatura, umidade, pressao FROM clima_historico ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    
    assert row is not None
    assert isinstance(row[0], float) # Temperatura
    assert isinstance(row[1], float) # Umidade
    assert isinstance(row[2], float) # Pressao
    conn.close()

def test_hourly_report_includes_weather():
    """Verifica se o relatório horário contém a linha de clima."""
    # Garante que tem dado
    sync_hourly_weather()
    
    # Adiciona uma leitura fake para o relatório não vir vazio
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO leituras (nome_estrutura, oxigenio, temperatura, aeradores_ativos, timestamp_site)
        VALUES (?, ?, ?, ?, ?)
    """, ("Tanque Teste", 5.0, 25.0, 0, "2026-05-09 10:00:00"))
    conn.commit()
    conn.close()
    
    report = get_hourly_report()
    # Verifica a presença do emoji ou palavras chave do clima
    assert "🌤️" in report
    assert "hPa" in report
    assert "💧" in report
