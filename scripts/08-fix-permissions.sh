#!/bin/bash
# 08-fix-permissions.sh: Garante as permissões corretas para o funcionamento do sistema

set -e

# Detecta a raiz do projeto (um nível acima de scripts/)
MONITOR_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_FILE="${MONITOR_DIR}/logs/scripts_log.log"

echo "--- [08] Ajustando permissões do sistema em: $MONITOR_DIR ---"

# 1. Cria pastas essenciais se não existirem
mkdir -p "${MONITOR_DIR}/logs"
mkdir -p "${MONITOR_DIR}/reports"
mkdir -p "${MONITOR_DIR}/data/postgres"

# 2. Permissões de execução nos scripts
echo "--- Configurando permissões de execução... ---"
chmod +x "${MONITOR_DIR}/scripts/"*.sh
find "${MONITOR_DIR}/src" -name "*.py" -exec chmod +x {} +

# 3. Permissão no banco de dados SQLite (se existir)
if [ -f "${MONITOR_DIR}/data/piscicultura_dados.db" ]; then
    chmod 666 "${MONITOR_DIR}/data/piscicultura_dados.db"
fi

# 4. Permissões de escrita em pastas de saída e dados
echo "--- Ajustando permissões de escrita em logs, relatórios e dados... ---"
chmod 777 "${MONITOR_DIR}/reports"
chmod 777 "${MONITOR_DIR}/logs"
chmod -R 777 "${MONITOR_DIR}/data"

# 5. Permissões gerais do diretório do projeto
chmod 755 "${MONITOR_DIR}"

# 6. Garantir que o arquivo de log de scripts seja acessível
touch "${LOG_FILE}"
chmod 666 "${LOG_FILE}"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Permissões ajustadas com sucesso" >> "${LOG_FILE}"
echo "✅ Permissões configuradas!"
