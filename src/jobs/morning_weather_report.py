import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

from src.services.weather import get_weather_forecast
from src.services.notification import send_telegram_message

# Carregar variáveis de ambiente
load_dotenv()

def format_morning_report(data):
    """
    Formata o relatório de bom dia com clima detalhado.
    """
    # Usar fuso horário de São Paulo para identificar "hoje"
    agora = pd.Timestamp.now(tz='America/Sao_Paulo')
    hoje_str = agora.strftime("%d/%m/%Y")
    
    # 1. Cabeçalho
    msg = f"☀️ *BOM DIA! Previsão para {hoje_str}*\n"
    msg += f"📍 Localização: `{data['latitude']:.4f}, {data['longitude']:.4f}`\n\n"
    
    # 2. Resumo de Hoje por Período (Manhã, Tarde, Noite)
    df_hourly = data['hourly']
    # Garantir que a coluna 'date' tenha o timezone correto
    if not isinstance(df_hourly['date'].iloc[0], datetime):
        df_hourly['date'] = pd.to_datetime(df_hourly['date'])
    
    # Filtrar para o dia de hoje (comparando as datas no fuso local)
    hoje_mask = df_hourly['date'].dt.date == agora.date()
    df_hoje = df_hourly[hoje_mask].copy()
    
    if not df_hoje.empty:
        msg += "📅 *Hoje por Período:*\n"
        
        periodos = [
            ("Manhã", 6, 12, "🌅"),
            ("Tarde", 12, 18, "☀️"),
            ("Noite", 18, 24, "🌙")
        ]
        
        for nome, inicio, fim, emoji in periodos:
            # Filtrar horas do período
            df_periodo = df_hoje[(df_hoje['date'].dt.hour >= inicio) & (df_hoje['date'].dt.hour < fim)]
            
            if not df_periodo.empty:
                temp_med = df_periodo['temperature_2m'].mean()
                chuva_max = df_periodo['precipitation_probability'].max()
                
                # Escolher emoji de chuva se probabilidade for alta
                chuva_icon = "🌧️" if chuva_max > 50 else ("🌦️" if chuva_max > 20 else "")
                
                msg += f"{emoji} *{nome}:* `{temp_med:.1f}°C` | {chuva_icon} `{chuva_max:.0f}%` chuva\n"
        msg += "\n"

    # 3. Resumo dos Próximos Dias (Usando o bloco daily)
    if 'daily' in data and not data['daily'].empty:
        df_daily = data['daily']
        if not isinstance(df_daily['date'].iloc[0], datetime):
            df_daily['date'] = pd.to_datetime(df_daily['date'])
            
        msg += "🔭 *Próximos Dias:*\n"
        
        # Mapeamento para tradução manual (evita dependência de locale do sistema)
        dias_pt = {
            'MON': 'SEG', 'TUE': 'TER', 'WED': 'QUA', 'THU': 'QUI',
            'FRI': 'SEX', 'SAT': 'SAB', 'SUN': 'DOM'
        }
        
        # Pular o primeiro dia (hoje) se já mostramos acima, ou mostrar todos
        # Vamos mostrar os próximos 6 dias (fechando a semana)
        proximos_dias = df_daily[df_daily['date'].dt.date > agora.date()].head(6)
        
        for _, row in proximos_dias.iterrows():
            dia_en = row['date'].strftime('%a').upper()
            dia_pt = dias_pt.get(dia_en, dia_en)
            data_dia = row['date'].strftime('%d/%m')
            
            # Formata a linha com temperatura, chance de chuva e volume em mm
            chuva_mm = row.get('precipitation_sum', 0)
            msg += f"• *{dia_pt} ({data_dia}):* `{row['temperature_2m_min']:.0f}°/{row['temperature_2m_max']:.0f}°C` | 🌧️ `{row['precipitation_probability_max']:.0f}%` (`{chuva_mm:.1f}mm`)\n"


    return msg

def main():
    try:
        # 1. Obter dados (isso também atualiza o log local)
        data = get_weather_forecast()
        
        # 2. Formatar mensagem
        mensagem = format_morning_report(data)
        
        # 3. Enviar para o Telegram
        send_telegram_message(mensagem)
        print("Relatório de bom dia enviado com sucesso!")
        
    except Exception as e:
        error_msg = f"❌ Erro ao gerar relatório de bom dia: {e}"
        print(error_msg)
        # Opcional: enviar erro para o admin se send_telegram_message estiver ok
        # send_telegram_message(error_msg)

if __name__ == "__main__":
    main()
