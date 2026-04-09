#!/bin/bash
#
# Script para configurar o ambiente de desenvolvimento em Alpine Linux.
# O .venv é sempre criado na RAIZ do repositório, independente de onde
# o script for chamado.
#

# Abortar em caso de erro
set -e

echo "--- Iniciando configuração do ambiente ---"

# --- Resolve a raiz do repositório ---
# SCRIPT_DIR = pasta onde este script está (scripts/)
# REPO_ROOT   = pasta pai = raiz do repo
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "--- Raiz do repositório detectada: $REPO_ROOT ---"

# --- Variáveis (caminhos absolutos a partir da raiz do repo) ---
VENV_DIR="$REPO_ROOT/.venv"
REQUIREMENTS_FILE="$REPO_ROOT/requirements.txt"
ENV_EXAMPLE_FILE="$REPO_ROOT/.env.example"
ENV_FILE="$REPO_ROOT/.env"

# --- Funções ---
install_alpine_deps() {
    echo "--- Detectado Alpine Linux. Instalando dependências via apk ---"
    apk update

    # build-base: gcc, g++, make e outras ferramentas de compilação
    # python3-dev: arquivos de cabeçalho para compilar módulos Python
    # py3-pip / py3-virtualenv: pip e venv no Alpine
    # postgresql-dev, sqlite-dev: cabeçalhos para psycopg2 e sqlite3
    # libffi-dev: para pacotes Python que usam cffi (cryptography etc.)
    # zlib-dev: compressão
    # util-linux: comandos como uuidgen
    # openblas / openblas-dev: para numpy e scipy
    # freetype, libpng, jpeg, tiff e seus -dev: para matplotlib
    # chromium / chromium-chromedriver: automação web / Selenium
    # ncurses-dev: algumas libs de console
    apk add --no-cache \
        git \
        docker \
        docker-cli-compose \
        python3 \
        py3-pip \
        py3-virtualenv \
        python3-dev \
        build-base \
        postgresql-dev \
        sqlite-dev \
        libffi-dev \
        zlib-dev \
        util-linux \
        openblas \
        openblas-dev \
        freetype \
        freetype-dev \
        libpng \
        libpng-dev \
        jpeg \
        jpeg-dev \
        tiff \
        tiff-dev \
        chromium \
        chromium-chromedriver \
        ncurses-dev

    # Garante que o Docker sobe junto com o sistema
    rc-update add docker boot 2>/dev/null || true
    rc-service docker start 2>/dev/null || true

    echo "--- Dependências do sistema instaladas. ---"
}

# --- Verificação de OS e Instalação de Dependências ---
if [ -f "/etc/os-release" ]; then
    . /etc/os-release
    if [ "$ID" = "alpine" ]; then
        install_alpine_deps
    else
        echo "AVISO: Sistema operacional não é Alpine Linux. Dependências de sistema não instaladas."
        echo "Instale manualmente: git, docker, docker-compose, python3, pip, build-base,"
        echo "postgresql-dev, sqlite-dev, chromium, chromium-chromedriver e libs de desenvolvimento."
    fi
else
    echo "AVISO: Não foi possível determinar o sistema operacional. Dependências não instaladas."
fi

# --- Configurando o ambiente virtual na raiz do repo ---
echo "--- Configurando o ambiente virtual em '$VENV_DIR' ---"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    echo "Ambiente virtual criado em $VENV_DIR."
else
    echo "Ambiente virtual já existe em $VENV_DIR."
fi

# --- Instala dependências Python ---
echo "--- Instalando dependências Python ---"
if [ ! -f "$VENV_DIR/bin/python3" ]; then
    echo "ERRO: python3 não encontrado em $VENV_DIR/bin/python3."
    echo "Por favor, verifique a criação do ambiente virtual."
    exit 1
fi

"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$REQUIREMENTS_FILE"

# --- Verificando arquivo de configuração '.env' ---
echo "--- Verificando arquivo de configuração '.env' ---"
if [ ! -f "$ENV_FILE" ]; then
    echo "Copiando '$ENV_EXAMPLE_FILE' para '$ENV_FILE'..."
    cp "$ENV_EXAMPLE_FILE" "$ENV_FILE"
    echo ""
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    echo "!! IMPORTANTE: Edite o arquivo '$ENV_FILE' com suas        !!"
    echo "!! configurações (tokens de bot, senhas de banco de dados). !!"
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
else
    echo "Arquivo '$ENV_FILE' já existe. Nenhuma ação necessária."
fi

echo ""
echo "✅ Configuração concluída com sucesso!"
echo ""
echo "Para ativar o ambiente virtual, execute a partir da raiz do repo:"
echo "  source .venv/bin/activate"
echo ""
echo "Após configurar o .env, inicie os serviços Docker com:"
echo "  docker compose up -d"
echo ""
echo "Para configurar os cron jobs:"
echo "  bash scripts/setup_cron.sh"
echo ""

exit 0
