import os
import base64
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

# Configurações Evolution API v2 (WhatsApp)
EVOLUTION_API_URL = os.environ.get("EVOLUTION_API_URL", "http://hermes-evolution-api:8080").rstrip("/")
EVOLUTION_API_KEY = os.environ.get(
    "EVOLUTION_API_KEY",
    "8c114ae397eb273edfe82e05728be8b4e17cc25649d7e26df40c438c67c368b0"
)
EVOLUTION_INSTANCE = os.environ.get("EVOLUTION_INSTANCE", "hermes")
ENABLE_WHATSAPP = os.environ.get("ENABLE_WHATSAPP", "true").lower() in ("1", "true", "yes")
ENABLE_TELEGRAM = os.environ.get("ENABLE_TELEGRAM", "false").lower() in ("1", "true", "yes")


def normalize_whatsapp_number(phone: str) -> str:
    """Higieniza o número de telefone e adiciona DDI 55 caso possua apenas DDD + número (10 ou 11 dígitos)."""
    digits = "".join(ch for ch in str(phone or "") if ch.isdigit())
    if not digits:
        return ""
    if len(digits) in (10, 11) and not digits.startswith("55"):
        digits = "55" + digits
    return digits


def send_whatsapp_message(
    text: str,
    phone: str = None,
    only_alerts: bool = False,
    only_reports: bool = False
) -> bool:
    """
    Envia mensagem de texto via Evolution API v2 (WhatsApp).
    Se 'phone' for informado, envia diretamente para aquele número (ex: teste individual).
    Caso contrário, consulta dinamicamente os contatos ativos na tabela 'contatos_whatsapp'.
    """
    if not EVOLUTION_API_URL or not EVOLUTION_API_KEY or not EVOLUTION_INSTANCE:
        logger.warning("Evolution API não configurada completamente. Mensagem WhatsApp ignorada.")
        return False

    targets = []
    if phone:
        norm = normalize_whatsapp_number(phone)
        if norm:
            targets.append(("Teste Direto", norm))
    else:
        try:
            from src.services.database import listar_contatos_whatsapp
            contatos = listar_contatos_whatsapp(
                apenas_ativos=True,
                apenas_alertas=only_alerts,
                apenas_relatorios=only_reports
            )
            for c in contatos:
                norm = normalize_whatsapp_number(c.get("telefone", ""))
                if norm:
                    targets.append((c.get("nome", "Contato"), norm))
        except Exception as e:
            logger.error("Erro ao consultar contatos_whatsapp: %s", e)
            return False

    if not targets:
        logger.info("Nenhum destinatário WhatsApp ativo encontrado para envio.")
        return False

    url = f"{EVOLUTION_API_URL}/message/sendText/{EVOLUTION_INSTANCE}"
    headers = {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }

    any_sent = False
    for nome, numero in targets:
        payload = {
            "number": numero,
            "text": text
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            logger.info("WhatsApp enviado com sucesso via Evolution API para %s (%s).", nome, numero)
            any_sent = True
        except Exception as e:
            logger.error("Erro ao enviar WhatsApp via Evolution API para %s (%s): %s", nome, numero, e)

    return any_sent


def send_whatsapp_photo(
    caption: str,
    photo_path: str,
    phone: str = None,
    only_alerts: bool = False,
    only_reports: bool = True
) -> bool:
    """Envia uma imagem com legenda via Evolution API v2 (WhatsApp) para contatos ativos."""
    if not EVOLUTION_API_URL or not EVOLUTION_API_KEY or not EVOLUTION_INSTANCE:
        logger.warning("Evolution API não configurada. Imagem WhatsApp ignorada.")
        return False

    try:
        with open(photo_path, "rb") as img_file:
            b64_media = base64.b64encode(img_file.read()).decode("utf-8")
    except FileNotFoundError:
        logger.error("Arquivo de imagem não encontrado em %s", photo_path)
        return False

    targets = []
    if phone:
        norm = normalize_whatsapp_number(phone)
        if norm:
            targets.append(("Teste Direto", norm))
    else:
        try:
            from src.services.database import listar_contatos_whatsapp
            contatos = listar_contatos_whatsapp(
                apenas_ativos=True,
                apenas_alertas=only_alerts,
                apenas_relatorios=only_reports
            )
            for c in contatos:
                norm = normalize_whatsapp_number(c.get("telefone", ""))
                if norm:
                    targets.append((c.get("nome", "Contato"), norm))
        except Exception as e:
            logger.error("Erro ao consultar contatos_whatsapp para foto: %s", e)
            return False

    if not targets:
        return False

    url = f"{EVOLUTION_API_URL}/message/sendMedia/{EVOLUTION_INSTANCE}"
    headers = {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }

    any_sent = False
    for nome, numero in targets:
        payload = {
            "number": numero,
            "mediatype": "image",
            "mimetype": "image/png",
            "caption": caption,
            "media": b64_media,
            "fileName": os.path.basename(photo_path) or "relatorio.png"
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=20)
            response.raise_for_status()
            logger.info("Imagem WhatsApp enviada para %s (%s).", nome, numero)
            any_sent = True
        except Exception as e:
            logger.error("Erro ao enviar imagem WhatsApp para %s (%s): %s", nome, numero, e)

    return any_sent


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
    """
    Fachada unificada de mensageria (Alertas e Relatórios).
    1. Envia push via ntfy.sh.
    2. Envia para os contatos ativos no WhatsApp (Evolution API) quando ENABLE_WHATSAPP=true.
    3. Envia para o Telegram apenas se ENABLE_TELEGRAM=true.
    """
    is_urgent = "🚨" in text or "⚠️" in text or "OFFLINE" in text.upper() or "CRÍTICO" in text.upper()

    # 1. Espelhamento automático para ntfy.sh
    if notify_ntfy:
        priority = "urgent" if is_urgent else "default"
        tags = ["fish"]
        if "🚨" in text or "CRÍTICO" in text.upper():
            tags.extend(["rotating_light", "warning"])
        elif "⚠️" in text or "OFFLINE" in text.upper():
            tags.append("warning")
        elif "🟢" in text or "ONLINE" in text.upper():
            tags.append("white_check_mark")
        send_ntfy_message(text, title="Piscicultura Alerta", priority=priority, tags=tags)

    # 2. Envio via Evolution API (WhatsApp) para contatos cadastrados no Postgres
    if ENABLE_WHATSAPP and chat_id is None:
        send_whatsapp_message(text, only_alerts=is_urgent, only_reports=not is_urgent)

    # 3. Envio para Telegram (apenas se habilitado ou chamado explicitamente com chat_id em testes)
    if not ENABLE_TELEGRAM and chat_id is None:
        return

    target_chat = chat_id or DEFAULT_CHAT_ID
    if not TELEGRAM_TOKEN or not target_chat:
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
    """Envia uma imagem com legenda via WhatsApp (Evolution API) e opcionalmente Telegram."""
    if ENABLE_WHATSAPP and chat_id is None:
        send_whatsapp_photo(caption, photo_path, only_reports=True)

    if not ENABLE_TELEGRAM and chat_id is None:
        return

    target_chat = chat_id or DEFAULT_CHAT_ID
    if not TELEGRAM_TOKEN or not target_chat:
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
