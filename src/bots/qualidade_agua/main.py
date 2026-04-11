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

# Importação local (db.py na mesma pasta)
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

# Estado simples em memória por chat
estado_chat: dict[int, dict] = {}


# ==========================
# FUNÇÕES AUXILIARES
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

def parse_data_ddmma(texto: str) -> date:
    """
    Converte 'DD/MM/AA' ou 'DD/MM/AAAA' para date.
    """
    texto = texto.strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(texto, fmt).date()
        except ValueError:
            continue
    raise ValueError("Formato de data inválido")


# ==========================
# HANDLERS DE COMANDO
# ==========================

async def cmd_start(message: Message):
    await message.answer(
        "👋 Olá! Use /lancar para registrar qualidade de água de um tanque."
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
        "--- Seleção de Tanque para Qualidade de Água ---\n"
        "Escolha o tanque:",
        reply_markup=kb.as_markup(),
    )

async def cmd_cancel(message: Message):
    chat_id = message.chat.id
    if chat_id in estado_chat:
        estado_chat.pop(chat_id, None)
        await message.answer(
            "❌ Lançamento cancelado.\n"
            "Quando quiser começar de novo, use /lancar."
        )
    else:
        await message.answer("Nenhum lançamento em andamento no momento.")


# ==========================
# CALLBACK: ESCOLHA DO TANQUE
# ==========================

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
        "lote": int(lote),
    }

    await call.message.answer(
        f">> Lançamento: {tanque} (Lote: {lote})\n\n"
        "Data da coleta (DD/MM/AA) [vazio = Hoje]:"
    )
    await call.answer()


# ==========================
# FLUXO PRINCIPAL (mensagens de texto)
# ==========================

async def fluxo_agua(message: Message):
    chat_id = message.chat.id
    estado = estado_chat.get(chat_id)
    if not estado or "step" not in estado:
        return

    step = estado["step"]
    texto = (message.text or "").strip()

    try:
        if step == "data":
            if texto == "":
                estado["data_coleta"] = date.today()
            else:
                estado["data_coleta"] = parse_data_ddmma(texto)
            estado["step"] = "hora"
            await message.answer("Hora da coleta (HH:MM) [vazio = horário atual]:")

        elif step == "hora":
            if texto == "":
                estado["hora_coleta"] = datetime.now().time().replace(second=0, microsecond=0)
            else:
                estado["hora_coleta"] = datetime.strptime(texto, "%H:%M").time()
            estado["step"] = "ph"
            await message.answer("Informe o pH (ex: 7.2):")

        elif step == "ph":
            estado["ph"] = float(texto.replace(",", "."))
            estado["step"] = "amonia"
            await message.answer("Informe Amônia (mg/L, ex: 0.25):")

        elif step == "amonia":
            estado["amonia"] = float(texto.replace(",", "."))
            estado["step"] = "nitrito"
            await message.answer("Informe Nitrito (mg/L, ex: 0.10):")

        elif step == "nitrito":
            estado["nitrito"] = float(texto.replace(",", "."))
            estado["step"] = "aguardando_pergunta_anotacao"
            await message.answer(
                "Quer lançar anotação de manejo (Probiótico, CAL, SAL, etc.)?",
                reply_markup=teclado_sim_nao("anotacao"),
            )

        elif step == "anotacao_valor":
            estado["anotacao_manejo"] = texto if texto != "" else None
            await salvar_e_resumir(message, estado)

    except ValueError:
        await message.answer("Valor inválido. Por favor, tente novamente com o formato correto.")
    except Exception as e:
        await message.answer(f"❌ Erro inesperado: {e}")
        estado_chat.pop(chat_id, None)


# ==========================
# CALLBACK: SIM/NÃO ANOTAÇÃO
# ==========================

