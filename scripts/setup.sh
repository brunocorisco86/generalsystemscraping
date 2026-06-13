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
VENV_PYTHON="$SCRIPT_DIR/../.venv/bin/python3"
if [ -f "$VENV_PYTHON" ]; then
    "$VENV_PYTHON" "$SCRIPT_DIR/05-init-sqlite-db.py"
else
    # Fallback caso o venv ainda não tenha sido criado por algum motivo
    python3 "$SCRIPT_DIR/05-init-sqlite-db.py"
fi

# Etapa 06: Instalação das Tarefas Cron
sh "$SCRIPT_DIR/06-install-cron.sh"

# Etapa 15 (Opcional): Autocomissionamento de MAC Addresses
ENV_FILE="$SCRIPT_DIR/../.env"
if [ -f "$ENV_FILE" ]; then
    EMAIL=$(grep 'LOGIN_EMAIL' "$ENV_FILE" | cut -d '=' -f2- | sed 's/^[ 	]*//;s/[ 	]*$//' | tr -d '"' | tr -d "'")
    if [ ! -z "$EMAIL" ] && [ "$EMAIL" != "seu_email@exemplo.com" ]; then
        echo ""
        echo "------------------------------------------------------------"
        echo "Deseja rodar o autocomissionamento de MAC addresses agora? [S/n]"
        read -r run_macs
        if [ "$run_macs" != "n" ] && [ "$run_macs" != "N" ]; then
            chmod +x "$SCRIPT_DIR/15-auto-configure-macs.sh"
            chmod +x "$SCRIPT_DIR/15-auto-configure-macs.py"
            sh "$SCRIPT_DIR/15-auto-configure-macs.sh" || echo "⚠️ Aviso: Autocomissionamento falhou, mas o setup continuará."
        fi
    fi
fi

echo ""
echo "------------------------------------------------------------"
echo "✅ CONFIGURAÇÃO COMPLETA REALIZADA COM SUCESSO!"
echo "------------------------------------------------------------"
echo "Para ativar o ambiente virtual: source .venv/bin/activate"
echo "Verifique as tarefas agendadas: crontab -l"
echo "------------------------------------------------------------"
echo ""
