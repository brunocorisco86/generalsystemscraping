import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from src.services.weather import get_weather_forecast

@patch('openmeteo_requests.Client')
def test_get_weather_forecast(mock_client_class):
    # Setup mock
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    
    mock_response = MagicMock()
    mock_client.weather_api.return_value = [mock_response]
    
    # Mock Current data
    mock_current = MagicMock()
    mock_response.Current.return_value = mock_current
    mock_current.Time.return_value = 1715270400  # Exemplo de timestamp
    
    # Simular variáveis (0: temp, 1: humidity, 2: pressure, 3: cloud_cover)
    var0 = MagicMock()
    var0.Value.return_value = 25.5
    var1 = MagicMock()
    var1.Value.return_value = 60.0
    var2 = MagicMock()
    var2.Value.return_value = 1013.0
    var3 = MagicMock()
    var3.Value.return_value = 45.0
    
    mock_current.Variables.side_effect = [var0, var1, var2, var3]
    
    # Mock Hourly data
    mock_hourly = MagicMock()
    mock_response.Hourly.return_value = mock_hourly
    mock_hourly.Time.return_value = 1715270400
    mock_hourly.TimeEnd.return_value = 1715277600
    mock_hourly.Interval.return_value = 3600
    
    # Simular arrays numpy para hourly
    h_var0 = MagicMock()
    h_var0.ValuesAsNumpy.return_value = [25.5, 24.0]
    h_var1 = MagicMock()
    h_var1.ValuesAsNumpy.return_value = [60.0, 65.0]
    h_var2 = MagicMock()
    h_var2.ValuesAsNumpy.return_value = [0.0, 0.5]
    h_var3 = MagicMock()
    h_var3.ValuesAsNumpy.return_value = [1013.0, 1012.0]
    h_var4 = MagicMock()
    h_var4.ValuesAsNumpy.return_value = [10, 80]
    h_var5 = MagicMock()
    h_var5.ValuesAsNumpy.return_value = [45.0, 50.0]
    
    mock_hourly.Variables.side_effect = [h_var0, h_var1, h_var2, h_var3, h_var4, h_var5]
    
    # Mock Daily data
    mock_daily = MagicMock()
    mock_response.Daily.return_value = mock_daily
    mock_daily.Time.return_value = 1715270400
    mock_daily.TimeEnd.return_value = 1715270400 + (86400 * 2)
    mock_daily.Interval.return_value = 86400
    
    d_var0 = MagicMock()
    d_var0.ValuesAsNumpy.return_value = [28.0, 27.0]
    d_var1 = MagicMock()
    d_var1.ValuesAsNumpy.return_value = [18.0, 17.0]
    d_var2 = MagicMock()
    d_var2.ValuesAsNumpy.return_value = [10, 20]
    d_var3 = MagicMock()
    d_var3.ValuesAsNumpy.return_value = [0.0, 2.0]
    d_var4 = MagicMock()
    d_var4.ValuesAsNumpy.return_value = [1013.0, 1012.0]
    
    mock_daily.Variables.side_effect = [d_var0, d_var1, d_var2, d_var3, d_var4]
    
    mock_response.Latitude.return_value = -24.0
    mock_response.Longitude.return_value = -53.0
    mock_response.Elevation.return_value = 400.0
    mock_response.Timezone.return_value = b"America/Sao_Paulo"
    
    # Execute
    result = get_weather_forecast()
    
    # Assertions
    assert result["latitude"] == -24.0
    assert result["longitude"] == -53.0
    assert result["current"]["temperature_2m"] == 25.5
    assert result["current"]["cloud_cover"] == 45.0
    assert isinstance(result["hourly"], pd.DataFrame)
    assert len(result["hourly"]) == 2
    assert result["hourly"]["temperature_2m"].iloc[0] == 25.5
    assert result["hourly"]["cloud_cover"].iloc[0] == 45.0

@patch('os.getenv')
@patch('openmeteo_requests.Client')
def test_get_weather_forecast_env_vars(mock_client_class, mock_getenv):
    """Verifica se o serviço utiliza as coordenadas do .env corretamente."""
    # Setup mocks para coordenadas customizadas
    def side_effect(key, default=None):
        if key == "LATITUDE_SEDE": return "-25.5"
        if key == "LONGITUDE_SEDE": return "-54.5"
        return default
    mock_getenv.side_effect = side_effect
    
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_response = MagicMock()
    mock_client.weather_api.return_value = [mock_response]
    
    # Mock Current e Hourly (mínimo para não quebrar)
    curr = MagicMock()
    curr.Time.return_value = 1715270400
    curr.Variables.return_value = MagicMock(Value=lambda: 0.0)
    mock_response.Current.return_value = curr
    
    hourly = MagicMock()
    hourly.Time.return_value = 1715270400
    hourly.TimeEnd.return_value = 1715270400 + 3600
    hourly.Interval.return_value = 3600
    hourly.Variables.return_value = MagicMock(ValuesAsNumpy=lambda: [0.0])
    mock_response.Hourly.return_value = hourly

    daily = MagicMock()
    daily.Time.return_value = 1715270400
    daily.TimeEnd.return_value = 1715270400 + 86400
    daily.Interval.return_value = 86400
    daily.Variables.return_value = MagicMock(ValuesAsNumpy=lambda: [0.0])
    mock_response.Daily.return_value = daily
    
    mock_response.Latitude.return_value = -25.5
    mock_response.Longitude.return_value = -54.5
    
    # Execute
    get_weather_forecast()
    
    # Verificar se o cliente foi chamado com as coordenadas do "os.getenv"
    args, kwargs = mock_client.weather_api.call_args
    assert kwargs['params']['latitude'] == -25.5
    assert kwargs['params']['longitude'] == -54.5
