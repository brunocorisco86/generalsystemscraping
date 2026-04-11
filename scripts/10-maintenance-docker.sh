#!/bin/sh
# 10-maintenance-docker.sh: Para, remove containers e limpa imagens do projeto

set -e

# Resolve a raiz do repositório
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "--- [10] Manutenção e Limpeza Docker ---"

# 1. Detecta o comando docker compose
DOCKER_COMPOSE="docker compose"
if ! $DOCKER_COMPOSE version >/dev/null 2>&1; then
    DOCKER_COMPOSE="docker-compose"
fi

cd "$REPO_ROOT"

# 2. Pergunta ao usuário o nível de limpeza
echo "Escolha o nível de limpeza:"
echo "1) Parar e remover apenas os containers (Mantém imagens e dados)"
echo "2) Limpeza completa (Remove containers, volumes e imagens locais)"
echo "3) Cancelar"
printf "Opção: "
read opcao

case $opcao in # Usando case para compatibilidade POSIX
    1)
        echo "--- Parando e removendo containers... ---"
        $DOCKER_COMPOSE down
        ;;
    2)
        echo "--- Realizando limpeza profunda (Containers, Imagens Locais e Orfãos)... ---"
        $DOCKER_COMPOSE down --rmi local --volumes --remove-orphans
        echo "--- Removendo imagens suspensas (prune)... ---"
        docker image prune -f
        ;;
    *)
        echo "Operação cancelada."
        exit 0
        ;;
esac

echo ""
echo "✅ Manutenção concluída!"
echo "Para reinstalar/subir os serviços novamente, use: bash scripts/07-start-containers.sh"
