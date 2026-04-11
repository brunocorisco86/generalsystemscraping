#!/bin/sh
# 02-setup-venv.sh: Cria o ambiente virtual na raiz do repositório (POSIX compliant)

set -e

# Resolve a raiz do repositório sem usar extensões bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$REPO_ROOT/.venv"

echo "--- [02/06] Preparando ambiente virtual Python ---"
echo "Destino: $VENV_DIR"

if [ ! -d "$VENV_DIR" ]; then
    echo "--- Criando novo ambiente virtual herdando pacotes do sistema (--system-site-packages)... ---"
    # O uso de --system-site-packages é CRUCIAL no Alpine/Raspberry Pi
    # para usar Matplotlib/Numpy/Scipy pré-compilados e evitar falta de memória.
    python3 -m venv --system-site-packages "$VENV_DIR"
    echo "✅ Ambiente virtual criado com sucesso."
else
    echo "--- Ambiente virtual já existente. Pulando criação. ---"
fi

# Upgrade inicial no pip para evitar alertas e garantir estabilidade
echo "--- Atualizando o gerenciador de pacotes (pip)... ---"
"$VENV_DIR/bin/python3" -m pip install --upgrade pip

echo "--- Etapa 02 concluída com sucesso! ---"
