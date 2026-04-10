import os
import requests
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram_message(text: str):
    """Envia uma mensagem de texto simples para o chat configurado."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("AVISO: Token ou Chat ID do Telegram não configurado. Mensagem não enviada.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Erro ao enviar mensagem para o Telegram: {e}")

def send_telegram_photo(caption: str, photo_path: str):
    """Envia uma imagem com legenda para o chat configurado."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("AVISO: Token ou Chat ID do Telegram não configurado. Imagem não enviada.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            files = {'photo': photo}
            data = {
                'chat_id': TELEGRAM_CHAT_ID,
                'caption': caption,
                'parse_mode': 'Markdown'
            }
            response = requests.post(url, data=data, files=files, timeout=30)
            response.raise_for_status()
    except FileNotFoundError:
        print(f"Erro: Arquivo de imagem não encontrado em {photo_path}")
    except requests.RequestException as e:
        print(f"Erro ao enviar imagem para o Telegram: {e}")