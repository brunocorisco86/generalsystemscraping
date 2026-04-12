#!/bin/sh
# 01-system-deps.sh: Instala dependências do sistema de forma cadenciada e compatível com POSIX (sh/ash)

set -e

echo "--- [01/06] Iniciando verificação cautelosa de dependências ---"

# Detecta se precisa de sudo ou se já é root
SUDO=""
if [ "$(id -u)" -ne 0 ]; then
    if command -v sudo >/dev/null 2>&1; then
        SUDO="sudo"
    else
        echo "ERRO: Usuário não é root e 'sudo' não foi encontrado."
        exit 1
    fi
fi

# Função para instalar pacotes um a um com pausa para arrefecimento (Compatível com POSIX sh)
install_sequentially() {
    manager=$1
    shift
    packages=$@
    
    # Conta total de pacotes
    total=0
    for pkg in $packages; do total=$((total + 1)); done
    
    count=1
    for pkg in $packages; do
        echo "[$count/$total] Instalando: $pkg..."
        
        if [ "$manager" = "apk" ]; then
            $SUDO apk add --no-cache "$pkg"
        else
            $SUDO apt-get install -y "$pkg"
        fi

        echo "✅ $pkg instalado. Pausando 1 segundo para arrefecimento..."
        sleep 1
        count=$((count + 1))
    done
}

# Definição das listas de dependências como strings (POSIX compatible)
# Adicionadas bibliotecas py3- para evitar compilação em hardware limitado
ALPINE_DEPS="git docker docker-cli-compose python3 py3-pip py3-virtualenv python3-dev build-base postgresql-dev sqlite-dev libffi-dev zlib-dev util-linux openblas openblas-dev freetype freetype-dev libpng libpng-dev jpeg jpeg-dev tiff tiff-dev chromium chromium-chromedriver ncurses-dev py3-matplotlib py3-numpy py3-pandas py3-scipy py3-requests py3-sqlalchemy py3-psycopg2 py3-dotenv py3-seaborn py3-openpyxl"

DEBIAN_DEPS="git docker docker-cli-compose python3 py3-pip py3-virtualenv python3-dev build-base postgresql-dev sqlite-dev libffi-dev zlib-dev util-linux openblas openblas-dev freetype freetype-dev libpng libpng-dev jpeg jpeg-dev tiff tiff-dev chromium chromium-chromedriver ncurses-dev py3-matplotlib py3-numpy py3-pandas py3-scipy py3-requests py3-sqlalchemy py3-psycopg2 py3-dotenv py3-seaborn py3-openpyxl"

if [ -f "/etc/os-release" ]; then
    . /etc/os-release
    case "$ID" in
        alpine)
            echo "--- Detectado Alpine Linux. Iniciando instalação sequencial via APK ---"
            $SUDO apk update
            install_sequentially "apk" $ALPINE_DEPS
            
            echo "--- Configurando serviços de fundo ---"
            $SUDO rc-update add docker boot 2>/dev/null || true
            $SUDO rc-service docker start 2>/dev/null || true
            ;;
        pop|ubuntu|debian)
            echo "--- Detectado sistema Debian-based. Iniciando instalação sequencial via APT ---"
            $SUDO apt-get update
            install_sequentially "apt" $DEBIAN_DEPS
            
            echo "--- Configurando serviços de fundo ---"
            $SUDO systemctl enable docker 2>/dev/null || true
            $SUDO systemctl start docker 2>/dev/null || true
            ;;
        *)
            echo "AVISO: Sistema '$ID' não suportado automaticamente."
            exit 1
            ;;
    esac
else
    echo "ERRO: Não foi possível detectar o sistema operacional."
    exit 1
fi

echo "--- Etapa 01 concluída com sucesso! Hardware preservado. ---"
