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
NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "https://ntfy.sh/piscicultura-patel-palotina")

def send_ntfy_message(
    message: str,
    title: str = "Piscicultura Patel",
    priority: str = "default",
    tags: list = None,
    click_url: str = None
) -> bool:
    """
    Envia uma notificação push via ntfy.sh para o tópico configurado.
    Ultraleve, sem necessidade de bibliotecas pesadas.
    """
    if not NTFY_TOPIC:
        return False

    url = NTFY_TOPIC.strip()
    headers = {
        "Title": title.encode("utf-8"),
        "Priority": priority,
    }
    if tags:
        headers["Tags"] = ",".join(tags)
    if click_url:
        headers["Click"] = click_url

    try:
        response = requests.post(
            url,
            data=message.encode("utf-8"),
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        logger.info("Notificação ntfy.sh enviada com sucesso para %s.", url)
        return True
    except Exception as e:
        logger.error("Erro ao enviar notificação ntfy.sh: %s", e)
        return False

def send_telegram_message(text: str, chat_id=None, notify_ntfy: bool = True):
    """Envia mensagem para o Telegram e opcionalmente espelha via push no ntfy.sh."""
    # Espelhamento automático para ntfy.sh para alertas e relatórios
    if notify_ntfy:
        # Detecta prioridade pelo conteúdo
        priority = "urgent" if "🚨" in text or "⚠️" in text or "OFFLINE" in text else "default"
        tags = ["fish"]
        if "🚨" in text or "CRÍTICO" in text.upper():
            tags.extend(["rotating_light", "warning"])
        elif "⚠️" in text or "OFFLINE" in text.upper():
            tags.append("warning")
        elif "🟢" in text or "ONLINE" in text.upper():
            tags.append("white_check_mark")
        send_ntfy_message(text, title="Piscicultura Alerta", priority=priority, tags=tags)

    target_chat = chat_id or DEFAULT_CHAT_ID
    if not TELEGRAM_TOKEN or not target_chat:
        logger.warning("Token ou Chat ID do Telegram não configurado. Mensagem Telegram ignorada.")
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