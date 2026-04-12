#!/usr/bin/env python3
"""
Bot Telegram para qualidade da água.
Fluxo adaptado para detectar tipo de exploração (Limnologia vs Consumo).
"""
import os
import sys
import asyncio
from datetime import date, datetime
from dotenv import load_dotenv

# Adicionar o caminho do projeto ao sys.path para permitir importações do src
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.append(project_root)

from aiogram import Bot, Dispatcher, F  # noqa: E402
from aiogram.client.default import DefaultBotProperties  # noqa: E402
from aiogram.filters import Command  # noqa: E402
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup  # noqa: E402
from aiogram.utils.keyboard import InlineKeyboardBuilder  # noqa: E402

# Importação local
from .db import (  # noqa: E402
    get_estruturas_ativas,
    get_lote_por_estrutura,
    inserir_qualidade_limnologia,
    inserir_qualidade_consumo,
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
    if not texto:
        return date.today()
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(texto, fmt).date()
        except ValueError:
            continue
    raise ValueError("Formato de data inválido (use DD/MM/AA)")

def parse_float(texto: str) -> float:
    return float(texto.replace(",", "."))

# ==========================
# HANDLERS: COMANDOS
# ==========================

async def cmd_start(message: Message):
    await message.answer(
        "💧 *Gestor de Qualidade da Água*\n\n"
        "📊 *Manejo*\n"
        "/lancar - Registrar parâmetros (Limnologia ou Consumo)\n\n"
        "📦 *Ciclo de Vida*\n"
        "/novo_lote - Iniciar Lote\n"
        "/fechar_lote - Finalizar Lote\n\n"
        "🛠️ *Geral*\n"
        "/cancel - Cancelar operação atual",
        parse_mode="Markdown"
    )

async def cmd_cancel(message: Message):
    estado_chat.pop(message.chat.id, None)
    await message.answer("❌ Operação cancelada.")

# ==========================
# FLUXO: QUALIDADE DA ÁGUA
# ==========================

async def cmd_lancar(message: Message):
    chat_id = message.chat.id
    try:
        estruturas = await get_estruturas_ativas()
        if not estruturas:
            await message.answer("⚠️ Nenhuma estrutura com lote ativo. Use /novo_lote.")
            return
        kb = InlineKeyboardBuilder()
        for e in estruturas:
            label = f"{e['propriedade']} - {e['nome']}"
            kb.button(text=label, callback_data=f"agua_uid:{e['uid']}:{e['tipo_exploracao_id']}")
        kb.adjust(1)
        estado_chat[chat_id] = {"step": "agua_estrutura"}
        await message.answer("--- Registro de Qualidade de Água ---\nEscolha a estrutura:", reply_markup=kb.as_markup())
    except Exception as e:
        await message.answer(f"❌ Erro: {e}")

async def callback_agua_uid(call: CallbackQuery):
    chat_id = call.message.chat.id
    partes = call.data.split(":")
    uid = partes[1]
    tipo_id = int(partes[2])
    lote = await get_lote_por_estrutura(uid)

    estado_chat[chat_id] = {
        "step": "agua_data",
        "estrutura_uid": uid,
        "tipo_exploracao_id": tipo_id,
        "lote": lote
    }

    tipo_msg = "Piscicultura (Limnologia)" if tipo_id == 1 else "Consumo Animal"
    await call.message.answer(f"📍 {tipo_msg}\nLote {lote}\nData da coleta (DD/MM/AA) [vazio = Hoje]:")
    await call.answer()

# ==========================
# MÁQUINA DE ESTADOS (TEXTO)
# ==========================

async def handle_messages(message: Message):
    chat_id = message.chat.id
    estado = estado_chat.get(chat_id)
    if not estado or not message.text:
        return

    step = estado["step"]
    texto = message.text.strip()
    tipo_id = estado.get("tipo_exploracao_id")

    try:
        # --- FLUXO COMUM ---
        if step == "agua_data":
            estado["data_coleta"] = parse_data_br(texto)
            estado["step"] = "agua_hora"
            await message.answer("Hora da coleta (HH:MM) [vazio = agora]:")

        elif step == "agua_hora":
            estado["hora_coleta"] = datetime.now().time().replace(second=0, microsecond=0) if texto == "" else datetime.strptime(texto, "%H:%M").time()
            estado["step"] = "agua_ph"
            await message.answer("Informe o pH (ex: 7.2):")

        elif step == "agua_ph":
            estado["ph"] = parse_float(texto)
            if tipo_id == 1: # Piscicultura
                estado["step"] = "limno_amonia"
                await message.answer("Amônia (mg/L):")
            else:
                estado["step"] = "cons_sdt"
                await message.answer("SDT (Sólidos Dissolvidos Totais):")

        # --- BRANCH: LIMNOLOGIA (PISCICULTURA) ---
        elif step == "limno_amonia":
            estado["amonia"] = parse_float(texto)
            estado["step"] = "limno_nitrito"
            await message.answer("Nitrito (mg/L):")

        elif step == "limno_nitrito":
            estado["nitrito"] = parse_float(texto)
            estado["step"] = "limno_alcalinidade"
            await message.answer("Alcalinidade (mg/L):")

        elif step == "limno_alcalinidade":
            estado["alcalinidade"] = parse_float(texto)
            estado["step"] = "limno_transparencia"
            await message.answer("Transparência (cm):")

        elif step == "limno_transparencia":
            estado["transparencia"] = parse_float(texto)
            await inserir_qualidade_limnologia(estado)
            await message.answer("✅ Dados de Limnologia salvos com sucesso!")
            estado_chat.pop(chat_id, None)

        # --- BRANCH: CONSUMO ---
        elif step == "cons_sdt":
            estado["sdt"] = parse_float(texto)
            estado["step"] = "cons_orp"
            await message.answer("ORP (mV):")

        elif step == "cons_orp":
            estado["orp"] = parse_float(texto)
            estado["step"] = "cons_cloro"
            await message.answer("Cloro (ppm):")

        elif step == "cons_cloro":
            estado["ppm_cloro"] = parse_float(texto)
            await inserir_qualidade_consumo(estado)
            await message.answer("✅ Dados de Qualidade de Bebida salvos!")
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
    dp.message.register(cmd_cancel, Command("cancel"))
    
    dp.callback_query.register(callback_agua_uid, F.data.startswith("agua_uid:"))
    
    dp.message.register(handle_messages, F.text)

    print("Iniciando o bot de Qualidade da Água (Multitipo)...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
