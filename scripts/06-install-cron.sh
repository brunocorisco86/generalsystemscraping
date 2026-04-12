#!/bin/sh
# 06-install-cron.sh: Instala tarefas no cron com caminhos absolutos e sem variáveis

set -e

echo "--- [06/06] Instalando Tarefas Automáticas no Cron ---"

# Detecta a pasta do script e a raiz do projeto (Compatível com POSIX/Alpine)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$PROJECT_ROOT_DIR/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "ERRO: Arquivo .env não encontrado em $ENV_FILE. Execute o script 'setup.sh' primeiro."
    exit 1
fi

# Carrega a variavel PROJECT_ROOT e remove aspas extras
PROJECT_ROOT=$(grep -v '^#' "$ENV_FILE" | grep 'PROJECT_ROOT' | cut -d '=' -f2- | sed 's/^[ 	]*//;s/[ 	]*$//' | tr -d '"' | tr -d "'")

if [ -z "$PROJECT_ROOT" ]; then
    PROJECT_ROOT="$PROJECT_ROOT_DIR"
fi

# Remove barra final se existir para evitar caminhos como //logs
PROJECT_ROOT=$(echo "$PROJECT_ROOT" | sed 's|/*$||')

VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python3"

# Verifica se o ambiente virtual existe
if [ ! -f "$VENV_PYTHON" ]; then
    echo "ERRO: Ambiente virtual não encontrado em $VENV_PYTHON"
    echo "Por favor, execute o setup.sh primeiro."
    exit 1
fi

# Gera o conteúdo do cron temporariamente com caminhos REAIS (Hardcoded)
TMP_NEW=$(mktemp)
echo "# --- PISCICULTURA: $PROJECT_ROOT ---" >> "$TMP_NEW"
echo "1-46/15 * * * * cd $PROJECT_ROOT && $VENV_PYTHON -m src.scrape.monitor_data >> $PROJECT_ROOT/logs/scrape.log 2>&1" >> "$TMP_NEW"
echo "3-48/15 * * * * cd $PROJECT_ROOT && $VENV_PYTHON -m src.alerts.offline_check >> $PROJECT_ROOT/logs/alerts.log 2>&1" >> "$TMP_NEW"
echo "4-49/15 * * * * cd $PROJECT_ROOT && $VENV_PYTHON -m src.alerts.alert_check >> $PROJECT_ROOT/logs/alerts.log 2>&1" >> "$TMP_NEW"
echo "3 7-22 * * * cd $PROJECT_ROOT && $VENV_PYTHON -m src.jobs.hourly_report >> $PROJECT_ROOT/logs/cron.log 2>&1" >> "$TMP_NEW"
echo "5 8 * * * cd $PROJECT_ROOT && $VENV_PYTHON -m src.jobs.nightly_report >> $PROJECT_ROOT/logs/cron.log 2>&1" >> "$TMP_NEW"
echo "32 8 * * * cd $PROJECT_ROOT && $VENV_PYTHON -m src.analysis.feed_prediction >> $PROJECT_ROOT/logs/cron.log 2>&1" >> "$TMP_NEW"
echo "6 17 * * * cd $PROJECT_ROOT && $VENV_PYTHON -m src.analysis.predict_oxygen >> $PROJECT_ROOT/logs/cron.log 2>&1" >> "$TMP_NEW"
echo "6 22 * * * cd $PROJECT_ROOT && $VENV_PYTHON -m src.jobs.evening_report >> $PROJECT_ROOT/logs/cron.log 2>&1" >> "$TMP_NEW"
echo "7 22-23,0-6 * * * cd $PROJECT_ROOT && $VENV_PYTHON -m src.jobs.vigi_report >> $PROJECT_ROOT/logs/cron.log 2>&1" >> "$TMP_NEW"
echo "0 7,18 * * * cd $PROJECT_ROOT && $VENV_PYTHON -m src.database.postgres.migrate_data >> $PROJECT_ROOT/logs/migrate.log 2>&1" >> "$TMP_NEW"
echo "0 1 * * * sh $PROJECT_ROOT/scripts/09-cleanup-logs.sh 7 >> $PROJECT_ROOT/logs/cron.log 2>&1" >> "$TMP_NEW"
echo "0 4 1 * * sh $PROJECT_ROOT/scripts/09-cleanup-logs.sh 30 >> $PROJECT_ROOT/logs/cron.log 2>&1" >> "$TMP_NEW"
echo "@reboot sleep 30 && sh $PROJECT_ROOT/scripts/08-fix-permissions.sh" >> "$TMP_NEW"

# Limpa o crontab atual de qualquer linha que contenha o caminho deste projeto
# Isso evita duplicatas e remove versões anteriores
CLEAN_CRON=$(crontab -l 2>/dev/null | grep -v "$PROJECT_ROOT" || echo "")

# Instala o novo crontab (Preserva o que já existia de outros sistemas e adiciona o nosso)
(echo "$CLEAN_CRON"; cat "$TMP_NEW") | crontab -

rm "$TMP_NEW"

echo "✅ Cron Jobs instalados com sucesso!"
echo "As tarefas agora utilizam caminhos absolutos:"
echo "Python: $VENV_PYTHON"
echo "Pasta:  $PROJECT_ROOT"
