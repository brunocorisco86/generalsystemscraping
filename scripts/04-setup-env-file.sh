#!/bin/sh
# 04-setup-env-file.sh: Configura o arquivo de variáveis de ambiente .env (POSIX compliant)

set -e

# Resolve caminhos
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_EXAMPLE_FILE="$REPO_ROOT/.env.example"
ENV_FILE="$REPO_ROOT/.env"

echo "--- [04/06] Preparando arquivo de configuração (.env) ---"

if [ ! -f "$ENV_FILE" ]; then
    if [ ! -f "$ENV_EXAMPLE_FILE" ]; then
        echo "ERRO: O arquivo template '$ENV_EXAMPLE_FILE' não foi encontrado."
        exit 1
    fi
    echo "--- Criando arquivo '.env' a partir do template... ---"
    cp "$ENV_EXAMPLE_FILE" "$ENV_FILE"
    
    # Injeta o PROJECT_ROOT real no arquivo .env
    # Usando o sed para substituir o placeholder pelo caminho absoluto real
    sed -i "s|PROJECT_ROOT=.*|PROJECT_ROOT=\"$REPO_ROOT\"|" "$ENV_FILE"
    
    # Gera uma FLASK_SECRET_KEY segura se o placeholder estiver presente
    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(24))')
    sed -i "s|# FLASK_SECRET_KEY=.*|FLASK_SECRET_KEY=\"$SECRET_KEY\"|" "$ENV_FILE"

    echo "✅ PROJECT_ROOT configurado automaticamente como: $REPO_ROOT"
    echo "✅ FLASK_SECRET_KEY gerada e injetada com segurança."
    echo ""
    echo "------------------------------------------------------------"
    echo "⚠️  IMPORTANTE: O arquivo '$ENV_FILE' foi gerado."
    echo "   Por favor, edite-o agora com suas credenciais:"
    echo "   1. Tokens do Telegram"
    echo "   2. Acessos do Noctua (Scraping)"
    echo "   3. Chaves da API Gemini (IA)"
    echo "   4. Credenciais do Dashboard Web (WEB_ADMIN_USER/PASS)"
    echo "------------------------------------------------------------"
else
    echo "--- Arquivo '.env' já existe. Nenhuma ação necessária. ---"
fi

echo "--- Etapa 04 concluída com sucesso! ---"
