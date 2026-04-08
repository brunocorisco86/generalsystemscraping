#!/usr/bin/env python3
"""
Bot Telegram para biometria da piscicultura.
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

# A importação agora é relativa ao pacote do bot
from .db import (
    get_tanques_ativos,
    get_lote_por_tanque,
    inserir_biometria,
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
# FUNÇÃO AUXILIAR: TECLADO SIM/NÃO
# ==========================

def teclado_sim_nao(prefix: str) -> InlineKeyboardMarkup:
    """
    Cria teclado inline com botões Sim/Não.
    """
    kb = InlineKeyboardBuilder()
    kb.button(text="Sim", callback_data=f"{prefix}:sim")
    kb.button(text="Não", callback_data=f"{prefix}:nao")
    kb.adjust(2)
    return kb.as_markup()


# ==========================
# FUNÇÃO AUXILIAR: PARSE DE DATA
# ==========================

def parse_data_br(texto: str) -> date:
    """
    Aceita formatos de data brasileiros (DD/MM/AAAA, DD/MM/AA).
    """
    texto = texto.strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(texto, fmt).date()
        except ValueError:
            continue
    raise ValueError("Formato de data inválido")


# ==========================
# HANDLERS
# ==========================

async def cmd_start(message: Message):
    await message.answer(
        "👋 Olá! Use /lancar para registrar biometria de um tanque."
    )


async def cmd_lancar(message: Message):
    chat_id = message.chat.id
    try:
        tanques = await get_tanques_ativos()
    except Exception as e:
        await message.answer(f"❌ Erro ao buscar tanques ativos: {e}")
        return

    if not tanques:
        await message.answer("⚠️ Nenhum tanque com lote ativo encontrado.")
        return

    kb = InlineKeyboardBuilder()
    for t in tanques:
        kb.button(text=t, callback_data=f"tanque:{t}")
    kb.adjust(2)

    estado_chat[chat_id] = {"step": "selecionando_tanque"}

    await message.answer(
        "--- Seleção de Tanque para Biometria ---\n"
        "Escolha o tanque:",
        reply_markup=kb.as_markup(),
    )

async def cmd_cancel(message: Message):
    chat_id = message.chat.id
    if chat_id in estado_chat:
        estado_chat.pop(chat_id, None)
        await message.answer(
            "❌ Lançamento cancelado. "
            "Quando quiser começar de novo, use /lancar."
        )
    else:
        await message.answer("Nenhum lançamento em andamento no momento.")

async def callback_tanque(call: CallbackQuery):
    chat_id = call.message.chat.id
    data = call.data or ""

    if not data.startswith("tanque:"):
        await call.answer()
        return

    tanque = data.split(":", 1)[1]
    try:
        lote = await get_lote_por_tanque(tanque)
    except Exception as e:
        await call.message.answer(f"❌ Erro ao buscar lote para o tanque {tanque}: {e}")
        await call.answer()
        return

    if not lote:
        await call.message.answer(
            f"[!] Nenhum lote ativo encontrado para o tanque {tanque}."
        )
        await call.answer()
        return

    estado_chat[chat_id] = {
        "step": "data",
        "tanque": tanque,
        "lote": lote,
    }

    await call.message.answer(
        f">> Lançamento: {tanque} (Lote: {lote})\n\n"
        "Data (DD/MM/AAAA ou DD/MM/AA) [vazio = Hoje]:"
    )
    await call.answer()


async def fluxo_biometria(message: Message):
    chat_id = message.chat.id
    estado = estado_chat.get(chat_id)

    if not estado or "step" not in estado:
        return

    step = estado["step"]
    texto = message.text.strip() if message.text else ""

    try:
        # ---- DATA ----
        if step == "data":
            if texto == "":
                estado["data_biometria"] = date.today()
            else:
                estado["data_biometria"] = parse_data_br(texto)
            estado["step"] = "volume"
            await message.answer("Volume (Estoque peixes):")

        # ---- VOLUME ----
        elif step == "volume":
            estado["volume_peixes"] = int(texto)
            estado["step"] = "peso"
            await message.answer("Peso Médio (g):")

        # ---- PESO ----
        elif step == "peso":
            estado["peso_medio_g"] = float(texto.replace(",", "."))
            estado["step"] = "racao"
            await message.answer("Consumo de Ração (kg):")

        # ---- RAÇÃO + INSERT ----
        elif step == "racao":
            estado["consumo_racao_kg"] = float(texto.replace(",", "."))

            await inserir_biometria(
                tanque=estado["tanque"],
                data_biometria=estado["data_biometria"],
                volume_peixes=estado["volume_peixes"],
                peso_medio_g=estado["peso_medio_g"],
                consumo_racao_kg=estado["consumo_racao_kg"],
                lote=int(estado["lote"]),
            )
            await message.answer(
                f"✅ Registro salvo para o {estado['tanque']}!\n\n"
                f"Data: {estado['data_biometria'].isoformat()}\n"
                f"Volume: {estado['volume_peixes']}\n"
                f"Peso médio: {estado['peso_medio_g']} g\n"
                f"Ração: {estado['consumo_racao_kg']} kg"
            )

            estado["step"] = "repetir_mesmo_tanque"
            await message.answer(
                f"Deseja realizar outro lançamento para o {estado['tanque']}?",
                reply_markup=teclado_sim_nao("repete"),
            )
    except ValueError as e:
        await message.answer(f"Valor inválido: {e}. Por favor, tente novamente.")
    except Exception as e:
        await message.answer(f"❌ Erro inesperado: {e}")
        estado_chat.pop(chat_id, None)


# ==========================
# CALLBACKS SIM/NÃO
# ==========================

async def callback_repete(call: CallbackQuery):
    """Botões Sim/Não para repetir lançamento no mesmo tanque."""
    chat_id = call.message.chat.id
    estado = estado_chat.get(chat_id)
    if not estado:
        await call.answer()
        return

    if call.data == "repete:sim":
        estado["step"] = "data"
        await call.message.answer(
            f">> Novo lançamento: {estado['tanque']} (Lote: {estado['lote']})\n\n"
            "Data (DD/MM/AAAA ou DD/MM/AA) [vazio = Hoje]:"
        )
    elif call.data == "repete:nao":
        estado["step"] = "outro_tanque"
        await call.message.answer(
            "Deseja continuar lançando (outro tanque)?",
            reply_markup=teclado_sim_nao("continua"),
        )
    await call.answer()


async def callback_continua(call: CallbackQuery):
    """Botões Sim/Não para continuar lançando em outro tanque ou encerrar."""
    chat_id = call.message.chat.id
    estado = estado_chat.get(chat_id)
    if not estado:
        await call.answer()
        return

    if call.data == "continua:sim":
        estado_chat.pop(chat_id, None)
        await call.message.answer("Ok, vamos selecionar outro tanque.")
        # Reusa a função de comando para reiniciar o fluxo
        await cmd_lancar(call.message)
    elif call.data == "continua:nao":
        await call.message.answer(
            "✅ Lançamentos concluídos. Obrigado! "
            "Quando quiser registrar novamente, use /lancar."
        )
        estado_chat.pop(chat_id, None)
    await call.answer()


# ==========================
# MAIN
# ==========================

async def main():
    bot = Bot(
        BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    dp = Dispatcher()

    # Registra todos os handlers
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_lancar, Command("lancar"))
    dp.message.register(cmd_cancel, Command("cancel"))
    dp.callback_query.register(callback_tanque, F.data.startswith("tanque:"))
    dp.callback_query.register(callback_repete, F.data.startswith("repete:"))
    dp.callback_query.register(callback_continua, F.data.startswith("continua:"))
    # Este handler deve ser o último para mensagens de texto
    dp.message.register(fluxo_biometria, F.text)

    try:
        print("Iniciando o bot de Biometria...")
        await dp.start_polling(bot)
    except Exception as e:
        print(f"Erro fatal no bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())

