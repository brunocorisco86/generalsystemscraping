#!/bin/bash

# Script para instalar automaticamente os Cron Jobs do projeto.
# Ele remove entradas antigas do projeto e adiciona as novas.

set -e

echo "--- [06/06] Instalando Tarefas Automáticas no Cron ---"

# Detecta a pasta do script e a raiz do projeto (Compatível com POSIX/Alpine)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$PROJECT_ROOT_DIR/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "ERRO: Arquivo .env não encontrado em $ENV_FILE. Execute o script 'setup.sh' na raiz do projeto primeiro."
    exit 1
fi

# Carrega a variavel PROJECT_ROOT e remove aspas extras
PROJECT_ROOT=$(grep -v '^#' "$ENV_FILE" | grep 'PROJECT_ROOT' | cut -d '=' -f2- | sed 's/^[ 	]*//;s/[ 	]*$//' | tr -d '"' | tr -d "'")

if [ -z "$PROJECT_ROOT" ]; then
    echo "ERRO: A variável 'PROJECT_ROOT' não está definida em seu arquivo .env."
    exit 1
fi

VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python3"

# Verifica se o ambiente virtual existe antes de prosseguir
if [ ! -f "$VENV_PYTHON" ]; then
    echo "ERRO: Ambiente virtual não encontrado em $VENV_PYTHON"
    echo "Por favor, execute o setup.sh primeiro para criar o venv."
    exit 1
fi

MARKER_START="# == PISCICULTURA START =="
MARKER_END="# == PISCICULTURA END =="

# Gera o conteúdo do cron temporariamente
TMP_CRON=$(mktemp)
echo "$MARKER_START" >> "$TMP_CRON"
echo "SHELL=/bin/sh" >> "$TMP_CRON"
echo "PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin" >> "$TMP_CRON"
echo "PROJECT_ROOT=$PROJECT_ROOT" >> "$TMP_CRON"
echo "VENV_PYTHON=$VENV_PYTHON" >> "$TMP_CRON"
echo ""
echo "1,16,31,46 * * * * cd \$PROJECT_ROOT && \$VENV_PYTHON -m src.scrape.monitor_data >> \$PROJECT_ROOT/logs/scrape.log 2>&1" >> "$TMP_CRON"
echo "3,18,33,48 * * * * cd \$PROJECT_ROOT && \$VENV_PYTHON -m src.alerts.offline_check >> \$PROJECT_ROOT/logs/alerts.log 2>&1" >> "$TMP_CRON"
echo "4,19,34,49 * * * * cd \$PROJECT_ROOT && \$VENV_PYTHON -m src.alerts.alert_check >> \$PROJECT_ROOT/logs/alerts.log 2>&1" >> "$TMP_CRON"
echo "3 7-22 * * * cd \$PROJECT_ROOT && \$VENV_PYTHON -m src.jobs.hourly_report >> \$PROJECT_ROOT/logs/cron.log 2>&1" >> "$TMP_CRON"
echo "5 8 * * * cd \$PROJECT_ROOT && \$VENV_PYTHON -m src.jobs.nightly_report >> \$PROJECT_ROOT/logs/cron.log 2>&1" >> "$TMP_CRON"
echo "32 8 * * * cd \$PROJECT_ROOT && \$VENV_PYTHON -m src.analysis.feed_prediction >> \$PROJECT_ROOT/logs/cron.log 2>&1" >> "$TMP_CRON"
echo "6 17 * * * cd \$PROJECT_ROOT && \$VENV_PYTHON -m src.analysis.predict_oxygen >> \$PROJECT_ROOT/logs/cron.log 2>&1" >> "$TMP_CRON"
echo "6 22 * * * cd \$PROJECT_ROOT && \$VENV_PYTHON -m src.jobs.evening_report >> \$PROJECT_ROOT/logs/cron.log 2>&1" >> "$TMP_CRON"
echo "7 22,23,0,1,2,3,4,5,6 * * * cd \$PROJECT_ROOT && \$VENV_PYTHON -m src.jobs.vigi_report >> \$PROJECT_ROOT/logs/cron.log 2>&1" >> "$TMP_CRON"
echo "00 07,18 * * * cd \$PROJECT_ROOT && \$VENV_PYTHON -m src.database.postgres.migrate_data >> \$PROJECT_ROOT/logs/migrate.log 2>&1" >> "$TMP_CRON"
echo "" >> "$TMP_CRON"
echo "# Limpeza automática de logs (Diária: mantém 7 dias | Mensal: limpeza profunda)" >> "$TMP_CRON"
echo "0 1 * * * sh \$PROJECT_ROOT/scripts/09-cleanup-logs.sh 7 >> \$PROJECT_ROOT/logs/cron.log 2>&1" >> "$TMP_CRON"
echo "0 4 1 * * sh \$PROJECT_ROOT/scripts/09-cleanup-logs.sh 30 >> \$PROJECT_ROOT/logs/cron.log 2>&1" >> "$TMP_CRON"
echo "" >> "$TMP_CRON"
echo "@reboot sleep 30 && sh \$PROJECT_ROOT/scripts/08-fix-permissions.sh" >> "$TMP_CRON"
echo "$MARKER_END" >> "$TMP_CRON"

# Lê o crontab atual, removendo blocos antigos do projeto
CURRENT_CRON=$(crontab -l 2>/dev/null | sed "/$MARKER_START/,/$MARKER_END/d" || echo "")

# Instala o novo crontab
(echo "$CURRENT_CRON"; cat "$TMP_CRON") | crontab -

rm "$TMP_CRON"

echo "✅ Cron Jobs instalados com sucesso para o usuário $(whoami)!"
echo "Verifique com: crontab -l"
