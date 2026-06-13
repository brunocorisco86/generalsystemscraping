#!/bin/sh
# scripts/15-auto-configure-macs.sh: Script de comissionamento automático de MACs

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python3"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "ERRO: Ambiente virtual não encontrado em $VENV_PYTHON"
    echo "Por favor, execute o setup.sh primeiro."
    exit 1
fi

"$VENV_PYTHON" "$SCRIPT_DIR/15-auto-configure-macs.py"
