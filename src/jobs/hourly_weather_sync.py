#!/usr/bin/env python3
"""
Job Horário de Sincronização de Clima (Ultra-Leve - Sem Pandas)
Coleta os dados atuais e previsão de 7 dias da API Open-Meteo via JSON HTTP puro,
salva em logs/latest_weather.json e persiste no SQLite local.
"""
import os
import sys
import json
import logging
import requests
from dotenv import load_dotenv

# Adicionar a raiz do projeto ao sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.services.database import get_sqlite_connection, get_local_now

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_openmeteo_json() -> dict | None:
    """Busca previsão do tempo da Open-Meteo via HTTP JSON puro (0 MB de overhead de Pandas)."""
    latitude = float(os.getenv("LATITUDE_SEDE", -24.333941440395304))
    longitude = float(os.getenv("LONGITUDE_SEDE", -53.81788447629622))

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m,relative_humidity_2m,rain,surface_pressure,precipitation_probability,cloud_cover",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum,surface_pressure_mean,cloud_cover_mean",
        "current": "temperature_2m,relative_humidity_2m,surface_pressure,cloud_cover",
        "timezone": "America/Sao_Paulo",
        "forecast_days": 7,
        "wind_speed_unit": "ms",
    }

    try:
        resp = requests.get(url, params=params, timeout=8)
        resp.raise_for_status()
        raw = resp.json()

        curr = raw.get("current", {})
        current_data = {
            "time": curr.get("time"),
            "temperature_2m": float(curr.get("temperature_2m", 0.0)),
            "relative_humidity_2m": float(curr.get("relative_humidity_2m", 0.0)),
            "surface_pressure": float(curr.get("surface_pressure", 0.0)),
            "cloud_cover": float(curr.get("cloud_cover", 0.0)),
        }

        h = raw.get("hourly", {})
        h_times = h.get("time", [])
        hourly_records = []
        for idx, t_str in enumerate(h_times):
            hourly_records.append({
                "date": t_str,
                "temperature_2m": h.get("temperature_2m", [0])[idx],
                "relative_humidity_2m": h.get("relative_humidity_2m", [0])[idx],
                "rain": h.get("rain", [0])[idx],
                "surface_pressure": h.get("surface_pressure", [0])[idx],
                "precipitation_probability": h.get("precipitation_probability", [0])[idx],
                "cloud_cover": h.get("cloud_cover", [0])[idx],
            })

        d = raw.get("daily", {})
        d_times = d.get("time", [])
        daily_records = []
        for idx, d_str in enumerate(d_times):
            daily_records.append({
                "date": d_str,
                "temperature_2m_max": d.get("temperature_2m_max", [0])[idx],
                "temperature_2m_min": d.get("temperature_2m_min", [0])[idx],
                "precipitation_probability_max": d.get("precipitation_probability_max", [0])[idx],
                "precipitation_sum": d.get("precipitation_sum", [0])[idx],
                "surface_pressure_mean": d.get("surface_pressure_mean", [0])[idx],
                "cloud_cover_mean": d.get("cloud_cover_mean", [0])[idx],
            })

        result = {
            "latitude": raw.get("latitude", latitude),
            "longitude": raw.get("longitude", longitude),
            "elevation": raw.get("elevation", 0.0),
            "timezone": raw.get("timezone", "America/Sao_Paulo"),
            "current": current_data,
            "hourly": hourly_records,
            "daily": daily_records,
        }

        log_dir = os.path.join(project_root, "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "latest_weather.json")
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        return result
    except Exception as e:
        logger.error(f"Erro ao consultar Open-Meteo JSON: {e}")
        return None


def sync_hourly_weather():
    """Obtém o clima atual e salva na tabela clima_historico e no cache JSON."""
    logger.info("Iniciando sincronização horária de clima...")

    try:
        weather_data = fetch_openmeteo_json()
        if not weather_data:
            # Tenta ler último cache local caso a internet falhe momentaneamente
            log_path = os.path.join(project_root, "logs", "latest_weather.json")
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8") as f:
                    weather_data = json.load(f)

        if not weather_data or not weather_data.get("current"):
            logger.error("Não foi possível obter os dados atuais do clima.")
            return

        current = weather_data["current"]
        temp = float(current.get("temperature_2m", 0.0))
        umid = float(current.get("relative_humidity_2m", 0.0))
        pres = float(current.get("surface_pressure", 0.0))
        cloud = float(current.get("cloud_cover", 0.0))

        conn = get_sqlite_connection()
        if not conn:
            logger.error("Não foi possível conectar ao SQLite.")
            return

        try:
            cursor = conn.cursor()
            now_str = get_local_now().strftime('%Y-%m-%d %H:%M:%S')
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
