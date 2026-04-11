#!/bin/sh
# 02-setup-venv.sh: Cria o ambiente virtual na raiz do repositório (POSIX compliant)

set -e

# Resolve a raiz do repositório sem usar extensões bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$REPO_ROOT/.venv"

echo "--- [02/05] Preparando ambiente virtual Python ---"
echo "Destino: $VENV_DIR"

if [ ! -d "$VENV_DIR" ]; then
    echo "--- Criando novo ambiente virtual com acesso aos pacotes de sistema... ---"
    python3 -m venv --system-site-packages "$VENV_DIR"
    echo "✅ Ambiente virtual criado com sucesso."
else
    echo "--- Ambiente virtual já existente. Pulando criação. ---"
fi

# Upgrade inicial no pip
echo "--- Atualizando o gerenciador de pacotes (pip)... ---"
"$VENV_DIR/bin/python3" -m pip install --upgrade pip

# --- Configuração do arquivo .env ---
ENV_FILE="$REPO_ROOT/.env"
ENV_EXAMPLE="$REPO_ROOT/.env.example"

echo "--- Configurando variáveis de ambiente (.env) ---"
if [ ! -f "$ENV_FILE" ]; then
    if [ -f "$ENV_EXAMPLE" ]; then
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        # Injeta o PROJECT_ROOT real
        sed -i "s|PROJECT_ROOT=.*|PROJECT_ROOT=\"$REPO_ROOT\"|" "$ENV_FILE"
        echo "✅ Arquivo .env criado e PROJECT_ROOT configurado: $REPO_ROOT"
    else
        echo "⚠️  AVISO: .env.example não encontrado. Pulei a criação do .env."
    fi
else
    # Se o arquivo já existe, apenas garante que o PROJECT_ROOT esteja correto (opcional)
    echo "--- Arquivo .env já existe. ---"
fi

echo "--- Etapa 02 concluída com sucesso! ---"
