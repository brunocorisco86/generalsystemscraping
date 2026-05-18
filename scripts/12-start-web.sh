#!/bin/sh
# 12-start-web.sh: Inicia o painel de controle web da piscicultura

set -e

# Resolve a raiz do repositório
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "--- [12] Iniciando Painel Web (Dashboard) ---"

# 1. Verifica ambiente virtual
VENV_PYTHON="$REPO_ROOT/.venv/bin/python3"
if [ ! -f "$VENV_PYTHON" ]; then
    echo "ERRO: Ambiente virtual não encontrado em $REPO_ROOT/.venv"
    echo "Por favor, execute scripts/02-setup-venv.sh primeiro."
    exit 1
fi

# 2. Inicia o Flask
echo "Acesse o painel em: http://localhost:5000 (ou o IP do Raspberry)"
cd "$REPO_ROOT"
export PYTHONPATH="$REPO_ROOT"
"$VENV_PYTHON" src/web/app.py
