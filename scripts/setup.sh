#!/bin/bash
# setup.sh: Script mestre que orquestra as etapas de configuração do ambiente.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "--- Iniciando configuração completa do ambiente ---"

# Garante permissões de execução para as etapas
chmod +x "$SCRIPT_DIR"/01-system-deps.sh
chmod +x "$SCRIPT_DIR"/02-setup-venv.sh
chmod +x "$SCRIPT_DIR"/03-install-python-deps.sh
chmod +x "$SCRIPT_DIR"/04-setup-env-file.sh

# Executa as etapas em ordem
bash "$SCRIPT_DIR"/01-system-deps.sh
bash "$SCRIPT_DIR"/02-setup-venv.sh
bash "$SCRIPT_DIR"/03-install-python-deps.sh
bash "$SCRIPT_DIR"/04-setup-env-file.sh

echo ""
echo "✅ Configuração completa realizada com sucesso!"
echo "Para ativar o ambiente virtual, execute: source .venv/bin/activate"
echo "Para agendar tarefas, execute: bash scripts/setup_cron.sh"
echo ""
