#!/bin/bash
# Script para garantir permissões corretas do sistema de monitoramento

MONITOR_DIR="/home/dietpi/piscicultura_monitor"
LOG_FILE="${MONITOR_DIR}/scripts_log.log"

# Ajustar propriedade dos scripts Python
chown nodered:nodered ${MONITOR_DIR}/*.py

# Permissões de execução nos scripts
chmod 755 ${MONITOR_DIR}/*.py

# Permissão no banco de dados
chmod 666 ${MONITOR_DIR}/piscicultura_dados.db

# Permissão total na pasta de relatórios
chmod 777 ${MONITOR_DIR}/reports/

# Permissões dos diretórios
chmod 755 ${MONITOR_DIR}
chmod 755 /home/dietpi

# Garantir que o log seja acessível
touch ${LOG_FILE}
chmod 666 ${LOG_FILE}

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Permissões ajustadas com sucesso" >> ${LOG_FILE}
