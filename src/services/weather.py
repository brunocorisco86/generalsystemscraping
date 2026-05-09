import os
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def get_weather_forecast():
    """
    Obtém a previsão do tempo utilizando a API Open-Meteo.
    Utiliza as coordenadas LATITUDE_SEDE e LONGITUDE_SEDE do arquivo .env.
    """
    # Configuração da sessão com cache e retry
    cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Coordenadas (fallback para as fornecidas pelo usuário se não estiverem no .env)
    latitude = float(os.getenv("LATITUDE_SEDE", -24.333941440395304))
    longitude = float(os.getenv("LONGITUDE_SEDE", -53.81788447629622))

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ["temperature_2m", "relative_humidity_2m", "rain", "surface_pressure", "precipitation_probability"],
        "current": ["temperature_2m", "relative_humidity_2m", "surface_pressure"],
        "timezone": "America/Sao_Paulo",
        "forecast_days": 3,
        "wind_speed_unit": "ms",
    }
    
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    # Processar dados atuais
    current = response.Current()
    current_data = {
        "time": current.Time(),
        "temperature_2m": current.Variables(0).Value(),
        "relative_humidity_2m": current.Variables(1).Value(),
        "surface_pressure": current.Variables(2).Value(),
    }

    # Processar dados horários
    hourly = response.Hourly()
    hourly_data = {
        "date": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left"
        ).tz_convert("America/Sao_Paulo"),
        "temperature_2m": hourly.Variables(0).ValuesAsNumpy(),
        "relative_humidity_2m": hourly.Variables(1).ValuesAsNumpy(),
        "rain": hourly.Variables(2).ValuesAsNumpy(),
        "surface_pressure": hourly.Variables(3).ValuesAsNumpy(),
        "precipitation_probability": hourly.Variables(4).ValuesAsNumpy(),
    }

    hourly_df = pd.DataFrame(data=hourly_data)

    return {
        "latitude": response.Latitude(),
        "longitude": response.Longitude(),
        "elevation": response.Elevation(),
        "timezone": response.Timezone(),
        "current": current_data,
        "hourly": hourly_df
    }

if __name__ == "__main__":
    # Teste rápido de execução direta
    result = get_weather_forecast()
    print(f"Clima atual em {result['latitude']}, {result['longitude']}:")
    print(f"Temperatura: {result['current']['temperature_2m']}°C")
    print(f"Umidade: {result['current']['relative_humidity_2m']}%")
    print("\nPrevisão próxima hora:")
    print(result['hourly'].head(2))
