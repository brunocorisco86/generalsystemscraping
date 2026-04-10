# Modelo de Crontab para Alpine Linux

Este documento fornece um modelo pronto para ser colado no seu `crontab -e`. Ele foi adaptado para o hardware do Raspberry Pi com Alpine Linux, utilizando caminhos absolutos e execução via módulos Python.

**Importante:** Substitua `/home/bruno/generalsystemscraping` pelo caminho real onde você clonou o repositório, caso seja diferente.

```cron
# ==============================================================================
# PROJETO PISCICULTURA - CONFIGURAÇÃO DE CRON (ALPINE LINUX)
# ==============================================================================
# Variáveis de Ambiente para o Cron
SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
PROJECT_ROOT=/home/bruno/generalsystemscraping
VENV_PYTHON=/home/bruno/generalsystemscraping/.venv/bin/python3

# ==============================================================================
# 1. MONITORAMENTO E COLETA (SCRAPING)
# ==============================================================================
# Captura dados dos tanques a cada 15 minutos
1,16,31,46 * * * * cd $PROJECT_ROOT && $VENV_PYTHON -m src.scrape.monitor_data >> $PROJECT_ROOT/logs/scrape.log 2>&1

# Verifica se o sistema está online (2 minutos após a coleta)
3,18,33,48 * * * * cd $PROJECT_ROOT && $VENV_PYTHON -m src.alerts.offline_check >> $PROJECT_ROOT/logs/alerts.log 2>&1

# ==============================================================================
# 2. ALERTAS OPERACIONAIS CRÍTICOS
# ==============================================================================
# Verifica níveis críticos de O2 (4 minutos após a coleta)
4,19,34,49 * * * * cd $PROJECT_ROOT && $VENV_PYTHON -m src.alerts.alert_check >> $PROJECT_ROOT/logs/alerts.log 2>&1

# ==============================================================================
# 3. RELATÓRIOS E ANÁLISES (TELEGRAM)
# ==============================================================================
# Relatório Horário (Estatísticas e Tendências)
3 7-22 * * * cd $PROJECT_ROOT && $VENV_PYTHON -m src.jobs.hourly_report >> $PROJECT_ROOT/logs/cron.log 2>&1

# 08:05 - Relatório Noturno (Resumo da noite anterior e Gráfico)
5 8 * * * cd $PROJECT_ROOT && $VENV_PYTHON -m src.jobs.nightly_report >> $PROJECT_ROOT/logs/cron.log 2>&1

# 08:00 - Predição de horário de Arraçoamento
32 8 * * * cd $PROJECT_ROOT && $VENV_PYTHON -m src.analysis.feed_prediction >> $PROJECT_ROOT/logs/cron.log 2>&1

# 17:06 - Análise Preditiva de Oxigênio (Forecast para a noite)
6 17 * * * cd $PROJECT_ROOT && $VENV_PYTHON -m src.analysis.predict_oxygen >> $PROJECT_ROOT/logs/cron.log 2>&1

# 22:06 - Fechamento do Dia (Gráfico Tarde/Noite e ajuste de Threshold)
6 22 * * * cd $PROJECT_ROOT && $VENV_PYTHON -m src.jobs.evening_report >> $PROJECT_ROOT/logs/cron.log 2>&1

# ==============================================================================
# 4. MANUTENÇÃO E BACKUP
# ==============================================================================
# Migração de dados SQLite para Postgres (Backup Incremental)
00 07,18 * * * cd $PROJECT_ROOT && $VENV_PYTHON -m src.jobs.migrate_data >> $PROJECT_ROOT/logs/migrate.log 2>&1

# Limpeza automática de logs (Mantém apenas os últimos 7 dias)
0 1 * * * sh $PROJECT_ROOT/scripts/cleanup_logs.sh >> $PROJECT_ROOT/logs/cron.log 2>&1

# Correção de permissões no boot
@reboot sleep 30 && sh $PROJECT_ROOT/scripts/fix_permissions.sh
```

### Notas sobre as mudanças:
1. **`python3 -m src.module`**: Agora usamos a flag `-m`. Isso é necessário para que as importações internas do projeto (como o serviço de banco de dados) funcionem corretamente.
2. **`cd $PROJECT_ROOT`**: Sempre entramos na pasta do projeto antes de rodar o comando para garantir que os caminhos relativos do Python funcionem.
3. **`VENV_PYTHON`**: Aponta diretamente para o Python dentro do seu ambiente virtual, evitando conflitos com o Python do sistema.
4. **Log Centralizado**: O script `cleanup_logs.sh` agora gerencia a limpeza para não encher o cartão SD, em vez de comandos `echo ""` manuais.
