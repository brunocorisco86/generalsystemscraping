#!/bin/sh
# 03-install-python-deps.sh: Instala as dependências Python no .venv (POSIX compliant)

set -e

# Resolve caminhos de forma segura e compatível
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$REPO_ROOT/.venv"
REQUIREMENTS_FILE="$REPO_ROOT/requirements.txt"

echo "--- [03/06] Iniciando instalação de bibliotecas Python ---"

if [ ! -f "$VENV_DIR/bin/pip" ]; then
    echo "ERRO: O ambiente virtual em '$VENV_DIR' não foi encontrado. Execute a etapa 02 primeiro."
    exit 1
fi

if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo "ERRO: O arquivo '$REQUIREMENTS_FILE' não existe na raiz do projeto."
    exit 1
fi

echo "--- Lendo arquivo de dependências: $REQUIREMENTS_FILE ---"
echo "--- Isso pode levar alguns minutos, dependendo do seu hardware... ---"

# Usa o pip do ambiente virtual
"$VENV_DIR/bin/pip" install -r "$REQUIREMENTS_FILE"

echo "--- Etapa 03 concluída com sucesso! ---"
