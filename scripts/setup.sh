#!/bin/sh
# setup.sh: Script mestre de configuração completa (POSIX compliant)

set -e

# Resolve a pasta onde os scripts estão
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "------------------------------------------------------------"
echo "--- PROJETO DE MONITORAMENTO DE PISCICULTURA: CONFIGURAÇÃO ---"
echo "------------------------------------------------------------"
echo ""

# Define as etapas e garante permissões
for script in "01-system-deps.sh" "02-setup-venv.sh" "03-install-python-deps.sh" "04-setup-env-file.sh" "05-init-sqlite-db.py" "06-install-cron.sh"; do
    chmod +x "$SCRIPT_DIR/$script"
done

# Orquestra a execução das etapas
sh "$SCRIPT_DIR/01-system-deps.sh"
sh "$SCRIPT_DIR/02-setup-venv.sh"
sh "$SCRIPT_DIR/03-install-python-deps.sh"
sh "$SCRIPT_DIR/04-setup-env-file.sh"

# Etapa 05: Inicialização do Banco de Dados via Python
echo "--- [05/06] Inicializando Banco de Dados SQLite ---"
VENV_PYTHON="$SCRIPT_DIR/../.venv/bin/python3"
if [ -f "$VENV_PYTHON" ]; then
    "$VENV_PYTHON" "$SCRIPT_DIR/05-init-sqlite-db.py"
else
    # Fallback caso o venv ainda não tenha sido criado por algum motivo
    python3 "$SCRIPT_DIR/05-init-sqlite-db.py"
fi

# Etapa 06: Instalação das Tarefas Cron
echo "--- [06/06] Instalando Tarefas no Cron ---"
sh "$SCRIPT_DIR/06-install-cron.sh"

echo ""
echo "------------------------------------------------------------"
echo "✅ CONFIGURAÇÃO COMPLETA REALIZADA COM SUCESSO!"
echo "------------------------------------------------------------"
echo "Para ativar o ambiente virtual: source .venv/bin/activate"
echo "Verifique as tarefas agendadas: crontab -l"
echo "------------------------------------------------------------"
echo ""