async def callback_anotacao(call: CallbackQuery):
    chat_id = call.message.chat.id
    estado = estado_chat.get(chat_id)
    if not estado:
        await call.answer()
        return

    if call.data == "anotacao:sim":
        estado["step"] = "anotacao_valor"
        await call.message.answer("Digite a anotação de manejo (ex: Probiótico, CAL 10 sacos):")
    elif call.data == "anotacao:nao":
        estado["anotacao_manejo"] = None
        await salvar_e_resumir(call.message, estado)

    await call.answer()


# ==========================
# SALVAR E RESUMIR
# ==========================

async def salvar_e_resumir(message: Message, estado: dict):
    chat_id = message.chat.id

    try:
        await inserir_qualidade_agua(
            id_tanque=estado["tanque"],
            id_lote=estado["lote"],
            data_coleta=estado["data_coleta"],
            hora_coleta=estado["hora_coleta"],
            ph=estado.get("ph"),
            amonia=estado.get("amonia"),
            nitrito=estado.get("nitrito"),
            anotacao_manejo=estado.get("anotacao_manejo"),
        )

        resumo = (
            f"✅ Registro salvo para o {estado['tanque']}!\n\n"
            f"Data: {estado['data_coleta'].isoformat()} {estado['hora_coleta'].strftime('%H:%M')}\n"
            f"pH: {estado.get('ph', '-')}\n"
            f"Amônia: {estado.get('amonia', '-')} mg/L\n"
            f"Nitrito: {estado.get('nitrito', '-')} mg/L\n"
            f"Manejo: {estado.get('anotacao_manejo') or '-'}"
        )
        await message.answer(resumo)
    except Exception as e:
        await message.answer(f"❌ Erro ao salvar no banco: {e}")
        estado_chat.pop(chat_id, None)
        return

    # Pergunta se quer repetir no mesmo tanque
    estado["step"] = "repetir_mesmo_tanque"
    await message.answer(
        f"Deseja realizar outro lançamento para o {estado['tanque']}?",
        reply_markup=teclado_sim_nao("repete"),
    )


# ==========================
# CALLBACKS REPETIR / CONTINUAR
# ==========================

async def callback_repete(call: CallbackQuery):
    chat_id = call.message.chat.id
    estado = estado_chat.get(chat_id)
    if not estado:
        await call.answer()
        return

    if call.data == "repete:sim":
        # Reinicia o fluxo para o mesmo tanque
        estado["step"] = "data"
        await call.message.answer(
            f">> Novo lançamento: {estado['tanque']} (Lote: {estado['lote']})\n\n"
            "Data da coleta (DD/MM/AA) [vazio = Hoje]:"
        )
    elif call.data == "repete:nao":
        # Pergunta se quer continuar em outro tanque
        estado["step"] = "outro_tanque"
        await call.message.answer(
            "Deseja continuar lançando em outro tanque?",
            reply_markup=teclado_sim_nao("continua"),
        )
    await call.answer()


async def callback_continua(call: CallbackQuery):
    chat_id = call.message.chat.id
    if call.data == "continua:sim":
        estado_chat.pop(chat_id, None)
        await call.message.answer("Ok, vamos selecionar outro tanque.")
        await cmd_lancar(call.message)
    elif call.data == "continua:nao":
        estado_chat.pop(chat_id, None)
        await call.message.answer(
            "✅ Lançamentos concluídos. Obrigado!\n"
            "Quando quiser registrar novamente, use /lancar."
        )
    await call.answer()


# ==========================
# MAIN
# ==========================

async def main():
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    # Registra todos os handlers
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_lancar, Command("lancar"))
    dp.message.register(cmd_cancel, Command("cancel"))
    dp.callback_query.register(callback_tanque, F.data.startswith("tanque:"))
    dp.callback_query.register(callback_anotacao, F.data.startswith("anotacao:"))
    dp.callback_query.register(callback_repete, F.data.startswith("repete:"))
    dp.callback_query.register(callback_continua, F.data.startswith("continua:"))
    dp.message.register(fluxo_agua, F.text)

    try:
        print("Iniciando o bot de Qualidade da Água...")
        await dp.start_polling(bot)
    except Exception as e:
        print(f"Erro fatal no bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())

