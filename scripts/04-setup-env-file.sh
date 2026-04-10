#!/bin/sh
# 04-setup-env-file.sh: Configura o arquivo de variáveis de ambiente .env (POSIX compliant)

set -e

# Resolve caminhos
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_EXAMPLE_FILE="$REPO_ROOT/.env.example"
ENV_FILE="$REPO_ROOT/.env"

echo "--- [04/04] Preparando arquivo de configuração (.env) ---"

if [ ! -f "$ENV_FILE" ]; then
    if [ ! -f "$ENV_EXAMPLE_FILE" ]; then
        echo "ERRO: O arquivo template '$ENV_EXAMPLE_FILE' não foi encontrado."
        exit 1
    fi
    echo "--- Criando arquivo '.env' a partir do template... ---"
    cp "$ENV_EXAMPLE_FILE" "$ENV_FILE"
    echo ""
    echo "------------------------------------------------------------"
    echo "⚠️  IMPORTANTE: O arquivo '$ENV_FILE' foi gerado."
    echo "   Por favor, edite-o agora com suas senhas e tokens."
    echo "------------------------------------------------------------"
else
    echo "--- Arquivo '.env' já existe. Nenhuma ação necessária. ---"
fi

echo "--- Etapa 04 concluída com sucesso! ---"
