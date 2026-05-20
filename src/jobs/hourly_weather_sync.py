#!/usr/bin/env python3
"""
Job Horário de Sincronização de Clima
Coleta os dados atuais da API Open-Meteo e persiste no SQLite local.
"""
import os
import sys
import logging
from datetime import datetime

# Adicionar a raiz do projeto ao sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

from src.services.weather import get_weather_forecast
from src.services.database import get_sqlite_connection

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def sync_hourly_weather():
    """Obtém o clima atual e salva na tabela clima_historico."""
    logger.info("Iniciando sincronização horária de clima...")
    
    try:
        # 1. Obter dados da API
        weather_data = get_weather_forecast()
        current = weather_data.get("current")
        
        if not current:
            logger.error("Não foi possível obter os dados atuais do clima.")
            return

        temp = current.get("temperature_2m")
        umid = current.get("relative_humidity_2m")
        pres = current.get("surface_pressure")
        cloud = current.get("cloud_cover")
        
        # 2. Persistir no SQLite
        conn = get_sqlite_connection()
        if not conn:
            logger.error("Não foi possível conectar ao SQLite.")
            return
            
        try:
            cursor = conn.cursor()
            # Inserir dados na tabela clima_historico
            # data_coleta usa DEFAULT CURRENT_TIMESTAMP se não fornecido, 
            # mas vamos passar o tempo atual para garantir sincronia com o fuso se necessário.
            # No SQLite, CURRENT_TIMESTAMP é UTC por padrão. 
            # Como o bot usa America/Sao_Paulo, vamos gravar o timestamp local formatado.
            now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                INSERT INTO clima_historico (data_coleta, temperatura, umidade, pressao, cloud_cover)
                VALUES (?, ?, ?, ?, ?)
            ''', (now_str, temp, umid, pres, cloud))
            
            conn.commit()
            logger.info(f"✅ Dados climáticos persistidos: {temp}°C, {umid}%, {pres}hPa, Cloud: {cloud}%")
            
        except Exception as e:
            logger.error(f"Erro ao inserir dados no SQLite: {e}")
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Erro geral no job de sincronização de clima: {e}")

if __name__ == "__main__":
    sync_hourly_weather()
