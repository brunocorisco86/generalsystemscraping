#!/bin/bash
# 01-system-deps.sh: Instala dependências do sistema detectando o OS (Alpine ou Debian/Ubuntu)

set -e

echo "--- [01/04] Verificando dependências do sistema ---"

# Função para Alpine Linux
install_alpine() {
    echo "--- Detectado Alpine Linux. Instalando via apk ---"
    sudo apk update
    sudo apk add --no-cache \
        git docker docker-cli-compose python3 py3-pip py3-virtualenv \
        python3-dev build-base postgresql-dev sqlite-dev libffi-dev \
        zlib-dev util-linux openblas openblas-dev freetype freetype-dev \
        libpng libpng-dev jpeg jpeg-dev tiff tiff-dev chromium \
        chromium-chromedriver ncurses-dev py3-matplotlib
    
    sudo rc-update add docker boot 2>/dev/null || true
    sudo rc-service docker start 2>/dev/null || true
}

# Função para Debian/Ubuntu/Pop!_OS
install_debian() {
    echo "--- Detectado sistema baseado em Debian/Ubuntu. Instalando via apt ---"
    sudo apt-get update
    sudo apt-get install -y \
        git docker.io docker-compose python3 python3-pip python3-venv \
        python3-dev build-essential libpq-dev libsqlite3-dev libffi-dev \
        zlib1g-dev libopenblas-dev libfreetype6-dev libpng-dev \
        libjpeg-dev libtiff-dev chromium-browser chromium-chromedriver \
        libncurses5-dev
    
    sudo systemctl enable docker 2>/dev/null || true
    sudo systemctl start docker 2>/dev/null || true
}

if [ -f "/etc/os-release" ]; then
    . /etc/os-release
    case "$ID" in
        alpine)
            install_alpine
            ;;
        pop|ubuntu|debian)
            install_debian
            ;;
        *)
            echo "AVISO: Sistema '$ID' não suportado automaticamente. Tente instalar dependências manuais."
            ;;
    esac
else
    echo "ERRO: Não foi possível detectar o sistema operacional via /etc/os-release."
    exit 1
fi

echo "--- Etapa 01 concluída com sucesso! ---"
