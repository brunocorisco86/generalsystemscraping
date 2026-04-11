#!/usr/bin/env python3
"""
Bot Telegram para biometria e gestão de lotes da piscicultura.
"""
import os
import sys
import asyncio
from datetime import date, datetime
from dotenv import load_dotenv

# Adicionar o caminho do projeto ao sys.path para permitir importações do src
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.append(project_root)

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Importação local (db.py na mesma pasta)
from db import (
    get_tanques_ativos,
    get_todos_tanques,
    get_lote_por_tanque,
    inserir_biometria,
    criar_lote,
    fechar_lote,
)

# ==========================
# CONFIG
# ==========================
load_dotenv()
BOT_TOKEN = os.environ.get("BOT_BIOMETRIA_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Token do bot de biometria não encontrado no .env")

# Estado simples em memória por chat
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
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(texto, fmt).date()
        except ValueError:
            continue
    raise ValueError("Formato de data inválido (use DD/MM/AA)")


# ==========================
# HANDLERS: GESTÃO DE LOTES
# ==========================

async def cmd_start(message: Message):
    await message.answer(
        "👋 Olá! Bem-vindo ao Gestor de Piscicultura.\n\n"
        "📊 *Biometria*\n"
        "/lancar - Registrar biometria\n\n"
        "📦 *Gestão de Lotes*\n"
        "/novo_lote - Abrir novo lote\n"
        "/fechar_lote - Encerrar lote atual\n\n"
        "🛠️ *Geral*\n"
        "/cancel - Cancelar operação atual",
        parse_mode="Markdown"
    )

async def cmd_novo_lote(message: Message):
    chat_id = message.chat.id
    try:
        tanques = await get_todos_tanques()
        kb = InlineKeyboardBuilder()
        for t in tanques:
            kb.button(text=t, callback_data=f"novo_lote_tanque:{t}")
        kb.adjust(2)
        estado_chat[chat_id] = {"step": "novo_lote_selecionando_tanque"}
        await message.answer("--- Abertura de Novo Lote ---\nEscolha o tanque:", reply_markup=kb.as_markup())
    except Exception as e:
        await message.answer(f"❌ Erro: {e}")

async def callback_novo_lote_tanque(call: CallbackQuery):
    chat_id = call.message.chat.id
    tanque = call.data.split(":")[1]
    lote_atual = await get_lote_por_tanque(tanque)
    if lote_atual:
        await call.message.answer(f"⚠️ O {tanque} já possui o Lote {lote_atual} ativo. Feche-o antes de abrir um novo.")
        estado_chat.pop(chat_id, None)
    else:
        estado_chat[chat_id] = {"step": "novo_lote_data", "tanque": tanque}
        await call.message.answer(f">> Novo Lote: {tanque}\nData de Início (DD/MM/AA) [vazio = Hoje]:")
    await call.answer()

async def cmd_fechar_lote(message: Message):
    chat_id = message.chat.id
    tanques = await get_tanques_ativos()
    if not tanques:
        await message.answer("⚠️ Nenhum lote ativo encontrado para fechar.")
        return
    kb = InlineKeyboardBuilder()
    for t in tanques:
        kb.button(text=t, callback_data=f"fechar_lote_tanque:{t}")
    kb.adjust(2)
    estado_chat[chat_id] = {"step": "fechar_lote_selecionando_tanque"}
    await message.answer("--- Encerramento de Lote ---\nEscolha o tanque:", reply_markup=kb.as_markup())

async def callback_fechar_lote_tanque(call: CallbackQuery):
    chat_id = call.message.chat.id
    tanque = call.data.split(":")[1]
    lote = await get_lote_por_tanque(tanque)
    estado_chat[chat_id] = {"step": "fechar_lote_data", "tanque": tanque, "lote": lote}
    await call.message.answer(f">> Fechar Lote {lote} ({tanque})\nData do Abate (DD/MM/AA) [vazio = Hoje]:")
    await call.answer()


# ==========================
# HANDLERS: BIOMETRIA
# ==========================

