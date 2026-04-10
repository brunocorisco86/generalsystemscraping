#!/bin/bash
# 02-setup-venv.sh: Cria o ambiente virtual na raiz do repositório

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$REPO_ROOT/.venv"

echo "--- [02/04] Configurando o ambiente virtual em '$VENV_DIR' ---"

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    echo "Ambiente virtual criado em $VENV_DIR."
else
    echo "Ambiente virtual já existe."
fi

# Upgrade inicial no pip
"$VENV_DIR/bin/python3" -m pip install --upgrade pip

echo "--- Etapa 02 concluída com sucesso! ---"
