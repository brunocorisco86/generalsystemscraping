# Project State (AI Context Compression)

## Tech Stack & Runtime

- **OS**: Alpine Linux (ARM64) / Raspberry Pi 3B.
- **Python**: 3.11+ (venv managed by `scripts/setup.sh`).
- **Containers**: Docker Compose (PostgreSQL, Unified Telegram Bot).
- **Automation**: Telegram Command Interface -> Python Scripts.
- **Database**: Hybrid SQLite (Local/Edge cache) + PostgreSQL (Long-term history).
- **UI/UX**: Telegram Bots (Biometria, Qualidade da Água) + **Web Dashboard (Flask)** para controle manual.
- **AI Agent**: Google Gemini (via LangChain Tools) para chat livre, filtragem inteligente de alertas e **predição de arraçoamento (Parecer do Especialista)**.

## Core Data Flow

1. **Scrape**: `src/scrape/monitor_data.py` (via Selenium/Headless Chromium + BeautifulSoup) roda a cada 10 min via Cron. Realiza login, audita e confere os MACs do site (/produtor) contra o .env (detectando novos tanques) e raspa as telemetrias acessando diretamente as URLs dos tanques (eliminando o escaneamento do menu lateral). Persiste no SQLite local.
2. **Dashboard**: `src/web/app.py` (Flask) provides local visualization and manual triggers for scraping, synchronization, and AI analysis.
3. **Weather Sync**: `src/jobs/hourly_weather_sync.py` runs every hour (minuto 01) to persist ambient temp, pressure, and humidity to SQLite.
3. **Alerts**: `src/alerts/alert_check.py` and `offline_check.py` run every 15 min.
   - **AI Validation**: Critical alerts analyzed by Gemini.
4. **Feed Prediction**: `src/analysis/feed_prediction.py` (09:00 via Cron).
   - **Data Integration**: Combines water O2/Temp, ambient Temp/Pressure/Humidity.
   - **AI Specialist**: Generates a "Micro-Context" summary for Gemini, obtaining an expert recommendation on whether to feed or wait based on metabolism and environmental stress.
5. **Jobs**: `src/jobs/` handles periodic reporting and data migration (SQLite -> Postgres).

## Critical Knowledge & Recent Fixes

- **Migration Fix**: Ensured `init_db` and `migrate_data` run via `docker exec` in `07-start-containers.sh` to resolve host naming issues (`postgres`) on new Raspberry Pi deployments.
- **Weather Automation**: Consolidated to `hourly_weather_sync` (min 01) and `morning_weather_report` (07:05). Removed redundant weather service cron calls.
- **Feed Prediction Optimization**: Integrated water and ambient temperatures + atmospheric pressure. Added AI-driven icons (✅/⚠️) based on specialist's textual feedback (TDD verified).
- **Timezone Enforcement**: Todos os relatórios e comparações utilizam explicitamente `America/Sao_Paulo` (GMT-3) através da biblioteca `pytz` para garantir consistência entre servidor (UTC) e usuário local.
- **Active Batch Isolation & Control**: 
  - **Migração Seletiva**: O script `migrate_data.py` filtra as leituras, enviando ao PostgreSQL apenas telemetrias de estruturas com lotes ativos (`data_abate IS NULL`).
  - **Tabela de Controle**: Progresso do SQLite rastreado por `controle_migracao` (campo `ultimo_id_leituras`), impedindo o processamento repetitivo de telemetrias inativas.
  - **Telegram Bot, Relatórios, Alertas e Consultas**: O bot bloqueia lançamentos de biometria e qualidade de água para tanques sem lote ativo. Relatórios, análises, consultas do bot e alertas de oxigênio/offline (`alert_check.py` e `offline_check.py`) filtram e ignoram dinamicamente estruturas inativas (ex: "Tanque 1" e "N/A") para evitar falsos positivos e processamento desnecessário.
