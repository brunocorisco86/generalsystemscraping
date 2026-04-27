#!/usr/bin/env python3
"""
Bot Telegram Unificado - PeixePatelBot
Consolida Biometria, Qualidade de Água e Comandos de Relatórios (ex-Node-RED).
"""
import os
import sys
import asyncio
import logging
from datetime import date, datetime
from dotenv import load_dotenv

# Adicionar o caminho do projeto ao sys.path para permitir importações do src
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

from aiogram import Bot, Dispatcher, F  # noqa: E402
from aiogram.client.default import DefaultBotProperties  # noqa: E402
from aiogram.filters import Command  # noqa: E402
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup  # noqa: E402
from aiogram.utils.keyboard import InlineKeyboardBuilder  # noqa: E402

# Importação de funções de banco de dados centralizadas
from src.bots.db import (  # noqa: E402
    get_estruturas_ativas,
    get_todas_estruturas,
    get_lote_por_estrutura,
    inserir_biometria,
    get_ultimo_estoque,
    criar_lote_completo,
    finalizar_lote_abate,
    inserir_qualidade_limnologia,
    inserir_qualidade_consumo,
)

# ==========================
# CONFIGURAÇÃO E LOGGING
# ==========================
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tenta várias fontes para o Token
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or \
            os.environ.get("BOT_BIOMETRIA_TOKEN") or \
            os.environ.get("TELEGRAM_TOKEN")

GROUP_ID = os.environ.get("TELEGRAM_GROUP_ID")
ADMIN_ID = os.environ.get("TELEGRAM_ADMIN_ID")

if not BOT_TOKEN:
    logger.error("ERRO: Nenhum Token de Bot encontrado no .env (TELEGRAM_BOT_TOKEN, BOT_BIOMETRIA_TOKEN ou TELEGRAM_TOKEN)")
    sys.exit(1)

# Estado do chat (FSM simplificada)
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

def parse_int(texto: str) -> int:
    return int(texto.strip())

