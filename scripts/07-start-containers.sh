#!/bin/sh
# 07-start-containers.sh: Inicializa os serviços Docker (Postgres e Bots)

set -e

# Resolve a raiz do repositório
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"

echo "--- [07] Inicializando Serviços Docker ---"

# 1. Verifica se o Docker está instalado
if ! command -v docker >/dev/null 2>&1; then
    echo "ERRO: Docker não encontrado. Por favor, instale o Docker primeiro."
    exit 1
fi

# 2. Verifica se o Docker Compose está instalado (v2 ou v1)
DOCKER_COMPOSE="docker compose"
if ! $DOCKER_COMPOSE version >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker-compose"
    if ! $DOCKER_COMPOSE version >/dev/null 2>&1; then
        echo "ERRO: Docker Compose não encontrado."
        exit 1
    fi
fi

# 3. Verifica se o arquivo .env existe
if [ ! -f "$ENV_FILE" ]; then
    echo "ERRO: Arquivo .env não encontrado em $REPO_ROOT."
    echo "Por favor, execute o setup.sh ou configure seu .env antes de iniciar os containers."
    exit 1
fi

# 4. Inicia os containers
echo "--- Subindo containers (Postgres, Biometria, Qualidade da Água)... ---"
cd "$REPO_ROOT"
$DOCKER_COMPOSE up -d --build

echo "--- Inicializando/Validando Schema do PostgreSQL ---"
VENV_PYTHON="$REPO_ROOT/.venv/bin/python3"
PYTHON_CMD="python3"
if [ -f "$VENV_PYTHON" ]; then
    PYTHON_CMD="$VENV_PYTHON"
fi

# 1. Cria as tabelas no Postgres
"$PYTHON_CMD" -m src.database.postgres.init_db

# 2. Cria as tabelas no SQLite local
if [ -f "$REPO_ROOT/scripts/05-init-sqlite-db.py" ]; then
    echo "--- Inicializando Schema do SQLite Local ---"
    "$PYTHON_CMD" "$REPO_ROOT/scripts/05-init-sqlite-db.py"
fi

# 3. Popula dados base (Propriedades, Estruturas) em ambos
if [ -f "$REPO_ROOT/scripts/08-populate-initial-data.py" ]; then
    echo "--- Populando dados iniciais (Propriedades/Estruturas) ---"
    "$PYTHON_CMD" "$REPO_ROOT/scripts/08-populate-initial-data.py"
fi

echo ""
echo "✅ Serviços iniciados e Banco de Dados configurado!"
echo "Para verificar o status: docker compose ps"
echo "Para ver logs: docker compose logs -f"
