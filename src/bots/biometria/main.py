#!/usr/bin/env python3
"""
Bot Telegram para biometria e gestão técnica de lotes.
Fluxo adaptado para múltiplas propriedades e estruturas.
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
from aiogram.types import Message, CallbackQuery  # noqa: E402
from aiogram.utils.keyboard import InlineKeyboardBuilder  # noqa: E402

# Importação local
from .db import (  # noqa: E402
    get_estruturas_ativas,
    get_todas_estruturas,
    get_lote_por_estrutura,
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

def parse_int(texto: str) -> int:
    return int(texto.strip())

# ==========================
# HANDLERS GERAIS
# ==========================

async def cmd_start(message: Message):
    await message.answer(
        "🌿 *Gestor de Biometria e Lotes*\n\n"
        "📊 *Manejo*\n"
        "/lancar - Registrar biometria (Estoque/Peso/Mortalidade)\n\n"
        "📦 *Ciclo de Vida*\n"
        "/novo_lote - Alojamento (Início de Ciclo)\n"
        "/fechar_lote - Finalização (Venda/Abate)\n\n"
        "🛠️ *Geral*\n"
        "/cancel - Cancelar operação atual",
        parse_mode="Markdown"
    )

async def cmd_cancel(message: Message):
    estado_chat.pop(message.chat.id, None)
    await message.answer("❌ Operação cancelada.")

# ==========================
# FLUXO: NOVO LOTE
# ==========================

async def cmd_novo_lote(message: Message):
    chat_id = message.chat.id
    estruturas = await get_todas_estruturas()
    kb = InlineKeyboardBuilder()
    for e in estruturas:
        label = f"{e['propriedade']} - {e['nome']}"
        kb.button(text=label, callback_data=f"nl_uid:{e['uid']}")
    kb.adjust(1)
    estado_chat[chat_id] = {"step": "nl_estrutura"}
    await message.answer("--- Iniciar Novo Lote ---\nEscolha a estrutura:", reply_markup=kb.as_markup())

async def callback_novo_lote_uid(call: CallbackQuery):
    chat_id = call.message.chat.id
    uid = call.data.split(":")[1]
    lote_ativo = await get_lote_por_estrutura(uid)
    if lote_ativo:
        await call.message.answer(f"⚠️ Esta estrutura já possui o Lote {lote_ativo} ativo.")
        estado_chat.pop(chat_id, None)
    else:
        estado_chat[chat_id] = {"step": "nl_lote_nome", "estrutura_uid": uid}
        await call.message.answer("Digite a Identificação do Lote (ex: 2024/01):")
    await call.answer()

# ==========================
# FLUXO: FECHAR LOTE
# ==========================

async def cmd_fechar_lote(message: Message):
    chat_id = message.chat.id
    estruturas = await get_estruturas_ativas()
    if not estruturas:
        await message.answer("⚠️ Nenhuma estrutura com lote ativo para fechar.")
        return
    kb = InlineKeyboardBuilder()
    for e in estruturas:
        label = f"{e['propriedade']} - {e['nome']}"
        kb.button(text=label, callback_data=f"fl_uid:{e['uid']}")
    kb.adjust(1)
    estado_chat[chat_id] = {"step": "fl_estrutura"}
    await message.answer("--- Fechar Lote ---\nEscolha a estrutura:", reply_markup=kb.as_markup())

async def callback_fechar_lote_uid(call: CallbackQuery):
    chat_id = call.message.chat.id
    uid = call.data.split(":")[1]
    lote = await get_lote_por_estrutura(uid)
    estado_chat[chat_id] = {"step": "fl_data", "estrutura_uid": uid, "lote": lote}
    await call.message.answer(f">> Fechar Lote {lote}\nData Final (DD/MM/AA) [vazio = Hoje]:")
    await call.answer()

# ==========================
# FLUXO: BIOMETRIA (LANÇAMENTO)
# ==========================

async def cmd_lancar(message: Message):
    chat_id = message.chat.id
    estruturas = await get_estruturas_ativas()
    if not estruturas:
        await message.answer("⚠️ Nenhuma estrutura com lote ativo. Use /novo_lote.")
        return
    kb = InlineKeyboardBuilder()
    for e in estruturas:
        label = f"{e['propriedade']} - {e['nome']}"
        kb.button(text=label, callback_data=f"bio_uid:{e['uid']}")
    kb.adjust(1)
    estado_chat[chat_id] = {"step": "bio_estrutura"}
    await message.answer("--- Lançar Biometria ---\nEscolha a estrutura:", reply_markup=kb.as_markup())

async def callback_bio_uid(call: CallbackQuery):
    chat_id = call.message.chat.id
    uid = call.data.split(":")[1]
    lote = await get_lote_por_estrutura(uid)
    estado_chat[chat_id] = {"step": "bio_data", "estrutura_uid": uid, "lote": lote}
    await call.message.answer(f"📊 Lote {lote}\nData (DD/MM/AA) [vazio = Hoje]:")
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

    try:
        # --- LÓGICA NOVO LOTE ---
        if step == "nl_lote_nome":
            estado["lote"] = texto
            estado["step"] = "nl_data"
            await message.answer("Data Início (DD/MM/AA) [vazio = Hoje]:")
        
        elif step == "nl_data":
            estado["data_alojamento"] = parse_data_br(texto)
            estado["step"] = "nl_qtd"
            await message.answer("Quantidade Alojada:")

        elif step == "nl_qtd":
            estado["peixes_alojados"] = parse_int(texto)
            estado["step"] = "nl_peso"
            await message.answer("Peso Médio Inicial (g):")

        elif step == "nl_peso":
            estado["peso_medio"] = parse_float(texto)
            estado["step"] = "nl_area"
            await message.answer("Área Útil (m²):")

        elif step == "nl_area":
            area = parse_float(texto)
            estado["area_acude"] = area
            estado["densidade"] = round(estado["peixes_alojados"] / area, 2)
            estado["step"] = "nl_desc"
            await message.answer(f"Densidade: {estado['densidade']}\n\nDescrição (vazio p/ pular):")

        elif step == "nl_desc":
            estado["descricao"] = texto if texto else None
            await criar_lote_completo(estado)
            await message.answer(f"✅ Lote {estado['lote']} iniciado!")
            estado_chat.pop(chat_id, None)

        # --- LÓGICA FECHAR LOTE ---
        elif step == "fl_data":
            estado["data_abate"] = parse_data_br(texto)
            estado["step"] = "fl_qtd"
            await message.answer("Quantidade Total Entregue/Vendida:")

        elif step == "fl_qtd":
            estado["qtd_peixes_entregues"] = parse_int(texto)
            estado["step"] = "fl_peso"
            await message.answer("Peso Total (kg):")

        elif step == "fl_peso":
            estado["peso_entregue"] = parse_float(texto)
            estado["step"] = "fl_rend"
            await message.answer("Rendimento (%) [vazio = 0]:")

        elif step == "fl_rend":
            estado["pct_rend_file"] = parse_float(texto) if texto else 0
            estado["step"] = "fl_valor"
            await message.answer("Valor Unitário (R$):")

        elif step == "fl_valor":
            estado["reais_por_peixe"] = parse_float(texto)
            if await finalizar_lote_abate(estado):
                await message.answer(f"✅ Lote {estado['lote']} finalizado!")
            estado_chat.pop(chat_id, None)

        # --- LÓGICA BIOMETRIA ---
        elif step == "bio_data":
            estado["data_bio"] = parse_data_br(texto)
            estado["step"] = "bio_qtd"
            await message.answer("Quantidade (Estoque atual):")

        elif step == "bio_qtd":
            estado["quantidade"] = parse_int(texto)
            estado["step"] = "bio_mortalidade"
            await message.answer("Mortalidade desde o último registro:")

        elif step == "bio_mortalidade":
            estado["mortalidade"] = parse_int(texto)
            estado["step"] = "bio_peso"
            await message.answer("Peso Médio (g):")

        elif step == "bio_peso":
            estado["peso"] = parse_float(texto)
            estado["step"] = "bio_racao"
            await message.answer("Consumo de Ração (kg):")

        elif step == "bio_racao":
            await inserir_biometria(
                estrutura_uid=estado["estrutura_uid"],
                data_biometria=estado["data_bio"],
                quantidade=estado["quantidade"],
                peso_medio=estado["peso"],
                mortalidade=estado["mortalidade"],
                consumo_racao=parse_float(texto),
                lote=estado["lote"]
            )
            await message.answer("✅ Biometria registrada!")
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
    
    dp.callback_query.register(callback_bio_uid, F.data.startswith("bio_uid:"))
    dp.callback_query.register(callback_novo_lote_uid, F.data.startswith("nl_uid:"))
    dp.callback_query.register(callback_fechar_lote_uid, F.data.startswith("fl_uid:"))
    
    dp.message.register(handle_messages, F.text)

    print("Iniciando o bot de Biometria...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
