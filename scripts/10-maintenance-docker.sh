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
echo "Escolha o nível de limpeza / manutenção:"
echo "1) Parar e remover apenas os containers (Mantém imagens e dados)"
echo "2) Limpeza profunda (Remove containers, volumes e TODAS as imagens do projeto)"
echo "3) Forçar Rebuild Total (Para, reconstrói sem cache e inicia tudo)"
echo "4) Cancelar"
printf "Opção: "
read opcao

case $opcao in # Usando case para compatibilidade POSIX
    1)
        echo "--- Parando e removendo containers... ---"
        $DOCKER_COMPOSE down
        ;;
    2)
        echo "--- Realizando limpeza profunda (Containers, Imagens e Orfãos)... ---"
        $DOCKER_COMPOSE down --rmi all --volumes --remove-orphans
        echo "--- Removendo imagens suspensas (prune)... ---"
        docker image prune -f
        ;;
    3)
        echo "--- Reiniciando com Rebuild Total (sem cache)... ---"
        $DOCKER_COMPOSE down
        $DOCKER_COMPOSE build --no-cache
        $DOCKER_COMPOSE up -d
        ;;
    *)
        echo "Operação cancelada."
        exit 0
        ;;
esac

echo ""
echo "✅ Manutenção concluída!"
echo ""
echo "--- Status Atual do Docker ---"
echo "Containers ativos:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "Imagens disponíveis:"
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
echo ""
echo "Para reinstalar/subir os serviços novamente, use: bash scripts/07-start-containers.sh"
