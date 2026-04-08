#!/bin/bash

# Script para limpar logs antigos, mantendo apenas os logs da última semana.

# Abortar em caso de erro
set -e

# Carrega a variável PROJECT_ROOT do arquivo .env
# Remove comentários e espaços em branco
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    echo "ERRO: Arquivo .env não encontrado. Execute o script 'setup.sh' primeiro."
    exit 1
fi
PROJECT_ROOT=$(grep -v '^#' "$ENV_FILE" | grep 'PROJECT_ROOT' | cut -d '=' -f2- | sed 's/^[ 	]*//;s/[ 	]*$//')

LOGS_DIR="$PROJECT_ROOT/logs"
RETENTION_DAYS=7 # Manter logs por 7 dias

echo "$(date): Iniciando limpeza de logs em $LOGS_DIR. Mantendo últimos $RETENTION_DAYS dias."

# Encontra e deleta arquivos de log mais antigos que RETENTION_DAYS dias
# -type f: apenas arquivos
# -name "*.log": apenas arquivos com extensão .log
# -mtime +N: arquivos modificados há mais de N dias
find "$LOGS_DIR" -type f -name "*.log" -mtime +$RETENTION_DAYS -delete

echo "$(date): Limpeza de logs concluída."

exit 0
