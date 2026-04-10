#!/bin/bash
# 04-setup-env-file.sh: Cria o arquivo .env se ele não existir

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_EXAMPLE_FILE="$REPO_ROOT/.env.example"
ENV_FILE="$REPO_ROOT/.env"

echo "--- [04/04] Verificando arquivo de configuração '.env' ---"

if [ ! -f "$ENV_FILE" ]; then
    if [ ! -f "$ENV_EXAMPLE_FILE" ]; then
        echo "ERRO: '$ENV_EXAMPLE_FILE' não encontrado."
        exit 1
    fi
    echo "Copiando '$ENV_EXAMPLE_FILE' para '$ENV_FILE'..."
    cp "$ENV_EXAMPLE_FILE" "$ENV_FILE"
    echo ""
    echo "IMPORTANTE: Edite o arquivo '$ENV_FILE' com suas configurações."
else
    echo "Arquivo '$ENV_FILE' já existe. Nenhuma ação necessária."
fi

echo "--- Etapa 04 concluída com sucesso! ---"
