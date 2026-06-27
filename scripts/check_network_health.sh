#!/bin/sh
# scripts/check_network_health.sh: Network health check utility
# Logs current IP verification and local DNS resolution status.

LOG_FILE="/home/bruno/generalsystemscraping/logs/network_health.log"
EXPECTED_IP="192.168.1.99"
DNS_SERVER="192.168.1.7"
TEST_DOMAINS="peixe peixe.lan alpine.lan"

# Ensure the logs directory exists
mkdir -p "$(dirname "$LOG_FILE")"

echo "=== [$(date '+%Y-%m-%d %H:%M:%S')] Starting Network Health Check ===" >> "$LOG_FILE"

# 1. Verify static IP using ip -o -4 addr show (compatible with BusyBox)
CURRENT_IPS=$(ip -o -4 addr show 2>/dev/null | awk '{print $4}' | cut -d/ -f1)
IP_MATCH=0
for IP in $CURRENT_IPS; do
    if [ "$IP" = "$EXPECTED_IP" ]; then
        IP_MATCH=1
        break
    fi
done

if [ "$IP_MATCH" -eq 1 ]; then
    echo "[INFO] Static IP is correct: $EXPECTED_IP" >> "$LOG_FILE"
else
    echo "[ERROR] Expected static IP ($EXPECTED_IP) not found in current IPs: $CURRENT_IPS" >> "$LOG_FILE"
fi

# 2. Verify DNS resolution using the local DNS server
echo "[INFO] Testing DNS resolution via local DNS server ($DNS_SERVER)..." >> "$LOG_FILE"
DNS_FAILURES=0

for DOMAIN in $TEST_DOMAINS; do
    # Perform nslookup specifically querying the local DNS server
    RESOLVED_IP=$(nslookup "$DOMAIN" "$DNS_SERVER" 2>/dev/null | grep -A1 "Name:" | grep "Address:" | awk '{print $2}')
    if [ -z "$RESOLVED_IP" ]; then
        # fallback parsing for some nslookup/busybox versions
        RESOLVED_IP=$(nslookup "$DOMAIN" "$DNS_SERVER" 2>/dev/null | grep -A2 "Name:" | grep "Address 1:" | awk '{print $3}')
    fi

    if [ ! -z "$RESOLVED_IP" ]; then
        echo "[INFO] DNS Resolution SUCCESS: $DOMAIN -> $RESOLVED_IP" >> "$LOG_FILE"
    else
        echo "[ERROR] DNS Resolution FAILED for domain: $DOMAIN (DNS server: $DNS_SERVER)" >> "$LOG_FILE"
        DNS_FAILURES=$((DNS_FAILURES + 1))
    fi
done

if [ "$DNS_FAILURES" -eq 0 ]; then
    echo "[SUCCESS] All DNS resolution tests passed using local DNS server." >> "$LOG_FILE"
else
    echo "[FAILURE] $DNS_FAILURES DNS resolution test(s) failed." >> "$LOG_FILE"
fi

echo "=== [$(date '+%Y-%m-%d %H:%M:%S')] Network Health Check Completed ===" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
