#!/bin/sh
# scripts/14-watchdog-resilience.sh: Watchdog de resiliência do sistema
# Verifica e corrige DNS, Sincronização de Hora (NTP/HTTP fallback) e serviços críticos.

LOG_FILE="/home/bruno/generalsystemscraping/logs/watchdog.log"
echo "=== [$(date '+%Y-%m-%d %H:%M:%S')] Iniciando Verificação do Watchdog ===" >> "$LOG_FILE"

# 1. Verificar/Corrigir DNS
DNS_OK=1
nslookup google.com > /dev/null 2>&1 || DNS_OK=0

if [ "$DNS_OK" -eq 0 ]; then
    echo "[WARN] Falha na resolução de DNS. Tentando recuperar..." >> "$LOG_FILE"
    resolvconf -u >> "$LOG_FILE" 2>&1
    
    # Testa novamente
    nslookup google.com > /dev/null 2>&1 || DNS_OK=0
    if [ "$DNS_OK" -eq 0 ]; then
        echo "[ERROR] DNS continua falhando. Injetando nameservers públicos de emergência no /etc/resolv.conf..." >> "$LOG_FILE"
        echo -e "nameserver 8.8.8.8\nnameserver 1.1.1.1\nnameserver 100.100.100.100" > /etc/resolv.conf
    else
        echo "[INFO] DNS recuperado via resolvconf -u." >> "$LOG_FILE"
    fi
fi

# 2. Verificar/Corrigir Hora do Sistema (Evitar loop de expiração de certificado SSL no Tailscale)
YEAR=$(date +%Y)
if [ "$YEAR" -lt 2026 ]; then
    echo "[WARN] Data do sistema incorreta ($YEAR). Sincronizando relógio via HTTP puro (Google) para evitar falhas SSL..." >> "$LOG_FILE"
    
    # Obtém hora do Google via HTTP puro para ignorar TLS/SSL e DNS local se possível
    UTC_TIME=$(python3 -c "
import urllib.request, email.utils, sys
try:
    res = urllib.request.urlopen('http://google.com', timeout=10)
    date_str = res.headers.get('Date')
    if date_str:
        dt = email.utils.parsedate_to_datetime(date_str)
        print(dt.strftime('%Y-%m-%d %H:%M:%S'))
    else:
        sys.exit(1)
except Exception as e:
    print(f'ERRO: {e}', file=sys.stderr)
    sys.exit(1)
" 2>> "$LOG_FILE")
    
    if [ $? -eq 0 ] && [ ! -z "$UTC_TIME" ]; then
        date -u -s "$UTC_TIME" >> "$LOG_FILE" 2>&1
        echo "[INFO] Hora do sistema sincronizada com sucesso para UTC: $UTC_TIME" >> "$LOG_FILE"
        
        # Reinicia o Tailscale para reestabelecer conexões se necessário
        echo "[INFO] Reiniciando serviço Tailscale pós-ajuste de hora..." >> "$LOG_FILE"
        rc-service tailscale restart >> "$LOG_FILE" 2>&1
    else
        echo "[ERROR] Falha ao obter hora via HTTP do Google: $UTC_TIME" >> "$LOG_FILE"
    fi
fi

# 3. Garantir que o Swap está ativo
SWAP_ACTIVE=$(free -m | grep -i swap | awk '{print $2}')
if [ -z "$SWAP_ACTIVE" ] || [ "$SWAP_ACTIVE" -eq 0 ]; then
    echo "[WARN] Swap não está ativo. Ativando /swapfile..." >> "$LOG_FILE"
    if [ -f "/swapfile" ]; then
        swapon /swapfile >> "$LOG_FILE" 2>&1
    else
        echo "[ERROR] /swapfile não encontrado. Crie o swap primeiro." >> "$LOG_FILE"
    fi
fi

# 4. Verificar se o Web App (Flask) está rodando
if ! pgrep -f "src/web/app.py" > /dev/null; then
    echo "[WARN] Web App (Flask) não está rodando. Reiniciando..." >> "$LOG_FILE"
    cd /home/bruno/generalsystemscraping && nohup /home/bruno/generalsystemscraping/.venv/bin/python3 src/web/app.py >> /home/bruno/generalsystemscraping/logs/web.log 2>&1 &
fi

# 5. Verificar se o Bot Telegram está rodando
if ! docker ps --filter "name=peixe_patel_bot" --filter "status=running" | grep peixe_patel_bot > /dev/null; then
    echo "[WARN] Container peixe_patel_bot não está ativo. Reiniciando..." >> "$LOG_FILE"
    docker start peixe_patel_bot >> "$LOG_FILE" 2>&1
fi

echo "=== Verificação Concluída ===" >> "$LOG_FILE"
