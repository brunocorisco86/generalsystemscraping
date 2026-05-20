#!/bin/bash

# Script de Restauração de Banco de Dados via Cloudflare R2
# Autor: Manus (AI Architect)
# Data: 2026-05-20

set -e

# 1. Carregar variáveis de ambiente
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "[$(date)] ERRO: Arquivo .env não encontrado na raiz do projeto."
    exit 1
fi

BACKUP_DIR="${PROJECT_ROOT}/data/backups"
CONTAINER_NAME="piscicultura_postgres"

# Criar diretório se não existir
mkdir -p "$BACKUP_DIR"

# 2. Configuração rclone
export RCLONE_CONFIG_R2_TYPE=s3
export RCLONE_CONFIG_R2_PROVIDER=Cloudflare
export RCLONE_CONFIG_R2_ACCESS_KEY_ID="$R2_ACCESS_KEY_ID"
export RCLONE_CONFIG_R2_SECRET_ACCESS_KEY="$R2_SECRET_ACCESS_KEY"
export RCLONE_CONFIG_R2_ENDPOINT="$R2_ENDPOINT_URL"
export RCLONE_CONFIG_R2_ACL=private

echo "--- [RESTAURAÇÃO] Iniciando recuperação de dados do Cloudflare R2 ---"

# 3. Encontrar o backup mais recente no R2
echo "Buscando backups disponíveis no R2..."
LATEST_BACKUP=$(rclone lsf "R2:$R2_BUCKET_NAME/" | grep "piscicultura_backup_" | sort -r | head -n 1)

if [ -z "$LATEST_BACKUP" ]; then
    echo "ERRO: Nenhum backup encontrado no bucket $R2_BUCKET_NAME."
    exit 1
fi

echo "Backup mais recente encontrado: $LATEST_BACKUP"

# 4. Download do arquivo
echo "Baixando backup..."
rclone copy "R2:$R2_BUCKET_NAME/$LATEST_BACKUP" "$BACKUP_DIR/"

# 5. Restauração no PostgreSQL
echo "Iniciando injeção de dados no container $CONTAINER_NAME..."

# Descompacta e injeta via psql (Como o dump foi feito com pg_dump simples, usamos psql)
gunzip -c "$BACKUP_DIR/$LATEST_BACKUP" | docker exec -i "$CONTAINER_NAME" psql -U "$PG_USER" -d "$PG_DBNAME"

if [ $? -eq 0 ]; then
    echo "✅ Restauração concluída com sucesso!"
    echo "O banco de dados '$PG_DBNAME' foi atualizado."
else
    echo "❌ ERRO: Falha ao restaurar o banco de dados."
    exit 1
fi

echo "--- Processo Finalizado ---"
