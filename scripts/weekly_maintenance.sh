#!/bin/sh
# weekly_maintenance.sh: Rotina de manutenção semanal para sincronização de MACs e atualização de bancos de dados.

set -e

# Resolve a raiz do repositório
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"

echo "========================================================="
echo "   [MANUTENÇÃO] Iniciando Rotina de Manutenção Semanal   "
echo "========================================================="
echo "Data: $(date)"
echo "Projeto: $REPO_ROOT"

# 1. Verifica arquivo .env
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ ERRO: Arquivo .env não encontrado em $ENV_FILE"
    exit 1
fi

# 2. Carrega a variável PROJECT_ROOT e remove aspas extras
PROJECT_ROOT=$(grep -v '^#' "$ENV_FILE" | grep 'PROJECT_ROOT' | cut -d '=' -f2- | sed 's/^[ 	]*//;s/[ 	]*$//' | tr -d '"' | tr -d "'")
if [ -z "$PROJECT_ROOT" ]; then
    PROJECT_ROOT="$REPO_ROOT"
fi
PROJECT_ROOT=$(echo "$PROJECT_ROOT" | sed 's|/*$||')

VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python3"
if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ ERRO: Ambiente virtual não encontrado em $VENV_PYTHON"
    exit 1
fi

cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT"

# Exporta variáveis de ambiente de banco para fallback local seguro (aponta para a porta exposta pelo Docker no host)
export PG_HOST="localhost"
export PG_PORT="5432"

# 3. Executa o Comissionamento automático de MACs a partir do site da Noctua-IoT
echo "\n--- [Manutenção 1/5] Atualizando MACs do Site para o .env ---"
"$VENV_PYTHON" scripts/15-auto-configure-macs.py

# 4. Inicializa os schemas caso alguma tabela esteja faltando
echo "\n--- [Manutenção 2/5] Inicializando/Validando Schemas SQLite e Postgres ---"
CONTAINER_RUNNING=0
if command -v docker >/dev/null 2>&1; then
    if docker ps --filter "name=peixe_patel_bot" --filter "status=running" | grep peixe_patel_bot >/dev/null 2>&1; then
        CONTAINER_RUNNING=1
    fi
fi

# Inicializa o SQLite
"$VENV_PYTHON" scripts/05-init-sqlite-db.py

# Inicializa o Postgres
if [ $CONTAINER_RUNNING -eq 1 ]; then
    echo "Inicializando Postgres via container peixe_patel_bot..."
    if ! docker exec peixe_patel_bot python3 -m src.database.postgres.init_db; then
        echo "⚠️  Aviso: Falha ao rodar no container. Tentando localmente..."
        "$VENV_PYTHON" src/database/postgres/init_db.py
    fi
else
    echo "Inicializando Postgres localmente..."
    "$VENV_PYTHON" src/database/postgres/init_db.py
fi

# 5. Popula as novas estruturas e dados iniciais nos bancos (SQLite e Postgres)
echo "\n--- [Manutenção 3/5] Cadastrando Estruturas no SQLite/Postgres ---"
if [ $CONTAINER_RUNNING -eq 1 ]; then
    echo "Executando população cadastral via container peixe_patel_bot..."
    if ! docker exec peixe_patel_bot python3 scripts/08-populate-initial-data.py; then
        echo "⚠️  Aviso: Falha ao rodar no container. Tentando localmente..."
        "$VENV_PYTHON" scripts/08-populate-initial-data.py
    fi
else
    echo "Executando população cadastral localmente..."
    "$VENV_PYTHON" scripts/08-populate-initial-data.py
fi

# 6. Sincroniza dados históricos (SQLite -> Postgres)
echo "\n--- [Manutenção 4/5] Sincronizando dados SQLite -> Postgres ---"
if [ $CONTAINER_RUNNING -eq 1 ]; then
    echo "Executando migração de dados via container peixe_patel_bot..."
    if ! docker exec peixe_patel_bot python3 -m src.database.postgres.migrate_data; then
        echo "⚠️  Aviso: Falha ao rodar no container. Tentando localmente..."
        "$VENV_PYTHON" -m src.database.postgres.migrate_data
    fi
else
    echo "Executando migração de dados localmente..."
    "$VENV_PYTHON" -m src.database.postgres.migrate_data
fi

# 7. Limpa logs antigos para poupar espaço
echo "\n--- [Manutenção 5/5] Limpando arquivos de logs antigos (> 7 dias) ---"
if [ -f "$PROJECT_ROOT/scripts/09-cleanup-logs.sh" ]; then
    sh "$PROJECT_ROOT/scripts/09-cleanup-logs.sh" 7
fi

echo "\n========================================================="
echo "     ✅ Rotina de Manutenção Concluída com Sucesso!     "
echo "========================================================="
