#!/bin/bash
# 01-system-deps.sh: Instala dependências do sistema via APK (Alpine Linux)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "--- [01/04] Verificando dependências do sistema ---"

install_alpine_deps() {
    echo "--- Detectado Alpine Linux. Instalando dependências ---"
    sudo apk update
    sudo apk add --no-cache \
        git docker docker-cli-compose python3 py3-pip py3-virtualenv \
        python3-dev build-base postgresql-dev sqlite-dev libffi-dev \
        zlib-dev util-linux openblas openblas-dev freetype freetype-dev \
        libpng libpng-dev jpeg jpeg-dev tiff tiff-dev chromium \
        chromium-chromedriver ncurses-dev

    # Garante que o Docker sobe junto com o sistema
    sudo rc-update add docker boot 2>/dev/null || true
    sudo rc-service docker start 2>/dev/null || true
}

if [ -f "/etc/os-release" ]; then
    . /etc/os-release
    if [ "$ID" = "alpine" ]; then
        install_alpine_deps
    else
        echo "AVISO: Sistema não é Alpine. Instale as dependências de sistema manualmente."
    fi
else
    echo "AVISO: Não foi possível determinar o OS."
fi

echo "--- Etapa 01 concluída com sucesso! ---"
