import os
import sys
import logging
from typing import Optional
from dotenv import load_dotenv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder  # noqa: E402
from langchain_google_genai import ChatGoogleGenerativeAI  # noqa: E402
from langchain.agents import create_tool_calling_agent, AgentExecutor  # noqa: E402
from src.bots.agent_tools import AGENT_TOOLS  # noqa: E402

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# Criar um arquivo de log específico para as interações da IA
log_dir = os.path.join(project_root, "logs")
os.makedirs(log_dir, exist_ok=True)
agent_log_file = os.path.join(log_dir, "agent_interactions.log")
file_handler = logging.FileHandler(agent_log_file, encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

load_dotenv(os.path.join(project_root, ".env"))

# Configuração do Prompt do Agente
SYSTEM_PROMPT = """Você é um especialista em aquicultura, com foco avançado na criação de tilápias.
Sua função é auxiliar no monitoramento e análise de qualidade de água e dados de biometria.

REGRAS IMPORTANTES:
1. SEMPRE acione a ferramenta 'run_migration' ANTES de realizar consultas de leitura com 'query_postgres'.
2. Conhecimento de Domínio: Quedas de oxigênio (hipóxia) na criação de tilápias são normais e perigosas principalmente:
   - À noite e de madrugada (quando não há incidência solar e o fitoplâncton consome oxigênio em vez de produzir).
   - Em dias com temperatura da água elevada (pois a solubilidade do oxigênio diminui em águas quentes e o metabolismo dos peixes aumenta).
3. Avaliação de Aeradores:
   - O banco de dados possui a coluna 'aeradores_ativos'. Verifique essa informação! Se o sistema já acionou vários aeradores, uma pequena queda pode estar sendo contida.
4. Análise de Falsos Positivos (Outliers) e Intervalo de Confiança:
   - Se o oxigênio cair de forma abrupta de um nível saudável (ex: 5.0 mg/L) direto para perto de 0 ou um número muito anômalo em uma única leitura (quebrando o intervalo de confiança da série temporal recente), muito provavelmente é uma FALHA DE SENSOR (outlier / falso positivo).
   - Se a queda for gradual nas últimas horas e acompanhar as condições climáticas (noite/calor), é um RISCO REAL.
5. Economia de Tokens: Seja extremamente direto e conciso em suas análises. Não forneça longas explicações a menos que solicitado pelo usuário.

Se você estiver analisando um ALERTA de sistema e chegar à conclusão de que é um claro ERRO DE SENSOR (Falso Positivo), sua resposta final deve começar EXATAMENTE com a palavra: FALSO_POSITIVO
Nesse caso, após a palavra, você pode dar uma breve justificativa de 1 linha. Se for um problema real, escreva a notificação de alerta em formato adequado para envio no Telegram.
"""

def get_agent_executor() -> Optional[AgentExecutor]:
    """
    Inicializa o AgentExecutor com suporte a múltiplos modelos do Gemini e fallbacks.
    Tenta contornar erros de 'Model Not Found' ou limites de quota do plano gratuito.
    """
    # Verifica a presença da chave da API do Google
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("Chave do Google Gemini (GOOGLE_API_KEY) não encontrada no .env")
        return None

    try:
        # Nome do modelo primário configurável via .env
        primary_model = os.environ.get("GEMINI_MODEL_NAME", "gemini-flash-latest")
        
        # Lista de modelos para tentativa em caso de erro (fallback) - Atualizada para 2026
        model_options = [
            primary_model,
            "gemini-flash-latest",
            "gemini-2.0-flash",
            "gemini-pro-latest",
            "gemini-2.5-flash"
        ]

        # Remover duplicatas mantendo a ordem de preferência
        unique_models = []
        for m in model_options:
            if m not in unique_models:
                unique_models.append(m)
        
        logger.info(f"Modelos configurados para o Agente: {unique_models}")

        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Criar agentes para cada modelo
        agents = []
        for model_name in unique_models:
            try:
                llm = ChatGoogleGenerativeAI(
                    model=model_name,
                    google_api_key=api_key,
                    temperature=0.2
                )
                # O agente LangChain para o Gemini precisa suportar tool calling
                agent_runnable = create_tool_calling_agent(llm, AGENT_TOOLS, prompt)
                agents.append(agent_runnable)
            except Exception as e:
                logger.warning(f"Não foi possível preparar o agente para o modelo {model_name}: {e}")

        if not agents:
            logger.error("Nenhum modelo do Gemini pôde ser configurado.")
            return None

        # Implementa o mecanismo de fallback: se o primeiro falhar, tenta o próximo
        primary_agent = agents[0]
        if len(agents) > 1:
            agent = primary_agent.with_fallbacks(agents[1:])
        else:
            agent = primary_agent

        return AgentExecutor(agent=agent, tools=AGENT_TOOLS, verbose=False)
    except Exception as e:
        logger.error(f"Erro ao inicializar o Agente IA: {e}")
        return None

async def ask_agent(mensagem: str, chat_id: int) -> str:
    """Função para bater papo livremente com o agente via bot do Telegram."""
    executor = get_agent_executor()
    if not executor:
        return "⚠️ Agente de IA não está disponível (Verifique as configurações e API Key)."
    
    try:
        logger.info("--- NOVA CHAMADA DO AGENTE: CHAT LIVRE ---")
        logger.info(f"MENSAGEM DO USUARIO:\n{mensagem}")
        
        response = await executor.ainvoke({"input": mensagem})
        output = response.get("output", "Sem resposta da IA.")
        
        logger.info(f"RESPOSTA DA IA:\n{output}")
        return output
    except Exception as e:
        logger.error(f"Erro na execução do Agente: {e}", exc_info=True)
        if "404" in str(e) or "not found" in str(e).lower():
            return "⚠️ Erro: O modelo de IA não foi encontrado. Por favor, verifique a variável GEMINI_MODEL_NAME ou a disponibilidade do modelo no seu plano."
        return f"⚠️ Erro ao processar sua solicitação pela IA: {str(e)}"

async def analyze_alert_data(tanque: str, oxigenio: float, temperatura: float) -> Optional[str]:
    """
    Acionada pelo alert_check.py para analisar o contexto do tanque antes de disparar a notificação.
    Retorna a mensagem de alerta, ou None se for um falso positivo detectado pela IA.
    """
    executor = get_agent_executor()
    if not executor:
        # Se a IA estiver offline, fallback para um alerta padrão para segurança
        return (
            f"🚨 *ALERTA CRÍTICO (Fallback IA Indisponível)* 🚨\n\n"
            f"📍 Tanque: *{tanque}*\n"
            f"🔴 Oxigênio: *{oxigenio} Mg/L* 🔴\n"
            f"🌡️ Temp: {temperatura}°C"
        )
        
    input_msg = (
        f"ALERTA DETECTADO: O tanque '{tanque}' registrou uma leitura de {oxigenio} Mg/L de oxigênio e {temperatura}°C de temperatura agora.\n"
        f"Por favor, rode a migração e em seguida faça um SELECT das últimas 10 leituras deste tanque ordenadas por id DESC para ver o histórico recente.\n"
        f"Analise se esta leitura é uma queda real (necessidade de aeradores) ou um possível falso positivo do sensor de acordo com as regras estabelecidas.\n"
        f"Preste atenção ao intervalo de confiança da série temporal e se a coluna 'aeradores_ativos' indica que já estamos compensando o problema.\n"
        f"Lembre-se: se for falso positivo, comece com FALSO_POSITIVO."
    )

    try:
        logger.info("--- NOVA CHAMADA DO AGENTE: ALERTA ---")
        logger.info(f"PROMPT ENVIADO:\n{input_msg}")
        
        response = await executor.ainvoke({"input": input_msg})
        output = response.get("output", "")
        
        logger.info(f"RESPOSTA DA IA:\n{output}")
        
        # Se a IA decidiu que é falso positivo, não enviamos notificação
        if output.strip().startswith("FALSO_POSITIVO"):
            logger.info(f"Agente suprimiu um alerta para o {tanque}. Justificativa: {output}")
            return None
            
        return output
    except Exception as e:
        logger.error(f"Erro no Agente de Alerta: {e}")
        # Fallback de segurança em caso de erro na LLM
        return f"🚨 *ALERTA CRÍTICO (Erro na IA)* 🚨\nTanque: {tanque} | O2: {oxigenio} Mg/L"

def analyze_evening_report_sync(summary_data: str, plot_data_csv: str) -> str:
    """
    Função síncrona para ser chamada por jobs em background (como evening_report.py).
    Gera um parecer especialista sobre as condições da água antes do período noturno.
    """
    executor = get_agent_executor()
    if not executor:
        return "⚠️ Parecer do Especialista Indisponível (IA Offline)."
    
    prompt = (
        f"Você é o especialista em aquicultura responsável por analisar o fechamento do dia (relatório da tarde).\n"
        f"Abaixo está o resumo dos níveis de oxigênio e temperatura dos tanques de tilápias no fim da tarde:\n"
        f"{summary_data}\n\n"
        f"Para uma análise mais profunda, aqui estão os dados brutos da série temporal em formato CSV:\n"
        f"```csv\n{plot_data_csv}\n```\n\n"
        f"Por favor, escreva um BREVE parecer (máximo 3 frases) focado no risco de hipóxia para a noite e madrugada que se aproximam. "
        f"Avalie a combinação de temperatura e nível de O2 atual para recomendar ou não atenção redobrada aos aeradores.\n"
        f"Lembre-se da economia de tokens: seja direto e prático."
    )
    try:
        logger.info("--- NOVA CHAMADA DO AGENTE: RELATORIO DA TARDE ---")
        # Log do prompt omitido para economizar espaço no log se o CSV for muito grande
        logger.info("Prompt enviado com dados CSV.")
        
        response = executor.invoke({"input": prompt})
        output = response.get("output", "")
        
        logger.info(f"RESPOSTA DA IA:\n{output}")
        return output
    except Exception as e:
        logger.error(f"Erro ao gerar parecer noturno: {e}", exc_info=True)
        return "⚠️ Parecer do Especialista Indisponível no momento."

def analyze_nightly_report_sync(start_time_str: str, end_time_str: str, summary_data: str, plot_data_csv: str) -> str:
    """
    Função síncrona para o relatório da manhã (nightly_report.py).
    O Agente recebe o resumo e os dados brutos utilizados no gráfico.
    """
    executor = get_agent_executor()
    if not executor:
        return "⚠️ Parecer do Especialista Indisponível (IA Offline)."
    
    prompt = (
        f"Você é o especialista em aquicultura responsável por avaliar como os tanques passaram a noite.\n"
        f"O período noturno avaliado foi de {start_time_str} até {end_time_str}.\n"
        f"Aqui está um resumo estatístico pré-calculado pelo sistema:\n{summary_data}\n\n"
        f"Aqui estão os dados brutos da série temporal utilizados para gerar o gráfico (em CSV):\n"
        f"```csv\n{plot_data_csv}\n```\n\n"
        f"Sua tarefa: Faça uma avaliação geral de como foi a noite observando a série temporal. "
        f"Como você possui os dados CSV, avalie as curvas de cada tanque. "
        f"Forneça um parecer conciso (máximo 4 frases) resumindo se a noite foi segura e se alguma "
        f"estrutura apresentou risco contínuo ou anomalias."
    )
    try:
        logger.info("--- NOVA CHAMADA DO AGENTE: RELATORIO DA NOITE ---")
        logger.info("Prompt enviado com dados CSV.")
        
        response = executor.invoke({"input": prompt})
        output = response.get("output", "")
        
        logger.info(f"RESPOSTA DA IA:\n{output}")
        return output
    except Exception as e:
        logger.error(f"Erro ao gerar parecer da noite: {e}", exc_info=True)
        return "⚠️ Parecer do Especialista Indisponível no momento."

def analyze_custom_report_sync(report_title: str, summary_data: str, plot_data_csv: str) -> str:
    """
    Função síncrona genérica para uso nos scripts dinâmicos da pasta src/reports/.
    Avalia a métrica de acordo com o título (O2, Temperatura, Peso, etc).
    """
    executor = get_agent_executor()
    if not executor:
        return "⚠️ Parecer do Especialista Indisponível (IA Offline)."
    
    prompt = (
        f"Você é o especialista em aquicultura responsável por analisar o seguinte relatório gerado sob demanda: {report_title}\n\n"
        f"Abaixo está o resumo estatístico pré-calculado:\n"
        f"{summary_data}\n\n"
        f"Para uma análise visual precisa, aqui estão os dados brutos da série temporal utilizados para o gráfico (em CSV):\n"
        f"```csv\n{plot_data_csv}\n```\n\n"
        f"Sua tarefa: Faça uma avaliação da série temporal. Se for relatório de oxigênio ou temperatura, avalie tendências "
        f"de risco, constância e picos. Se for relatório de curva de peso (biometria), avalie o crescimento e sugira "
        f"ajustes nutricionais ou de manejo se a curva real estiver se distanciando da curva teórica.\n"
        f"Forneça um parecer MUITO conciso (máximo 4 frases) apontando sua visão especialista."
    )
    try:
        logger.info(f"--- NOVA CHAMADA DO AGENTE: RELATORIO CUSTOM ({report_title}) ---")
        logger.info("Prompt enviado com dados CSV.")
        
        response = executor.invoke({"input": prompt})
        output = response.get("output", "")
        
        logger.info(f"RESPOSTA DA IA:\n{output}")
        return output
    except Exception as e:
        logger.error(f"Erro ao gerar parecer para o relatório '{report_title}': {e}", exc_info=True)
        if "404" in str(e) or "not found" in str(e).lower():
            return "⚠️ Parecer Indisponível: O modelo de IA configurado não foi encontrado (Erro 404)."
        return "⚠️ Parecer do Especialista Indisponível no momento."
