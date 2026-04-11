#!/bin/bash
# Script para garantir permissões corretas do sistema de monitoramento

# Detecta a raiz do projeto (um nível acima de scripts/)
MONITOR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="${MONITOR_DIR}/logs/scripts_log.log"

# Cria pasta de logs se não existir
mkdir -p "${MONITOR_DIR}/logs"

# Ajustar propriedade dos scripts Python (opcional, dependendo do usuário que roda)
# chown $(whoami):$(whoami) ${MONITOR_DIR}/src/**/*.py

# Permissões de execução nos scripts
chmod +x ${MONITOR_DIR}/scripts/*.sh
chmod +x ${MONITOR_DIR}/src/**/*.py

# Permissão no banco de dados SQLite (se estiver no local padrão)
[ -f "${MONITOR_DIR}/data/piscicultura_dados.db" ] && chmod 666 "${MONITOR_DIR}/data/piscicultura_dados.db"

# Permissão na pasta de relatórios
mkdir -p "${MONITOR_DIR}/reports"
chmod 777 "${MONITOR_DIR}/reports/"

# Permissões dos diretórios
chmod 755 "${MONITOR_DIR}"

# Garantir que o log seja acessível
touch "${LOG_FILE}"
chmod 666 "${LOG_FILE}"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Permissões ajustadas em $MONITOR_DIR" >> "${LOG_FILE}"
