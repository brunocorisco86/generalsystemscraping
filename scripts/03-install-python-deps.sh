#!/bin/bash
# 03-install-python-deps.sh: Instala as dependências Python no .venv

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$REPO_ROOT/.venv"
REQUIREMENTS_FILE="$REPO_ROOT/requirements.txt"

if [ ! -f "$VENV_DIR/bin/pip" ]; then
    echo "ERRO: Ambiente virtual não encontrado em '$VENV_DIR'."
    exit 1
fi

if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo "ERRO: '$REQUIREMENTS_FILE' não encontrado."
    exit 1
fi

echo "--- [03/04] Instalando dependências Python via pip ---"

"$VENV_DIR/bin/pip" install -r "$REQUIREMENTS_FILE"

echo "--- Etapa 03 concluída com sucesso! ---"
