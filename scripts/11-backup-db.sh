#!/bin/bash

# Script de Backup PostgreSQL para Cloudflare R2
# Autor: Manus (AI Architect)
# Data: 2026-04-12

# 1. Carregar variáveis de ambiente
# O script assume que está sendo executado a partir da raiz do projeto
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "[$(date)] ERRO: Arquivo .env não encontrado na raiz do projeto."
    exit 1
fi

# 2. Configurações baseadas no .env
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="${PROJECT_ROOT}/data/backups"
BACKUP_FILE="piscicultura_backup_$TIMESTAMP.sql.gz"
CONTAINER_NAME="piscicultura_postgres"
RETENCAO_LOCAL=30

# Criar diretório de backup se não existir
mkdir -p "$BACKUP_DIR"

echo "[$(date)] Iniciando backup do banco de dados: $PG_DBNAME"

# 3. Gerar dump e compactar (Usando variáveis do .env)
# Nota: O pg_dump dentro do container usa as credenciais do ambiente do container
docker exec "$CONTAINER_NAME" pg_dump -U "$PG_USER" "$PG_DBNAME" | gzip > "$BACKUP_DIR/$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "[$(date)] Backup local gerado com sucesso: $BACKUP_FILE"
else
    echo "[$(date)] ERRO: Falha ao gerar backup local."
    exit 1
fi

# 4. Sincronizar com Cloudflare R2 (Usando variáveis do .env)
if command -v rclone &> /dev/null; then
    echo "[$(date)] Sincronizando com Cloudflare R2 (Bucket: $R2_BUCKET_NAME)..."
    
    # Configuração temporária do rclone via variáveis de ambiente para evitar dependência de config file
    export RCLONE_CONFIG_R2_TYPE=s3
    export RCLONE_CONFIG_R2_PROVIDER=Cloudflare
    export RCLONE_CONFIG_R2_ACCESS_KEY_ID="$R2_ACCESS_KEY_ID"
    export RCLONE_CONFIG_R2_SECRET_ACCESS_KEY="$R2_SECRET_ACCESS_KEY"
    export RCLONE_CONFIG_R2_ENDPOINT="$R2_ENDPOINT_URL"
    export RCLONE_CONFIG_R2_ACL=private

    rclone copy "$BACKUP_DIR/$BACKUP_FILE" "R2:$R2_BUCKET_NAME/"
    
    if [ $? -eq 0 ]; then
        echo "[$(date)] Sincronização com R2 concluída com sucesso."
    else
        echo "[$(date)] AVISO: Falha na sincronização com R2. Verifique as credenciais no .env."
    fi
else
    echo "[$(date)] AVISO: rclone não encontrado. Backup mantido apenas localmente em $BACKUP_DIR."
fi

# 5. Limpeza de backups antigos (Local)
echo "[$(date)] Limpando backups locais com mais de $RETENCAO_LOCAL dias..."
find "$BACKUP_DIR" -name "piscicultura_backup_*.sql.gz" -mtime +$RETENCAO_LOCAL -delete

echo "[$(date)] Processo de backup finalizado."