async def cmd_lancar(message: Message):
    chat_id = message.chat.id
    try:
        tanques = await get_tanques_ativos()
        if not tanques:
            await message.answer("⚠️ Nenhum tanque com lote ativo encontrado. Use /novo_lote primeiro.")
            return
        kb = InlineKeyboardBuilder()
        for t in tanques:
            kb.button(text=t, callback_data=f"tanque:{t}")
        kb.adjust(2)
        estado_chat[chat_id] = {"step": "selecionando_tanque"}
        await message.answer("--- Registro de Biometria ---\nEscolha o tanque:", reply_markup=kb.as_markup())
    except Exception as e:
        await message.answer(f"❌ Erro: {e}")

async def callback_tanque(call: CallbackQuery):
    chat_id = call.message.chat.id
    tanque = call.data.split(":")[1]
    lote = await get_lote_por_tanque(tanque)
    estado_chat[chat_id] = {"step": "data", "tanque": tanque, "lote": lote}
    await call.message.answer(f">> Lançamento: {tanque} (Lote: {lote})\nData (DD/MM/AA) [vazio = Hoje]:")
    await call.answer()

async def cmd_cancel(message: Message):
    chat_id = message.chat.id
    estado_chat.pop(chat_id, None)
    await message.answer("❌ Operação cancelada.")


# ==========================
# FLUXO DE MENSAGENS (MÁQUINA DE ESTADO)
# ==========================

async def handle_messages(message: Message):
    chat_id = message.chat.id
    estado = estado_chat.get(chat_id)
    if not estado or not message.text: return

    step = estado["step"]
    texto = message.text.strip()

    try:
        # --- NOVO LOTE ---
        if step == "novo_lote_data":
            estado["data_inicio"] = date.today() if texto == "" else parse_data_br(texto)
            estado["step"] = "novo_lote_desc"
            await message.answer("Descrição/Observação do lote (vazio para pular):")
        
        elif step == "novo_lote_desc":
            lote_id = await criar_lote(estado["tanque"], estado["data_inicio"], texto if texto else None)
            await message.answer(f"✅ Lote {lote_id} aberto com sucesso para o {estado['tanque']}!")
            estado_chat.pop(chat_id, None)

        # --- FECHAR LOTE ---
        elif step == "fechar_lote_data":
            dt = date.today() if texto == "" else parse_data_br(texto)
            if await fechar_lote(estado["tanque"], dt):
                await message.answer(f"✅ Lote {estado['lote']} encerrado com sucesso!")
            else:
                await message.answer("❌ Falha ao encerrar lote.")
            estado_chat.pop(chat_id, None)

        # --- BIOMETRIA ---
        elif step == "data":
            estado["data_biometria"] = date.today() if texto == "" else parse_data_br(texto)
            estado["step"] = "volume"
            await message.answer("Volume (Estoque peixes):")

        elif step == "volume":
            estado["volume_peixes"] = int(texto)
            estado["step"] = "peso"
            await message.answer("Peso Médio (g):")

        elif step == "peso":
            estado["peso_medio_g"] = float(texto.replace(",", "."))
            estado["step"] = "racao"
            await message.answer("Consumo de Ração (kg):")

        elif step == "racao":
            estado["consumo_racao_kg"] = float(texto.replace(",", "."))
            await inserir_biometria(
                tanque=estado["tanque"], data_biometria=estado["data_biometria"],
                volume_peixes=estado["volume_peixes"], peso_medio_g=estado["peso_medio_g"],
                consumo_racao_kg=estado["consumo_racao_kg"], lote=int(estado["lote"])
            )
            await message.answer(f"✅ Registro salvo para o {estado['tanque']}!")
            estado_chat.pop(chat_id, None)

    except Exception as e:
        await message.answer(f"⚠️ Erro: {e}")
        estado_chat.pop(chat_id, None)


# ==========================
# MAIN
# ==========================

async def main():
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_lancar, Command("lancar"))
    dp.message.register(cmd_novo_lote, Command("novo_lote"))
    dp.message.register(cmd_fechar_lote, Command("fechar_lote"))
    dp.message.register(cmd_cancel, Command("cancel"))
    
    dp.callback_query.register(callback_tanque, F.data.startswith("tanque:"))
    dp.callback_query.register(callback_novo_lote_tanque, F.data.startswith("novo_lote_tanque:"))
    dp.callback_query.register(callback_fechar_lote_tanque, F.data.startswith("fechar_lote_tanque:"))
    
    dp.message.register(handle_messages, F.text)

    print("Iniciando o bot de Biometria...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
