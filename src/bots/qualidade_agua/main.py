#!/usr/bin/env python3
"""
Bot Telegram para lançamento de qualidade de água.
"""
import os
import sys
import asyncio
from datetime import date, datetime, time
from dotenv import load_dotenv

# Adicionar o caminho do projeto ao sys.path para permitir importações do src
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.append(project_root)

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Importação local
from db import (
    get_tanques_ativos,
    get_lote_por_tanque,
    inserir_qualidade_agua,
)

# ==========================
# CONFIG
# ==========================
load_dotenv()
BOT_TOKEN = os.environ.get("BOT_AGUA_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Token do bot de qualidade da água não encontrado no .env")

estado_chat: dict[int, dict] = {}

# ==========================
# FUNÇÕES AUXILIARES
# ==========================

def teclado_sim_nao(prefix: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Sim", callback_data=f"{prefix}:sim")
    kb.button(text="Não", callback_data=f"{prefix}:nao")
    kb.adjust(2)
    return kb.as_markup()

def parse_data_br(texto: str) -> date:
    texto = texto.strip()
    if not texto: return date.today()
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(texto, fmt).date()
        except ValueError:
            continue
    raise ValueError("Formato de data inválido (use DD/MM/AA)")

def parse_float(texto: str) -> float:
    return float(texto.replace(",", "."))

# ==========================
# HANDLERS
# ==========================

async def cmd_start(message: Message):
    await message.answer(
        "💧 *Monitoramento de Qualidade da Água*\n\n"
        "Use /lancar para registrar parâmetros (pH, Amônia, Nitrito) de um tanque com lote ativo.\n\n"
        "🛠️ *Geral*\n"
        "/cancel - Cancelar operação atual",
        parse_mode="Markdown"
    )

async def cmd_lancar(message: Message):
    chat_id = message.chat.id
    try:
        tanques = await get_tanques_ativos()
        if not tanques:
            await message.answer("⚠️ Nenhum tanque com lote ativo encontrado. Abra um lote no bot de Biometria primeiro.")
            return
        
        kb = InlineKeyboardBuilder()
        for t in tanques:
            kb.button(text=t, callback_data=f"agua_t:{t}")
        kb.adjust(2)
        
        estado_chat[chat_id] = {"step": "selecionando_tanque"}
        await message.answer("--- Registro de Qualidade de Água ---\nEscolha o tanque:", reply_markup=kb.as_markup())
    except Exception as e:
        await message.answer(f"❌ Erro: {e}")

async def callback_tanque(call: CallbackQuery):
    chat_id = call.message.chat.id
    tanque = call.data.split(":")[1]
    lote = await get_lote_por_tanque(tanque)
    
    estado_chat[chat_id] = {"step": "data", "tanque": tanque, "lote": lote}
    await call.message.answer(f"🐟 {tanque} (Lote {lote})\nData da coleta (DD/MM/AA) [vazio = Hoje]:")
    await call.answer()

async def cmd_cancel(message: Message):
    estado_chat.pop(message.chat.id, None)
    await message.answer("❌ Operação cancelada.")

# ==========================
# MÁQUINA DE ESTADOS (TEXTO)
# ==========================

async def handle_messages(message: Message):
    chat_id = message.chat.id
    estado = estado_chat.get(chat_id)
    if not estado or not message.text: return

    step = estado["step"]
    texto = message.text.strip()

    try:
        if step == "data":
            estado["data_coleta"] = parse_data_br(texto)
            estado["step"] = "hora"
            await message.answer("Hora da coleta (HH:MM) [vazio = agora]:")

        elif step == "hora":
            if texto == "":
                estado["hora_coleta"] = datetime.now().time().replace(second=0, microsecond=0)
            else:
                estado["hora_coleta"] = datetime.strptime(texto, "%H:%M").time()
            estado["step"] = "ph"
            await message.answer("Informe o pH (ex: 7.2):")

        elif step == "ph":
            estado["ph"] = parse_float(texto)
            estado["step"] = "amonia"
            await message.answer("Informe Amônia (mg/L, ex: 0.25):")

        elif step == "amonia":
            estado["amonia"] = parse_float(texto)
            estado["step"] = "nitrito"
            await message.answer("Informe Nitrito (mg/L, ex: 0.10):")

        elif step == "nitrito":
            estado["nitrito"] = parse_float(texto)
            estado["step"] = "anotacao_pergunta"
            await message.answer("Deseja adicionar anotação de manejo?", reply_markup=teclado_sim_nao("anot"))

        elif step == "anotacao_texto":
            estado["anotacao"] = texto
            await finalizar_registro(message, estado)

    except ValueError:
        await message.answer("⚠️ Valor inválido. Tente novamente com o formato correto.")
    except Exception as e:
        await message.answer(f"❌ Erro inesperado: {e}")
        estado_chat.pop(chat_id, None)

async def callback_anotacao(call: CallbackQuery):
    chat_id = call.message.chat.id
    estado = estado_chat.get(chat_id)
    if not estado: return

    if call.data == "anot:sim":
        estado["step"] = "anotacao_texto"
        await call.message.answer("Digite a anotação (ex: Probiótico, CAL 10 sacos):")
    else:
        estado["anotacao"] = None
        await finalizar_registro(call.message, estado)
    await call.answer()

async def finalizar_registro(message: Message, estado: dict):
    try:
        await inserir_qualidade_agua(estado)
        resumo = (
            f"✅ *Qualidade da Água Salva!*\n\n"
            f"📍 {estado['tanque']} (Lote {estado['lote']})\n"
            f"📅 {estado['data_coleta'].strftime('%d/%m/%Y')} {estado['hora_coleta'].strftime('%H:%M')}\n"
            f"🧪 pH: `{estado['ph']}`\n"
            f"🧪 Amônia: `{estado['amonia']} mg/L`\n"
            f"🧪 Nitrito: `{estado['nitrito']} mg/L`\n"
            f"📝 Manejo: {estado['anotacao'] or '-'}"
        )
        await message.answer(resumo, parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Erro ao salvar: {e}")
    finally:
        estado_chat.pop(message.chat.id, None)

# ==========================
# MAIN
# ==========================

async def main():
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_lancar, Command("lancar"))
    dp.message.register(cmd_cancel, Command("cancel"))
    
    dp.callback_query.register(callback_tanque, F.data.startswith("agua_t:"))
    dp.callback_query.register(callback_anotacao, F.data.startswith("anot:"))
    
    dp.message.register(handle_messages, F.text)

    print("Iniciando o bot de Qualidade da Água...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