- **Environment**: All configuration resides in `.env`. Root path is dynamically detected.
- **Resilience and Hardware Troubleshooting (Jun 2026)**:
  - **Memory Limits (OOM)**: A ativação do Selenium/Chromedriver em servidores com pouca RAM (ex: ~1GB de RAM) pode causar travamento dos processos do Chrome e erros de timeout. Foi ativado e configurado um **Swapfile de 1GB** persistente no `/etc/fstab` (`/swapfile swap swap defaults 0 0`).
  - **DNS & Time Sync Loop (Tailscale)**: Falhas na control plane do Tailscale ou no DNS local (`100.100.100.100`) podem impedir o NTP de sincronizar o relógio. Com o relógio atrasado, conexões HTTPS com a control plane falham por expiração de certificado SSL, gerando um travamento circular.
  - **Watchdog Auto-Recuperação**: Implementado o script [14-watchdog-resilience.sh](file:///media/brunoconter/DOCUMENTOS2/9_ALPINE_GENERAL/scripts/14-watchdog-resilience.sh) (executado a cada 5 minutos pelo cron). Ele valida a resolução DNS (faz fallback temporário para `8.8.8.8` no `/etc/resolv.conf`), corrige o relógio do sistema buscando o Date Header via HTTP puro (Google) se o ano for menor que 2026, garante a ativação de swap e auto-reinicia o Web App Flask e o container Docker `peixe_patel_bot` se caírem.
  - **Mapeamento e Conferência de MAC Addresses**: Para evitar timeouts e quebras causadas pelo escaneamento dinâmico do menu lateral, o scraper agora lê os MACs estáticos configurados via `STRUCT_MACS` no `.env`. Ele realiza uma auditoria comparativa inicial no endpoint `/produtor` do site usando BeautifulSoup, emitindo alertas caso novos tanques sejam adicionados ao painel do Noctua IoT ou se tanques locais forem removidos no site, e navega diretamente para as URLs dos tanques.
  - **Autocomissionamento de MACs (scripts/15-*)**: Criada ferramenta interativa de setup integrada ao `setup.sh` que faz login no Noctua-IoT, extrai os MACs dos tanques e preenche automaticamente o campo `STRUCT_MACS` no `.env`.
  - **Correção de DNS Local e Pi-hole**: Mapeamento DNS local configurado no Pi-hole (`/etc/pihole/pihole.toml`) no servidor `alpine` (192.168.1.7), direcionando `peixe` e `peixe.lan` para 192.168.1.99, e `alpine.lan` para 192.168.1.7.
  - **Script de Validação de Rede**: Implementado e agendado o script `scripts/check_network_health.sh` via cron (diariamente às 02:00) para verificar se o IP estático está correto (192.168.1.99) e testar a resolução DNS local via `nslookup` contra o servidor DNS `alpine` (192.168.1.7). Os relatórios são salvos em `logs/network_health.log` e indicam sucesso total de resolução.
  - **Histórico de Pareceres da IA & Contexto Dinâmico**: O sistema persiste automaticamente os pareceres emitidos no PostgreSQL (`historico_pareceres_ia`) com limite aumentado para 500 caracteres (VARCHAR(500)), injetando cronologicamente os últimos 3 pareceres no prompt do sistema (`SYSTEM_PROMPT`) do Gemini para memória e contexto analítico.
  - **Estabilização da Suíte de Testes (TDD)**: Resolvida poluição de mocks em `sys.modules` e incompatibilidades do Pydantic no LangChain 0.2.x. O banco SQLite dummy (`data/test_dummy_db.sqlite`) passou a ser autoinicializado dinamicamente via `conftest.py` antes de rodar os testes.
  - **Sistema de Suspensão de Monitoramento (Jul 2026)**: Implementação de controle de suspensão de scraping, leituras, relatórios e alertas automáticos via comandos `/suspender` e `/reativar` no bot do Telegram. O estado suspenso interrompe todas as coletas e notificações periódicas, com exceção da notificação diária das 17h, que roda em modo de alerta especial caso existam lotes ativos não finalizados no Postgres. O monitoramento reativa-se de forma automática assim que um novo ciclo de lote é iniciado via `/novo_lote`.

## Domain Concepts

- **Ficha Verde (Green Sheet)**: Standardized data model for fish growth tracking.
- **Biometria**: Weight and health checks logged by users via bot.
- **Qualidade de Água**: Limnology (pH, Ammonia, Nitrite) and Consumption (Chlorine, ORP) metrics.

