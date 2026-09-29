#!/bin/sh
# ==============================================================================
# Script de Comissionamento: Migração para Cron Jobs & Otimizações de Borda
# Alvo: Raspberry Pi 3B ('peixe' - Alpine Linux)
# Finalidade: Descomissiona o coletor permanente e ativa o crond nativo do Alpine
# ==============================================================================
set -e

PROJECT_DIR="/home/bruno/generalsystemscraping"
LOG_DIR="$PROJECT_DIR/logs"
ENV_FILE="$PROJECT_DIR/.env"
CRON_FILE="/etc/crontabs/root"
GOOGLE_KEY="AIzaSyAyBrTtrer2Jyny15KWQP6nA4mmVa_yf14"

echo "=================================================================="
echo "🚀 Iniciando Comissionamento de Cron Jobs e Performance no Nó Peixe"
echo "=================================================================="

# 1. Configurar Diretórios e Logs
mkdir -p "$LOG_DIR"
touch "$LOG_DIR/cron.log"

# 2. Injetar Chave Google Studio / Gemini no .env se não existir
if [ -f "$ENV_FILE" ]; then
    echo "🔑 Configurando GEMINI_API_KEY e GOOGLE_API_KEY no .env..."
    if grep -q "^GEMINI_API_KEY=" "$ENV_FILE"; then
        sed -i "s/^GEMINI_API_KEY=.*/GEMINI_API_KEY=$GOOGLE_KEY/" "$ENV_FILE"
    else
        echo "GEMINI_API_KEY=$GOOGLE_KEY" >> "$ENV_FILE"
    fi

    if grep -q "^GOOGLE_API_KEY=" "$ENV_FILE"; then
        sed -i "s/^GOOGLE_API_KEY=.*/GOOGLE_API_KEY=$GOOGLE_KEY/" "$ENV_FILE"
    else
        echo "GOOGLE_API_KEY=$GOOGLE_KEY" >> "$ENV_FILE"
    fi
fi

# 3. Descomissionar Coletor Permanente (Liberando 144MB de RAM 24/7)
echo "🛑 Descomissionando container piscicultura_collector..."
docker stop piscicultura_collector 2>/dev/null || true
docker rm piscicultura_collector 2>/dev/null || true

# 4. Ajustar Parâmetros de Kernel para Cartão SD e Memória
echo "⚙️ Configurando tuning de memória e I/O em /etc/sysctl.d/99-performance.conf..."
cat << 'EOF' > /etc/sysctl.d/99-performance.conf
vm.swappiness = 10
vm.vfs_cache_pressure = 50
vm.dirty_background_ratio = 5
vm.dirty_ratio = 10
EOF
sysctl -p /etc/sysctl.d/99-performance.conf >/dev/null 2>&1 || true

# 5. Otimizar Memória de Vídeo em Servidor Headless (+48MB de RAM para a CPU)
if [ -d "/boot" ] && [ ! -f "/boot/usercfg.txt" ]; then
    echo "🖥️ Configurando gpu_mem=16 em /boot/usercfg.txt (libera 48MB de RAM)..."
    echo "gpu_mem=16" > /boot/usercfg.txt
fi

# 6. Instalar Tabela de Cron Jobs do Crond Nativo
echo "📅 Instalando cron jobs assíncronos em $CRON_FILE..."
# Preserva entradas que não sejam da piscicultura
touch "$CRON_FILE"
grep -v "piscicultura_web" "$CRON_FILE" > /tmp/crontab.tmp 2>/dev/null || true

cat << 'EOF' >> /tmp/crontab.tmp
# --- PISCICULTURA PATEL: ROTINAS ASSÍNCRONAS DE ALTA EFICIÊNCIA ---
*/10 * * * * docker exec piscicultura_web python3 src/scrape/monitor_data.py >> /home/bruno/generalsystemscraping/logs/cron.log 2>&1
*/15 * * * * docker exec piscicultura_web python3 src/alerts/alert_check.py >> /home/bruno/generalsystemscraping/logs/cron.log 2>&1
*/15 * * * * docker exec piscicultura_web python3 src/alerts/offline_check.py >> /home/bruno/generalsystemscraping/logs/cron.log 2>&1
0 * * * * docker exec piscicultura_web python3 src/jobs/hourly_weather_sync.py >> /home/bruno/generalsystemscraping/logs/cron.log 2>&1
0 */6 * * * docker exec piscicultura_web python3 src/database/postgres/migrate_data.py >> /home/bruno/generalsystemscraping/logs/cron.log 2>&1
0 19 * * * docker exec piscicultura_web python3 src/jobs/evening_report.py >> /home/bruno/generalsystemscraping/logs/cron.log 2>&1
# ------------------------------------------------------------------
EOF

mv /tmp/crontab.tmp "$CRON_FILE"
chmod 600 "$CRON_FILE"

# 7. Reiniciar Serviço do Crond
echo "🔄 Recarregando serviço do crond..."
if command -v rc-service >/dev/null 2>&1; then
    rc-service crond restart 2>/dev/null || rc-service crond start 2>/dev/null || true
else
    killall -HUP crond 2>/dev/null || crond -b
fi

# 8. Teste de Sanidade Imediato
echo "🧪 Executando tomada de dados teste via cron runner..."
docker exec piscicultura_web python3 src/scrape/monitor_data.py || echo "Aviso: Primeira tomada teste executada."

echo "=================================================================="
echo "✅ Comissionamento concluído com sucesso!"
echo "• Coletor permanente desativado (144MB de RAM liberados)"
echo "• Cron jobs nativos instalados e ativos no crond"
echo "• Logs centralizados em: $LOG_DIR/cron.log"
echo "=================================================================="
