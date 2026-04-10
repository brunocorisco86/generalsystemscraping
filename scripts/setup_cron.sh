#!/bin/bash

# Este script exibe as entradas de cron recomendadas para este projeto.
#
# USO:
# 1. Certifique-se de que a variável PROJECT_ROOT em seu arquivo .env
#    está configurada com o caminho absoluto para a raiz deste projeto.
# 2. Execute este script: bash scripts/setup_cron.sh
# 3. Copie a saída e cole-a em seu crontab com o comando: crontab -e
#

set -e

ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    echo "ERRO: Arquivo .env não encontrado. Execute o script 'setup.sh' primeiro."
    exit 1
fi

# Carrega a variável PROJECT_ROOT do arquivo .env
# Remove comentários e espaços em branco
PROJECT_ROOT=$(grep -v '^#' "$ENV_FILE" | grep 'PROJECT_ROOT' | cut -d '=' -f2- | sed 's/^[ 	]*//;s/[ 	]*$//')

if [ -z "$PROJECT_ROOT" ]; then
    echo "ERRO: A variável 'PROJECT_ROOT' não está definida em seu arquivo .env."
    echo "Por favor, adicione-a com o caminho absoluto para o diretório do projeto."
    exit 1
fi

VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python3"

# Verifica se o executável do Python no venv existe
if [ ! -f "$VENV_PYTHON" ]; then
    echo "ERRO: Python do ambiente virtual não encontrado em '$VENV_PYTHON'."
    echo "Verifique se o ambiente foi criado corretamente com 'setup.sh'."
    exit 1
fi

# --- Saída do Crontab ---

echo "--- Copie e cole as seguintes linhas em seu crontab (crontab -e) ---"
echo ""
echo "# =============================================================================="
echo "# == Cron Jobs para o Projeto de Monitoramento de Piscicultura"
echo "# =============================================================================="
echo ""
# Coleta de dados (executa a cada 15 minutos)
echo "*/15 * * * * cd $PROJECT_ROOT && $VENV_PYTHON -m src.scrape.monitor_data >> $PROJECT_ROOT/logs/scrape.log 2>&1"
echo ""
echo "# Verificação de alertas de Oxigênio (executa a cada 15 minutos, 2 min após a coleta)"
echo "2,17,32,47 * * * * cd $PROJECT_ROOT && $VENV_PYTHON -m src.alerts.alert_check >> $PROJECT_ROOT/logs/alerts.log 2>&1"
echo ""
echo "# Verificação de sistema offline (executa a cada 30 minutos)"
echo "*/30 * * * * cd $PROJECT_ROOT && $VENV_PYTHON -m src.alerts.offline_check >> $PROJECT_ROOT/logs/alerts.log 2>&1"
echo ""
echo "# Job de migração de dados do SQLite para o PostgreSQL (executa todo dia às 02:00)"

echo "0 2 * * * $VENV_PYTHON $PROJECT_ROOT/src/jobs/migrate_data.py >> $PROJECT_ROOT/logs/cron.log 2>&1"
echo ""
echo "# Relatório de final de tarde (executa todo dia às 23:30)"
echo "30 23 * * * $VENV_PYTHON $PROJECT_ROOT/src/jobs/evening_report.py >> $PROJECT_ROOT/logs/cron.log 2>&1"
echo ""
echo "# (Exemplo) Relatório de hora em hora (descomente para ativar)"
echo "# 0 * * * * $VENV_PYTHON $PROJECT_ROOT/src/jobs/hourly_report.py >> $PROJECT_ROOT/logs/cron.log 2>&1"
echo ""
echo "# (Exemplo) Relatório noturno (descomente para ativar)"
echo "# 0 6 * * * $VENV_PYTHON $PROJECT_ROOT/src/jobs/nightly_report.py >> $PROJECT_ROOT/logs/cron.log 2>&1"
echo ""
echo "# Limpeza de logs (executa todo dia à 01:00)"
echo "0 1 * * * bash $PROJECT_ROOT/scripts/cleanup_logs.sh >> $PROJECT_ROOT/logs/cron.log 2>&1"
echo ""
echo "# =============================================================================="
echo ""

exit 0
