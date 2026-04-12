#!/usr/bin/env python3
"""
Bot Telegram para biometria e gestão técnica de lotes (C.VALE / PATEL).
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
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Importação local
from db import (
    get_tanques_ativos,
    get_todos_tanques,
    get_lote_por_tanque,
    inserir_biometria,
    criar_lote_completo,
    finalizar_lote_abate,
)

# ==========================
# CONFIG
# ==========================
load_dotenv()
BOT_TOKEN = os.environ.get("BOT_BIOMETRIA_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Token do bot de biometria não encontrado no .env")

estado_chat: dict[int, dict] = {}

# ==========================
# FUNÇÕES AUXILIARES
# ==========================

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
# HANDLERS GERAIS
# ==========================

async def cmd_start(message: Message):
    await message.answer(
        "🌿 *Gestor de Piscicultura - C.VALE / PATEL*\n\n"
        "📊 *Manejo*\n"
        "/lancar - Registrar biometria periódica\n\n"
        "📦 *Ciclo de Vida*\n"
        "/novo_lote - Alojamento (Ficha Verde)\n"
        "/fechar_lote - Abate (Fechamento Final)\n\n"
        "🛠️ *Geral*\n"
        "/cancel - Cancelar operação atual",
        parse_mode="Markdown"
    )

async def cmd_cancel(message: Message):
    estado_chat.pop(message.chat.id, None)
    await message.answer("❌ Operação cancelada.")

# ==========================
# FLUXO: NOVO LOTE (FICHA VERDE)
# ==========================

async def cmd_novo_lote(message: Message):
    chat_id = message.chat.id
    tanques = await get_todos_tanques()
    kb = InlineKeyboardBuilder()
    for t in tanques: kb.button(text=t, callback_data=f"nl_t:{t}")
    kb.adjust(2)
    estado_chat[chat_id] = {"step": "nl_tanque"}
    await message.answer("--- Novo Alojamento ---\nEscolha o tanque:", reply_markup=kb.as_markup())

async def callback_novo_lote_tanque(call: CallbackQuery):
    chat_id = call.message.chat.id
    tanque = call.data.split(":")[1]
    lote_ativo = await get_lote_por_tanque(tanque)
    if lote_ativo:
        await call.message.answer(f"⚠️ O {tanque} já possui o Lote {lote_ativo} ativo.")
        estado_chat.pop(chat_id, None)
    else:
        estado_chat[chat_id] = {"step": "nl_lote_nome", "tanque": tanque}
        await call.message.answer(f"📍 Tanque: {tanque}\nDigite a Identificação do Lote (ex: 2024/01):")
    await call.answer()

# ==========================
# FLUXO: FECHAR LOTE (ABATE)
# ==========================

async def cmd_fechar_lote(message: Message):
    chat_id = message.chat.id
    tanques = await get_tanques_ativos()
    if not tanques:
        await message.answer("⚠️ Nenhum lote ativo para fechar.")
        return
    kb = InlineKeyboardBuilder()
    for t in tanques: kb.button(text=t, callback_data=f"fl_t:{t}")
    kb.adjust(2)
    estado_chat[chat_id] = {"step": "fl_tanque"}
    await message.answer("--- Fechamento de Lote (Abate) ---\nEscolha o tanque:", reply_markup=kb.as_markup())

async def callback_fechar_lote_tanque(call: CallbackQuery):
    chat_id = call.message.chat.id
    tanque = call.data.split(":")[1]
    lote = await get_lote_por_tanque(tanque)
    estado_chat[chat_id] = {"step": "fl_data", "tanque": tanque, "lote": lote}
    await call.message.answer(f">> Fechar Lote {lote} ({tanque})\nData do Abate (DD/MM/AA) [vazio = Hoje]:")
    await call.answer()

# ==========================
# FLUXO: BIOMETRIA (LANÇAMENTO)
# ==========================

async def cmd_lancar(message: Message):
    chat_id = message.chat.id
    tanques = await get_tanques_ativos()
    if not tanques:
        await message.answer("⚠️ Nenhum lote ativo. Use /novo_lote.")
        return
    kb = InlineKeyboardBuilder()
    for t in tanques: kb.button(text=t, callback_data=f"bio_t:{t}")
    kb.adjust(2)
    estado_chat[chat_id] = {"step": "bio_tanque"}
    await message.answer("--- Registro de Biometria ---\nEscolha o tanque:", reply_markup=kb.as_markup())

async def callback_bio_tanque(call: CallbackQuery):
    chat_id = call.message.chat.id
    tanque = call.data.split(":")[1]
    lote = await get_lote_por_tanque(tanque)
    estado_chat[chat_id] = {"step": "bio_data", "tanque": tanque, "lote": lote}
    await call.message.answer(f"🐟 {tanque} (Lote {lote})\nData (DD/MM/AA) [vazio = Hoje]:")
    await call.answer()

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
        # --- LÓGICA NOVO LOTE ---
        if step == "nl_lote_nome":
            estado["lote"] = texto
            estado["step"] = "nl_data"
            await message.answer("Data Alojamento (DD/MM/AA) [vazio = Hoje]:")
        
        elif step == "nl_data":
            estado["data_alojamento"] = parse_data_br(texto)
            estado["step"] = "nl_qtd"
            await message.answer("Quantidade de Peixes Alojados:")

        elif step == "nl_qtd":
            estado["peixes_alojados"] = int(texto)
            estado["step"] = "nl_peso"
            await message.answer("Peso Médio Inicial (g):")

        elif step == "nl_peso":
            estado["peso_medio"] = parse_float(texto)
            estado["step"] = "nl_area"
            await message.answer("Área do Açude (m²):")

        elif step == "nl_area":
            area = parse_float(texto)
            estado["area_acude"] = area
            estado["densidade"] = round(estado["peixes_alojados"] / area, 2)
            estado["step"] = "nl_desc"
            await message.answer(f"Densidade calculada: {estado['densidade']} peixes/m²\n\nDescrição opcional (vazio p/ pular):")

        elif step == "nl_desc":
            estado["descricao"] = texto if texto else None
            lote_id = await criar_lote_completo(estado)
            await message.answer(f"✅ Lote {lote_id} registrado com sucesso!")
            estado_chat.pop(chat_id, None)

        # --- LÓGICA FECHAR LOTE ---
        elif step == "fl_data":
            estado["data_abate"] = parse_data_br(texto)
            estado["step"] = "fl_qtd"
            await message.answer("Quantidade de Peixes Entregues:")

        elif step == "fl_qtd":
            estado["qtd_peixes_entregues"] = int(texto)
            estado["step"] = "fl_peso"
            await message.answer("Peso Total Entregue (kg):")

        elif step == "fl_peso":
            estado["peso_entregue"] = parse_float(texto)
            estado["step"] = "fl_rend"
            await message.answer("Rendimento Filé (%):")

        elif step == "fl_rend":
            estado["pct_rend_file"] = parse_float(texto)
            estado["step"] = "fl_valor"
            await message.answer("Valor Pago por Peixe (R$):")

        elif step == "fl_valor":
            estado["reais_por_peixe"] = parse_float(texto)
            if await finalizar_lote_abate(estado):
                await message.answer(f"✅ Lote {estado['lote']} finalizado com sucesso!")
            estado_chat.pop(chat_id, None)

        # --- LÓGICA BIOMETRIA ---
        elif step == "bio_data":
            estado["data_bio"] = parse_data_br(texto)
            estado["step"] = "bio_vol"
            await message.answer("Volume (Estoque peixes):")

        elif step == "bio_vol":
            estado["volume"] = int(texto)
            estado["step"] = "bio_peso"
            await message.answer("Peso Médio (g):")

        elif step == "bio_peso":
            estado["peso"] = parse_float(texto)
            estado["step"] = "bio_racao"
            await message.answer("Consumo de Ração (kg):")

        elif step == "bio_racao":
            await inserir_biometria(
                tanque=estado["tanque"], data_biometria=estado["data_bio"],
                volume_peixes=estado["volume"], peso_medio_g=estado["peso"],
                consumo_racao_kg=parse_float(texto), lote=estado["lote"]
            )
            await message.answer(f"✅ Biometria salva para o {estado['tanque']}!")
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
    
    dp.callback_query.register(callback_bio_tanque, F.data.startswith("bio_t:"))
    dp.callback_query.register(callback_novo_lote_tanque, F.data.startswith("nl_t:"))
    dp.callback_query.register(callback_fechar_lote_tanque, F.data.startswith("fl_t:"))
    
    dp.message.register(handle_messages, F.text)

    print("Iniciando o bot de Biometria (Schema C.VALE)...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
