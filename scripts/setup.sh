#!/bin/bash
#
# Script para configurar o ambiente de desenvolvimento em Alpine Linux.
#

# Abortar em caso de erro
set -e

echo "--- Iniciando configuração do ambiente ---"

# --- Variáveis ---
VENV_DIR=".venv"
REQUIREMENTS_FILE="requirements.txt"
ENV_EXAMPLE_FILE=".env.example"
ENV_FILE=".env"

# --- Funções ---
install_alpine_deps() {
    echo "--- Detectado Alpine Linux. Instalando dependências via apk ---"
    # Atualiza índices de pacotes
    apk update
    
    # Instala pacotes necessários para desenvolvimento, Docker, Python, etc.
    # build-base: gcc, g++, make e outras ferramentas de compilação
    # python3-dev: arquivos de cabeçalho para compilar módulos Python
    # postgresql-dev, sqlite-dev: cabeçalhos para psycopg2 e sqlite3
    # openjdk17: necessário para alguns drivers Java, pode ser útil
    # libffi-dev: frequentemente necessário para pacilar pacotes Python que usam cffi (cryptography)
    # ncurses-dev: para algumas libs de console
    # zlib-dev: para compressão
    # util-linux: para comandos como `uuidgen`
    # hdf5, hdf5-dev, openblas, openblas-dev: para numpy e scipy
    # freetype, freetype-dev, libpng, libpng-dev, jpeg, jpeg-dev, tiff, tiff-dev: para matplotlib
    apk add --no-cache \
        git \
        docker \
        docker-compose \
        python3 \
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
        ncurses-dev \
        # Fontes para matplotlib, se necessário. Deixar como comentário
        # font-noto-cjk font-freefont-ttf
    
    echo "--- Dependências do sistema instaladas. ---"
}

# --- Verificação de OS e Instalação de Dependências ---
if [ -f "/etc/os-release" ]; then
    . /etc/os-release
    if [ "$ID" = "alpine" ]; then
        install_alpine_deps
    else
        echo "AVISO: Sistema operacional não é Alpine Linux. Não foram instaladas dependências de sistema."
        echo "Por favor, instale 'git', 'docker', 'docker-compose', 'python3-dev', 'build-base', 'postgresql-dev', 'sqlite-dev', 'chromium', 'chromium-chromedriver' e outras libs de desenvolvimento manualmente."
    fi
else
    echo "AVISO: Não foi possível determinar o sistema operacional. Não foram instaladas dependências de sistema."
    echo "Por favor, instale 'git', 'docker', 'docker-compose', 'python3-dev', 'build-base', 'postgresql-dev', 'sqlite-dev', 'chromium', 'chromium-chromedriver' e outras libs de desenvolvimento manualmente."
fi

# --- Configurando o ambiente virtual ---
echo "--- Configurando o ambiente virtual em '$VENV_DIR' ---"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv $VENV_DIR
    echo "Ambiente virtual criado."
else
    echo "Ambiente virtual já existe."
fi

echo "--- Ativando o ambiente virtual e instalando dependências Python ---"
# O source precisa ser executado no contexto do shell do usuário,
# mas para o script, podemos chamar o pip diretamente.
# Verifica se o executável do python do venv existe
if [ ! -f "$VENV_DIR/bin/python3" ]; then
    echo "ERRO: O python do ambiente virtual não foi encontrado em $VENV_DIR/bin/python3."
    echo "Por favor, verifique a criação do ambiente virtual."
    exit 1
fi
$VENV_DIR/bin/pip install --upgrade pip
$VENV_DIR/bin/pip install -r $REQUIREMENTS_FILE

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
echo "Para ativar o ambiente virtual e começar a trabalhar, execute:"
echo "source $VENV_DIR/bin/activate"
echo ""
echo "Após configurar o .env, você pode iniciar os serviços Docker com:"
echo "docker-compose up -d"
echo ""
echo "E configurar os cron jobs com:"
echo "bash scripts/setup_cron.sh"
echo ""

exit 0
