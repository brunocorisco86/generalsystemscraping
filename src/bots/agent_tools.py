import os
import sys
import subprocess
import logging
from langchain.tools import tool

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.services.database import get_postgres_connection  # noqa: E402

logger = logging.getLogger(__name__)

@tool
def run_migration() -> str:
    """
    Aciona o script de migração de dados do SQLite (onde os dados brutos chegam) para o PostgreSQL.
    Você DEVE executar esta ferramenta ANTES de fazer um SELECT no PostgreSQL para garantir que os dados estejam atualizados.
    """
    script_path = os.path.join(project_root, "src", "database", "postgres", "migrate_data.py")
    try:
        python_exe = sys.executable or "python3"
        result = subprocess.run(
            [python_exe, script_path], 
            capture_output=True, 
            text=True,
            check=True
        )
        # O script de migração avisa se houveram novos registros no stdout/stderr.
        output = result.stdout + "\n" + result.stderr
        return f"Migração concluída com sucesso:\n{output}"
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro na migração: {e.stderr}")
        return f"Erro ao rodar migração: {e.stderr}"

@tool
def query_postgres(query_sql: str) -> str:
    """
    Executa uma consulta SELECT de leitura no banco de dados PostgreSQL e retorna os resultados.
    A tabela principal é a 'leituras'. Exemplo de colunas: id, estrutura_uid, nome_estrutura, oxigenio, temperatura, timestamp_site, data_coleta, aeradores_ativos.
    Certifique-se de executar 'run_migration' antes desta ferramenta.
    """
    if not query_sql.strip().upper().startswith("SELECT"):
        return "Erro: Apenas consultas SELECT são permitidas por questões de segurança."

    conn = get_postgres_connection()
    if not conn:
        return "Erro: Não foi possível conectar ao PostgreSQL."

    try:
        cur = conn.cursor()
        cur.execute(query_sql)
        rows = cur.fetchall()
        
        # Obter os nomes das colunas
        col_names = [desc[0] for desc in cur.description]
        
        if not rows:
            return "A consulta foi executada, mas não retornou nenhum resultado."
        
        # Formatar como string (limite de resultados para não estourar o contexto)
        limit = 50
        result_str = " | ".join(col_names) + "\n"
        result_str += "-" * 50 + "\n"
        for row in rows[:limit]:
            result_str += " | ".join(str(val) for val in row) + "\n"
            
        if len(rows) > limit:
            result_str += f"\n... (Mostrando apenas os primeiros {limit} registros de {len(rows)} totais)."
            
        return result_str
    except Exception as e:
        return f"Erro ao executar a consulta SQL: {e}"
    finally:
        if conn:
            conn.close()

@tool
def execute_python_report(script_name: str) -> str:
    """
    Executa um script Python da pasta src/reports/ e retorna o resultado no terminal.
    Os scripts disponíveis normalmente geram relatórios ou gráficos.
    Exemplos: 'bot_query_oxygen.py', 'bot_query_temp.py'.
    O parâmetro deve ser o nome exato do arquivo.
    """
    script_path = os.path.join(project_root, "src", "reports", script_name)
    if not os.path.exists(script_path):
        return f"Erro: O script {script_name} não foi encontrado em src/reports/."
    
    try:
        python_exe = sys.executable or "python3"
        result = subprocess.run(
            [python_exe, script_path, "0"], # "0" é o chat_id dummy para o script não quebrar se esperar
            capture_output=True, 
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Erro ao rodar relatório {script_name}: {e.stderr}"

# Lista de ferramentas que serão passadas para o agente
AGENT_TOOLS = [run_migration, query_postgres, execute_python_report]
