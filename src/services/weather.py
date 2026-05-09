import os
import json
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def log_weather_locally(data):
    """
    Salva os dados da previsão em um arquivo JSON local, 
    sobrescrevendo o anterior para economizar espaço.
    """
    try:
        # Tenta encontrar a raiz do projeto para garantir o caminho do log
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        log_dir = os.path.join(base_dir, "logs")
        log_path = os.path.join(log_dir, "latest_weather.json")
        
        os.makedirs(log_dir, exist_ok=True)
        
        # Converter DataFrame para dicionário para serialização JSON
        serializable_data = data.copy()
        
        # Corrigir tipos não serializáveis (bytes, datetime no DF)
        if isinstance(serializable_data.get("timezone"), bytes):
            serializable_data["timezone"] = serializable_data["timezone"].decode('utf-8')
            
        if isinstance(serializable_data.get("hourly"), pd.DataFrame):
            # Converte as datas para string para o JSON
            df = serializable_data["hourly"].copy()
            df['date'] = df['date'].dt.strftime('%Y-%m-%d %H:%M:%S%z')
            serializable_data["hourly"] = df.to_dict(orient="records")
            
        if isinstance(serializable_data.get("daily"), pd.DataFrame):
            # Converte as datas para string para o JSON no bloco daily
            df_daily = serializable_data["daily"].copy()
            df_daily['date'] = df_daily['date'].dt.strftime('%Y-%m-%d')
            serializable_data["daily"] = df_daily.to_dict(orient="records")
        
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(serializable_data, f, indent=4, ensure_ascii=False)
            
    except Exception as e:
        # IMPORTANTE: Silenciamos o erro para não travar o bot se o disco/pasta falhar
        print(f"AVISO: Não foi possível salvar log local de clima (permissão ou disco): {e}")

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
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_probability_max", "precipitation_sum", "surface_pressure_mean"],
        "current": ["temperature_2m", "relative_humidity_2m", "surface_pressure"],
        "timezone": "America/Sao_Paulo",
        "forecast_days": 7,
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
    hourly_df['date'] = pd.to_datetime(hourly_df['date']).dt.tz_convert("America/Sao_Paulo")

    # Processar dados diários
    daily = response.Daily()
    daily_data = {
        "date": pd.date_range(
            start=pd.to_datetime(daily.Time(), unit="s", utc=True),
            end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=daily.Interval()),
            inclusive="left"
        ).tz_convert("America/Sao_Paulo"),
        "temperature_2m_max": daily.Variables(0).ValuesAsNumpy(),
        "temperature_2m_min": daily.Variables(1).ValuesAsNumpy(),
        "precipitation_probability_max": daily.Variables(2).ValuesAsNumpy(),
        "precipitation_sum": daily.Variables(3).ValuesAsNumpy(),
        "surface_pressure_mean": daily.Variables(4).ValuesAsNumpy(),
    }
    daily_df = pd.DataFrame(data=daily_data)
    daily_df['date'] = pd.to_datetime(daily_df['date']).dt.tz_convert("America/Sao_Paulo")

    result = {
        "latitude": response.Latitude(),
        "longitude": response.Longitude(),
        "elevation": response.Elevation(),
        "timezone": response.Timezone(),
        "current": current_data,
        "hourly": hourly_df,
        "daily": daily_df
    }

    # Salva o log localmente (sobrescrevendo o anterior)
    log_weather_locally(result)

    return result

if __name__ == "__main__":
    # Teste rápido de execução direta
    result = get_weather_forecast()
    print(f"Clima atual em {result['latitude']}, {result['longitude']}:")
    print(f"Temperatura: {result['current']['temperature_2m']}°C")
    print(f"Umidade: {result['current']['relative_humidity_2m']}%")
    print("\nPrevisão próxima hora:")
    print(result['hourly'].head(2))
