#!/bin/bash
# 09-cleanup-logs.sh: Limpa logs antigos para economizar espaço em disco

set -e

# Detecta a pasta do script e a raiz do projeto (Compatível com POSIX/Alpine)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$PROJECT_ROOT_DIR/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "ERRO: Arquivo .env não encontrado em $ENV_FILE. Execute o setup.sh primeiro."
    exit 1
fi

# Carrega a variavel PROJECT_ROOT e remove aspas extras
PROJECT_ROOT=$(grep -v '^#' "$ENV_FILE" | grep 'PROJECT_ROOT' | cut -d '=' -f2- | sed 's/^[ 	]*//;s/[ 	]*$//' | tr -d '"' | tr -d "'")

LOGS_DIR="$PROJECT_ROOT/logs"
RETENTION_DAYS=7 # Valor padrão: 7 dias

# Se um argumento for passado, usa como dias de retenção
if [ ! -z "$1" ]; then
    RETENTION_DAYS=$1
fi

if [ ! -d "$LOGS_DIR" ]; then
    echo "AVISO: Diretório de logs $LOGS_DIR não encontrado."
    exit 0
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando limpeza de logs em $LOGS_DIR (retenção: $RETENTION_DAYS dias)."

# Encontra e deleta arquivos de log mais antigos que RETENTION_DAYS dias
find "$LOGS_DIR" -type f -name "*.log" -mtime +$RETENTION_DAYS -delete

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Limpeza de logs concluída."