async def executar_script_python(script_relative_path: str, chat_id: int):
    """Executa um script Python via subprocess, passando o chat_id."""
    script_path = os.path.join(project_root, script_relative_path)
    python_exe = sys.executable or "python3"
    
    logger.info(f"Executando script: {script_path} para chat_id: {chat_id}")
    
    try:
        process = await asyncio.create_subprocess_exec(
            python_exe, script_path, str(chat_id),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            err_msg = stderr.decode().strip()
            logger.error(f"Erro ao executar {script_relative_path}: {err_msg}")
            # Opcional: avisar o admin
    except Exception as e:
        logger.error(f"Falha crítica ao tentar rodar {script_relative_path}: {e}")

# ==========================
# HANDLERS: COMANDOS GERAIS
# ==========================

async def cmd_start(message: Message):
    await message.answer(
        "🚀 *PeixePatelBot - Sistema Unificado*\n\n"
        "📦 *Manejo e Biometria*\n"
        "/biometria - Registrar peso/mortalidade\n"
        "/novo_lote - Iniciar Ciclo\n"
        "/fechar_lote - Finalizar Ciclo\n\n"
        "💧 *Qualidade da Água*\n"
        "/agua - Registrar parâmetros manuais\n\n"
        "📊 *Relatórios Rápidos*\n"
        "/oxigenio - Nível atual de O2\n"
        "/temperatura - Temperatura atual\n"
        "/ox7d /ox15d - Histórico de Oxigênio\n"
        "/temp7d - Histórico de Temperatura\n"
        "/previsao - Curva de oxigênio\n\n"
        "🛠️ *Sistema*\n"
        "/backup - Sincronizar banco de dados\n"
        "/cancel - Cancelar operação atual",
        parse_mode="Markdown"
    )

async def cmd_cancel(message: Message):
    estado_chat.pop(message.chat.id, None)
    await message.answer("❌ Operação cancelada.")

# ==========================
# HANDLERS: EX-NODE-RED (SUBPROCESS)
# ==========================

@Dispatcher().message(Command("oxigenio"))
async def handle_oxigenio(message: Message):
    await executar_script_python("src/reports/bot_query_oxygen.py", message.chat.id)

@Dispatcher().message(Command("ox7d"))
async def handle_ox7d(message: Message):
    await executar_script_python("src/reports/bot_query_ox_7d.py", message.chat.id)

@Dispatcher().message(Command("ox15d"))
async def handle_ox15d(message: Message):
    await executar_script_python("src/reports/bot_query_ox_15d.py", message.chat.id)

@Dispatcher().message(Command("temp7d"))
async def handle_temp7d(message: Message):
    await executar_script_python("src/reports/bot_query_temp_7d.py", message.chat.id)

@Dispatcher().message(Command("previsao"))
async def handle_previsao(message: Message):
    await executar_script_python("src/analysis/plot_curva.py", message.chat.id)

@Dispatcher().message(Command("temperatura"))
async def handle_temperatura(message: Message):
    await executar_script_python("src/reports/bot_query_temp.py", message.chat.id)

@Dispatcher().message(Command("backup"))
async def handle_backup(message: Message):
    await message.answer("🔄 Iniciando sincronização/backup...")
    await executar_script_python("src/database/postgres/migrate_data.py", message.chat.id)


# ==========================
# FLUXO: QUALIDADE DA ÁGUA
# ==========================

async def cmd_agua(message: Message):
    chat_id = message.chat.id
    try:
        estruturas = await get_estruturas_ativas()
        if not estruturas:
            await message.answer("⚠️ Nenhuma estrutura com lote ativo. Use /novo_lote.")
            return
        kb = InlineKeyboardBuilder()
        for e in estruturas:
            label = f"{e['propriedade']} - {e['nome']}"
            # Truncamos o UID para 32 caracteres para caber no limite de 64 bytes do callback_data
            kb.button(text=label, callback_data=f"agua_uid:{e['uid'][:16]}:{e['tipo_exploracao_id']}")
        kb.adjust(1)
        estado_chat[chat_id] = {"step": "agua_estrutura"}
        await message.answer("--- Registro de Qualidade de Água ---\nEscolha a estrutura:", reply_markup=kb.as_markup())
    except Exception as e:
        await message.answer(f"❌ Erro: {e}")

async def callback_agua_uid(call: CallbackQuery):
    chat_id = call.message.chat.id
    partes = call.data.split(":")
    uid_prefix = partes[1]
    tipo_id = int(partes[2])
    
    # Busca o UID completo a partir do prefixo
    estruturas = await get_todas_estruturas()
    full_uid = next((e['uid'] for e in estruturas if e['uid'].startswith(uid_prefix)), None)
    
    if not full_uid:
        await call.message.answer("❌ Estrutura não encontrada.")
        return

    lote = await get_lote_por_estrutura(full_uid)

    estado_chat[chat_id] = {
        "step": "agua_data",
        "estrutura_uid": full_uid,
        "tipo_exploracao_id": tipo_id,
        "lote": lote
    }

    tipo_msg = "Piscicultura (Limnologia)" if tipo_id == 1 else "Consumo Animal"
    await call.message.answer(f"📍 {tipo_msg}\nLote {lote}\nData da coleta (DD/MM/AA) [vazio = Hoje]:")
    await call.answer()

# ==========================
# FLUXO: BIOMETRIA
# ==========================

async def cmd_biometria(message: Message):
    chat_id = message.chat.id
    estruturas = await get_estruturas_ativas()
    if not estruturas:
        await message.answer("⚠️ Nenhuma estrutura com lote ativo. Use /novo_lote.")
        return
    kb = InlineKeyboardBuilder()
    for e in estruturas:
        label = f"{e['propriedade']} - {e['nome']}"
        kb.button(text=label, callback_data=f"bio_uid:{e['uid'][:16]}")
    kb.adjust(1)
    estado_chat[chat_id] = {"step": "bio_estrutura"}
    await message.answer("--- Lançar Biometria ---\nEscolha a estrutura:", reply_markup=kb.as_markup())

async def callback_bio_uid(call: CallbackQuery):
    chat_id = call.message.chat.id
    uid_prefix = call.data.split(":")[1]
    
    estruturas = await get_todas_estruturas()
    full_uid = next((e['uid'] for e in estruturas if e['uid'].startswith(uid_prefix)), None)
    
    if not full_uid:
        await call.message.answer("❌ Estrutura não encontrada.")
        return

    lote = await get_lote_por_estrutura(full_uid)
    estado_chat[chat_id] = {"step": "bio_data", "estrutura_uid": full_uid, "lote": lote}
    await call.message.answer(f"📊 Lote {lote}\nData (DD/MM/AA) [vazio = Hoje]:")
    await call.answer()

async def callback_bio_loop(call: CallbackQuery):
    chat_id = call.message.chat.id
    uid_prefix = call.data.split(":")[1]
    
    # Busca dados anteriores para manter o contexto
    estruturas = await get_todas_estruturas()
    full_uid = next((e['uid'] for e in estruturas if e['uid'].startswith(uid_prefix)), None)
    
    if not full_uid:
        await call.message.answer("❌ Estrutura não encontrada.")
        return

    lote = await get_lote_por_estrutura(full_uid)
    
    # Reinicia o fluxo direto na data, mas mantendo a estrutura
    estado_chat[chat_id] = {
        "step": "bio_data", 
        "estrutura_uid": full_uid, 
        "lote": lote
    }
    await call.message.answer(f"🔄 Novo lançamento para Lote {lote}\nData (DD/MM/AA) [vazio = Hoje]:")
    await call.answer()

async def callback_bio_finish(call: CallbackQuery):
    chat_id = call.message.chat.id
    estado_chat.pop(chat_id, None)
    await call.message.answer("✅ Processo de biometria finalizado.")
    await call.answer()

# ==========================
# FLUXO: LOTE (NOVO / FECHAR)
# ==========================

async def cmd_novo_lote(message: Message):
    chat_id = message.chat.id
    estruturas = await get_todas_estruturas()
    kb = InlineKeyboardBuilder()
    for e in estruturas:
        label = f"{e['propriedade']} - {e['nome']}"
        kb.button(text=label, callback_data=f"nl_uid:{e['uid'][:16]}")
    kb.adjust(1)
    estado_chat[chat_id] = {"step": "nl_estrutura"}
    await message.answer("--- Iniciar Novo Lote ---\nEscolha a estrutura:", reply_markup=kb.as_markup())

async def callback_novo_lote_uid(call: CallbackQuery):
    chat_id = call.message.chat.id
    uid_prefix = call.data.split(":")[1]
    
    estruturas = await get_todas_estruturas()
    full_uid = next((e['uid'] for e in estruturas if e['uid'].startswith(uid_prefix)), None)
    
    if not full_uid:
        await call.message.answer("❌ Estrutura não encontrada.")
        return

    lote_ativo = await get_lote_por_estrutura(full_uid)
    if lote_ativo:
        await call.message.answer(f"⚠️ Esta estrutura já possui o Lote {lote_ativo} ativo.")
        estado_chat.pop(chat_id, None)
    else:
        estado_chat[chat_id] = {"step": "nl_lote_nome", "estrutura_uid": full_uid}
        await call.message.answer("Digite a Identificação do Lote (ex: 2024/01):")
    await call.answer()

async def cmd_fechar_lote(message: Message):
    chat_id = message.chat.id
    estruturas = await get_estruturas_ativas()
    if not estruturas:
        await message.answer("⚠️ Nenhuma estrutura com lote ativo para fechar.")
        return
    kb = InlineKeyboardBuilder()
    for e in estruturas:
        label = f"{e['propriedade']} - {e['nome']}"
        kb.button(text=label, callback_data=f"fl_uid:{e['uid'][:16]}")
    kb.adjust(1)
    estado_chat[chat_id] = {"step": "fl_estrutura"}
    await message.answer("--- Fechar Lote ---\nEscolha a estrutura:", reply_markup=kb.as_markup())

async def callback_fechar_lote_uid(call: CallbackQuery):
    chat_id = call.message.chat.id
    uid_prefix = call.data.split(":")[1]
    
    estruturas = await get_todas_estruturas()
    full_uid = next((e['uid'] for e in estruturas if e['uid'].startswith(uid_prefix)), None)
    
    if not full_uid:
        await call.message.answer("❌ Estrutura não encontrada.")
        return

    lote = await get_lote_por_estrutura(full_uid)
    estado_chat[chat_id] = {"step": "fl_data", "estrutura_uid": full_uid, "lote": lote}
    await call.message.answer(f">> Fechar Lote {lote}\nData Final (DD/MM/AA) [vazio = Hoje]:")
    await call.answer()

# ==========================
# MÁQUINA DE ESTADOS (MENSAGENS TEXTO)
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
        # --- FLUXO: QUALIDADE ÁGUA ---
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

        # --- FLUXO: BIOMETRIA ---
        elif step == "bio_data":
            estado["data_bio"] = parse_data_br(texto)
            estado["step"] = "bio_qtd"
            await message.answer("Quantidade (Estoque atual):")
        elif step == "bio_qtd":
            quantidade_atual = parse_int(texto)
            estoque_anterior = await get_ultimo_estoque(estado["estrutura_uid"], estado["lote"])
            mortalidade = estoque_anterior - quantidade_atual
            
            estado["quantidade"] = quantidade_atual
            estado["mortalidade"] = max(0, mortalidade) # Garante que não seja negativa para fins de log, embora o cálculo possa ser flexível
            
            msg_mortalidade = f"📉 Mortalidade calculada: *{mortalidade}* (Anterior: {estoque_anterior} -> Atual: {quantidade_atual})"
            await message.answer(f"{msg_mortalidade}\n\nAgora informe o Peso Médio (g):", parse_mode="Markdown")
            estado["step"] = "bio_peso"
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
            
            kb = InlineKeyboardBuilder()
            kb.button(text="🔄 Novo Lançamento (Mesma Estrutura)", callback_data=f"bio_loop:{estado['estrutura_uid'][:16]}")
            kb.button(text="✅ Finalizar", callback_data="bio_finish")
            kb.adjust(1)
            
            await message.answer("✅ Biometria registrada com sucesso!\nDeseja realizar outro lançamento para esta mesma estrutura?", reply_markup=kb.as_markup())
            # Não removemos o estado ainda, deixamos para o callback ou próximo comando

        # --- FLUXO: LOTE ---
        elif step == "nl_lote_nome":
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

    except Exception as e:
        logger.error(f"Erro no processamento da mensagem: {e}")
        await message.answer(f"⚠️ Erro: {e}")
        estado_chat.pop(chat_id, None)

# ==========================
# MAIN
# ==========================

async def main():
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    # Registro de Comandos de Texto
    dp.message.register(cmd_start, Command("start", "help"))
    dp.message.register(cmd_biometria, Command("biometria", "lancar_biometria"))
    dp.message.register(cmd_agua, Command("agua", "lancar_agua"))
    dp.message.register(cmd_novo_lote, Command("novo_lote"))
    dp.message.register(cmd_fechar_lote, Command("fechar_lote"))
    dp.message.register(cmd_cancel, Command("cancel"))
    
    # Comandos Legados Node-RED (usando decorators acima ou registro explícito)
    # Já registrados via decorators @Dispatcher().message... mas para garantir:
    dp.message.register(handle_oxigenio, Command("oxigenio"))
    dp.message.register(handle_temperatura, Command("temperatura"))
    dp.message.register(handle_ox7d, Command("ox7d"))
    dp.message.register(handle_ox15d, Command("ox15d"))
    dp.message.register(handle_temp7d, Command("temp7d"))
    dp.message.register(handle_previsao, Command("previsao"))
    dp.message.register(handle_backup, Command("backup"))

    # Registro de Callbacks
    dp.callback_query.register(callback_agua_uid, F.data.startswith("agua_uid:"))
    dp.callback_query.register(callback_bio_uid, F.data.startswith("bio_uid:"))
    dp.callback_query.register(callback_bio_loop, F.data.startswith("bio_loop:"))
    dp.callback_query.register(callback_bio_finish, F.data == "bio_finish")
    dp.callback_query.register(callback_novo_lote_uid, F.data.startswith("nl_uid:"))
    dp.callback_query.register(callback_fechar_lote_uid, F.data.startswith("fl_uid:"))
    
    # Handler Genérico de Mensagens (Máquina de Estados)
    dp.message.register(handle_messages, F.text)

    logger.info("Iniciando Bot Unificado PeixePatelBot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
