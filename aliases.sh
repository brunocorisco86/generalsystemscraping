#!/bin/bash
# aliases.sh: Atalhos para as etapas de configuração

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

alias setup-sys="bash $REPO_ROOT/scripts/01-system-deps.sh"
alias setup-venv="bash $REPO_ROOT/scripts/02-setup-venv.sh"
alias setup-py="bash $REPO_ROOT/scripts/03-install-python-deps.sh"
alias setup-env="bash $REPO_ROOT/scripts/04-setup-env-file.sh"
alias setup-all="bash $REPO_ROOT/scripts/setup.sh"

echo "--- Aliases carregados! ---"
echo "Comandos disponíveis: setup-sys, setup-venv, setup-py, setup-env, setup-all"
