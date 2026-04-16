import os
import requests
import logging
from dotenv import load_dotenv

# Configuração do logger
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
DEFAULT_CHAT_ID = os.environ.get("TELEGRAM_GROUP_ID")

def send_telegram_message(text: str, chat_id=None):
    """Envia uma mensagem de texto simples para o chat configurado ou um chat_id específico."""
    target_chat = chat_id or DEFAULT_CHAT_ID
    if not TELEGRAM_TOKEN or not target_chat:
        logger.warning("Token ou Chat ID do Telegram não configurado. Mensagem não enviada.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": target_chat,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error("Erro ao enviar mensagem para o Telegram: %s", e)

def send_telegram_photo(caption: str, photo_path: str, chat_id=None):
    """Envia uma imagem com legenda para o chat configurado ou um chat_id específico."""
    target_chat = chat_id or DEFAULT_CHAT_ID
    if not TELEGRAM_TOKEN or not target_chat:
        logger.warning("Token ou Chat ID do Telegram não configurado. Imagem não enviada.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            files = {'photo': photo}
            data = {
                'chat_id': target_chat,
                'caption': caption,
                'parse_mode': 'Markdown'
            }
            response = requests.post(url, data=data, files=files, timeout=30)
            response.raise_for_status()
    except FileNotFoundError:
        logger.error("Arquivo de imagem não encontrado em %s", photo_path)
    except requests.RequestException as e:
        logger.error("Erro ao enviar imagem para o Telegram: %s", e)