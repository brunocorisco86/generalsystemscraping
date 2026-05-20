#!/bin/bash

# Script de Backup PostgreSQL para Cloudflare R2
# Autor: Manus (AI Architect)
# Data: 2026-04-12

# 1. Resolver caminhos e carregar variáveis de ambiente
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"

if [ -f "$ENV_FILE" ]; then
    # Carrega variáveis de forma robusta, ignorando comentários e linhas inválidas
    while read -r line || [ -n "$line" ]; do
        case "$line" in
            # Ignora linhas vazias e comentários que começam com #
            "" | [[:space:]]*#*) continue ;;
            # Exporta apenas se tiver o formato CHAVE=VALOR
            [A-Za-z0-9_]*=*) export "$line" ;;
        esac
    done < "$ENV_FILE"
else
    echo "[$(date)] ERRO: Arquivo .env não encontrado em $ENV_FILE"
    exit 1
fi

# 2. Configurações baseadas no .env ou calculadas
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
# Se PROJECT_ROOT não estiver no .env, usa o REPO_ROOT detectado
ACTUAL_PROJECT_ROOT="${PROJECT_ROOT:-$REPO_ROOT}"
BACKUP_DIR="${ACTUAL_PROJECT_ROOT}/data/backups"
BACKUP_FILE="piscicultura_backup_$TIMESTAMP.sql.gz"
CONTAINER_NAME="piscicultura_postgres"
RETENCAO_LOCAL=30
RETENCAO_R2=5

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

        # 5. Limpeza de backups antigos no R2 (Mantém as últimas N versões)
        echo "[$(date)] Verificando retenção no R2 (Mantendo as últimas $RETENCAO_R2 versões)..."
        # Lista arquivos, ordena do mais novo para o mais antigo, e pega a partir do N+1
        BACKUPS_R2=$(rclone lsf "R2:$R2_BUCKET_NAME/" | grep "piscicultura_backup_" | sort -r)
        COUNT_R2=$(echo "$BACKUPS_R2" | grep -v '^$' | wc -l)

        if [ "$COUNT_R2" -gt "$RETENCAO_R2" ]; then
            TO_DELETE=$(echo "$BACKUPS_R2" | tail -n +$((RETENCAO_R2 + 1)))
            for file in $TO_DELETE; do
                if [ -n "$file" ]; then
                    echo "Deletando backup antigo no R2: $file"
                    rclone deletefile "R2:$R2_BUCKET_NAME/$file"
                fi
            done
        fi
    else
        echo "[$(date)] AVISO: Falha na sincronização com R2. Verifique as credenciais no .env."
    fi
else
    echo "[$(date)] AVISO: rclone não encontrado. Backup mantido apenas localmente em $BACKUP_DIR."
fi

# 6. Limpeza de backups antigos (Local)
echo "[$(date)] Limpando backups locais com mais de $RETENCAO_LOCAL dias..."
find "$BACKUP_DIR" -name "piscicultura_backup_*.sql.gz" -mtime +$RETENCAO_LOCAL -delete

echo "[$(date)] Processo de backup finalizado."

