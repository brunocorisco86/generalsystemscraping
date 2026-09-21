#!/usr/bin/env python3
"""
Serviço coletor e despachante periódico autônomo para execução em container Docker.
Substitui a necessidade de crontab bare-metal, executando coleta via API,
checagem de alertas críticos e sincronização com baixo consumo de CPU e RAM.
"""
import time
import signal
import sys
import logging
from datetime import datetime

from src.scrape.monitor_data import scrape_and_save
from src.alerts.alert_check import check_alerts
from src.alerts.offline_check import check_last_reading as check_offline
from src.jobs.hourly_weather_sync import sync_hourly_weather
from src.database.postgres.migrate_data import migrate_data

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [CollectorService] - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

running = True

def handle_shutdown(signum, frame):
    global running
    logger.info("Recebido sinal de encerramento (%s). Finalizando graceful shutdown...", signum)
    running = False

signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

def run_collector_loop():
    logger.info("=== Iniciando Coletor Autônomo da Piscicultura (Noctua IoT) ===")
    
    last_scrape = 0
    last_alert = 0
    last_weather = 0
    last_migrate = 0

    INTERVAL_SCRAPE = 600       # 10 minutos
    INTERVAL_ALERT = 900        # 15 minutos
    INTERVAL_WEATHER = 3600     # 1 hora
    INTERVAL_MIGRATE = 21600    # 6 horas (ou 2x ao dia)

    # Executa a primeira tomada de dados imediatamente ao subir o container
    logger.info("Executando primeira tomada de dados imediata...")
    try:
        scrape_and_save()
        last_scrape = time.time()
    except Exception as e:
        logger.error("Erro na tomada inicial: %s", e)

    while running:
        now = time.time()

        # 1. Coleta via API (10 min)
        if now - last_scrape >= INTERVAL_SCRAPE:
            try:
                logger.info("⏰ Ciclo de Coleta de Sensores (10m)...")
                scrape_and_save()
                last_scrape = now
            except Exception as e:
                logger.error("Erro no ciclo de coleta: %s", e)

        # 2. Checagem de Alertas e Offline (15 min)
        if now - last_alert >= INTERVAL_ALERT:
            try:
                logger.info("⏰ Ciclo de Checagem de Alertas e Conectividade (15m)...")
                check_alerts()
                check_offline()
                last_alert = now
            except Exception as e:
                logger.error("Erro no ciclo de alertas: %s", e)

        # 3. Sincronização de Clima (1h)
        if now - last_weather >= INTERVAL_WEATHER:
            try:
                logger.info("⏰ Ciclo de Sincronização Meteorológica (1h)...")
                sync_hourly_weather()
                last_weather = now
            except Exception as e:
                logger.error("Erro na sincronização de clima: %s", e)

        # 4. Migração Histórica Postgres (6h)
        if now - last_migrate >= INTERVAL_MIGRATE:
            try:
                logger.info("⏰ Ciclo de Migração SQLite -> PostgreSQL...")
                migrate_data(silent=True)
                last_migrate = now
            except Exception as e:
                logger.error("Erro na migração de dados: %s", e)

        # Sleep curto de 10 segundos para responder rápido ao sinal de shutdown
        time.sleep(10)

    logger.info("=== Coletor Autônomo finalizado com sucesso ===")

if __name__ == "__main__":
    run_collector_loop()
