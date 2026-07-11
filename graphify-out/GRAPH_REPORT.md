# Graph Report - .  (2026-07-11)

## Corpus Check
- Corpus is ~38,954 words - fits in a single context window. You may not need a graph.

## Summary
- 406 nodes · 813 edges · 55 communities (27 shown, 28 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 46 edges (avg confidence: 0.67)
- Token cost: 43,400 input · 6,700 output

## Community Hubs (Navigation)
- Agent & Alert System
- Telegram Bot & Database Operations
- Dashboard Web & Data Migration
- Weather Sync & Reports
- Project Logs & System Setup
- Device MAC Configuration & Scraper
- Database MER Entities & Catalogs
- AI Context & Watchdog Resilience
- Database Initialization Scripts
- Database Restoration & Cloudflare R2
- Architecture, Postgres & SQLite
- Gompertz Growth Curves & Plotting
- Database Tools & Python Reports
- Backup Strategy & Execution
- Docker Services & Backup Restoration
- System Maintenance Scripts
- Tank Reading Monitors
- Gemini AI Integrations
- Telegram Bot Menu & Setup
- Database Backup Execution
- 01-system-deps Component
- init db Component
- test env Component
- aliases Component
- Cron: Alertas Críticos Component
- Google Gemini API & LangChain Component
- Runtime Python 3.12 Component
- 02-setup-venv Component
- 03-install-python-deps Component
- 04-setup-env-file Component
- 06-install-cron Component
- 07-start-containers Component
- 08-fix-permissions Component
- 09-cleanup-logs Component
- 10-maintenance-docker Component
- 15-auto-configure-macs script Component
- setup Component
- Fluxo de Deploy via Git Component
- Infraestrutura de Rede e DNS Component
- Auto-recuperação & Resiliência Component
- Unidades de Medida Component
- Cron: Monitoramento e Coleta Component
- Cron: Relatórios e Análises Component
- Flask Web App Component
- Selenium & ChromeDriver Component
- Development Requirements Dependencies Component
- Requirements Dependencies Component

## God Nodes (most connected - your core abstractions)
1. `get_sqlite_connection()` - 51 edges
2. `get_postgres_connection()` - 43 edges
3. `get_all_estruturas_map()` - 33 edges
4. `send_telegram_message()` - 28 edges
5. `send_telegram_photo()` - 26 edges
6. `main()` - 24 edges
7. `analyze_custom_report_sync()` - 20 edges
8. `get_weather_forecast()` - 15 edges
9. `Project State (AI Context Compression)` - 14 edges
10. `handle_messages()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `migrate_sqlite()` --calls--> `get_sqlite_connection()`  [EXTRACTED]
  scripts/migrate_add_cloud_cover.py → src/services/database.py
- `migrate_postgres()` --calls--> `get_postgres_connection()`  [EXTRACTED]
  scripts/migrate_add_cloud_cover.py → src/services/database.py
- `main()` --calls--> `get_driver()`  [EXTRACTED]
  scripts/scrape_produtor.py → src/scrape/monitor_data.py
- `test_alert_check_filters_inactive_batches()` --calls--> `check_alerts()`  [EXTRACTED]
  tests/test_alert_check_filter.py → src/alerts/alert_check.py
- `test_clima_historico_table_exists()` --calls--> `get_sqlite_connection()`  [EXTRACTED]
  tests/test_weather_sync.py → src/services/database.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Fluxo de Coleta e Monitoramento de Telemetria** — docs_architecture_noctua_iot_scraping, docs_architecture_monitoramento_alertas, docs_architecture_consolidacao_migracao, docs_mer_leituras [INFERRED 0.85]
- **Monitoramento de Qualidade da Água** — docs_mer_qualidade_agua_limnologia, docs_mer_qualidade_agua_consumo, docs_tech_stack_stack_aiogram [INFERRED 0.85]
- **Web Application Frontend Templates** — src_web_templates_base, src_web_templates_dashboard, src_web_templates_login [EXTRACTED 1.00]
- **Backup and DB Persistence Layer** — knowledge_backups_guide, knowledge_estrategia_backup_manus, src_services_database [INFERRED 0.85]
- **System Monitoring and Self-Healing watchdog flow** — scripts_check_network_health, scripts_14_watchdog_resilience, src_alerts_alert_check, src_alerts_offline_check [INFERRED 0.85]

## Communities (55 total, 28 thin omitted)

### Community 0 - "Agent & Alert System"
Cohesion: 0.10
Nodes (55): AgentExecutor, migrate_postgres(), migrate_sqlite(), check_alerts(), Verifica as últimas leituras no banco de dados e dispara alertas se necessário., run_production_logic(), generate_prediction(), get_historical_value() (+47 more)

### Community 1 - "Telegram Bot & Database Operations"
Cohesion: 0.08
Nodes (64): CallbackQuery, InlineKeyboardMarkup, Message, Pool, criar_lote_completo(), finalizar_lote_abate(), get_estruturas_ativas(), get_lote_por_estrutura() (+56 more)

### Community 2 - "Dashboard Web & Data Migration"
Cohesion: 0.08
Nodes (28): Guia de Comissionamento: Dashboard Web Local, Roadmap do Projeto, PYTHONPATH, 12-start-web.sh script, migrate_data(), Migra dados do SQLite para o PostgreSQL., get_user_by_id(), init_web_auth_db() (+20 more)

### Community 3 - "Weather Sync & Reports"
Cohesion: 0.09
Nodes (25): get_hourly_report(), Gera o relatório estatístico das últimas leituras para cada tanque., Obtém o clima atual e salva na tabela clima_historico., sync_hourly_weather(), format_morning_report(), main(), Formata o relatório de bom dia com clima detalhado., get_weather_forecast() (+17 more)

### Community 4 - "Project Logs & System Setup"
Cohesion: 0.08
Nodes (17): Diário de Bordo — 27 de Junho de 2026, Diário de Bordo — 28 de Junho de 2026, init_sqlite(), Inicializa o banco de dados SQLite local com o novo MER., check_network_health.sh script, run_tests.sh script, Garante que o ambiente esteja apontando para testes e injeta PROJECT_ROOT.     C, set_test_environment() (+9 more)

### Community 5 - "Device MAC Configuration & Scraper"
Cohesion: 0.16
Nodes (16): main(), Atualiza as variáveis STRUCT_MACS, STRUCT_NAME e STRUCT_PLUSCODE no arquivo .env, update_env_file(), main(), get_configured_macs(), get_driver(), Carrega os MACs configurados localmente no .env no formato Nome:MAC., Configura o driver do Chrome em modo headless com fallback de localização e otim (+8 more)

### Community 6 - "Database MER Entities & Catalogs"
Cohesion: 0.20
Nodes (12): Tipos de Exploração, Biometria Entity, Clima Histórico Entity, Estrutura Entity, Leituras Entity, Lotes Entity, Propriedade Entity, Proprietário Entity (+4 more)

### Community 7 - "AI Context & Watchdog Resilience"
Cohesion: 0.24
Nodes (9): Project State (AI Context Compression), Active Batch Isolation, Biometria, Ficha Verde (Green Sheet), Histórico de Pareceres da IA, Qualidade de Água, Watchdog Resilience, 14-watchdog-resilience.sh script (+1 more)

### Community 8 - "Database Initialization Scripts"
Cohesion: 0.31
Nodes (9): generate_sha256(), get_env_data(), main(), populate_postgres(), populate_sqlite(), Popula o SQLite com os dados do .env., Gera um hash SHA256 a partir de uma string., Recupera e valida dados de cadastro do .env, suportando múltiplas estruturas. (+1 more)

### Community 9 - "Database Restoration & Cloudflare R2"
Cohesion: 0.25
Nodes (7): RCLONE_CONFIG_R2_ACCESS_KEY_ID, RCLONE_CONFIG_R2_ACL, RCLONE_CONFIG_R2_ENDPOINT, RCLONE_CONFIG_R2_PROVIDER, RCLONE_CONFIG_R2_SECRET_ACCESS_KEY, RCLONE_CONFIG_R2_TYPE, 13-restore-db.sh script

### Community 10 - "Architecture, Postgres & SQLite"
Cohesion: 0.33
Nodes (7): Regra de Filtragem de Lotes Ativos, Segregação SQLite e PostgreSQL, Consolidação (Migração) de Dados, Monitoramento & Alertas, Noctua IoT Scraping, PostgreSQL, SQLite (Borda)

### Community 11 - "Gompertz Growth Curves & Plotting"
Cohesion: 0.43
Nodes (6): ajustar_gompertz(), ajustar_reta(), gerar_curva(), metricas_reta(), modelo_gompertz(), Ajuste linear simples: y = a*x + b     Retorna coeficientes a, b.

### Community 12 - "Database Tools & Python Reports"
Cohesion: 0.29
Nodes (6): execute_python_report(), query_postgres(), Aciona o script de migração de dados do SQLite (onde os dados brutos chegam) par, Executa uma consulta SELECT de leitura no banco de dados PostgreSQL e retorna os, Executa um script Python da pasta src/reports/ e retorna o resultado no terminal, run_migration()

### Community 13 - "Backup Strategy & Execution"
Cohesion: 0.53
Nodes (5): Guia de Backups, Cloudflare R2, pg_dump, Estratégia de Backup: Mentoria e Planejamento, 11-backup-db.sh script

### Community 14 - "Docker Services & Backup Restoration"
Cohesion: 0.40
Nodes (5): Bot Unificado Container Service, PostgreSQL Container Service, Backup Remoto com Cloudflare R2, Restauração de Backup, Cron: Manutenção e Inicialização

### Community 15 - "System Maintenance Scripts"
Cohesion: 0.40
Nodes (4): PG_HOST, PG_PORT, PYTHONPATH, weekly_maintenance.sh script

### Community 16 - "Tank Reading Monitors"
Cohesion: 0.50
Nodes (4): check_last_reading(), Verifica o tempo da última leitura dos tanques.      Envia alerta se o atraso fo, Garante que check_last_reading não gera alertas offline para tanques sem lote at, test_offline_check_filters_inactive_batches()

### Community 17 - "Gemini AI Integrations"
Cohesion: 0.67
Nodes (3): Google Gemini IA, Telegram Bot UI, src/bots/requirements.txt

### Community 18 - "Telegram Bot Menu & Setup"
Cohesion: 0.67
Nodes (3): Configuração do Menu do Bot no BotFather, Aiogram Telegram Bot, Comandos Manuais do Telegram

## Knowledge Gaps
- **60 isolated node(s):** `aliases.sh script`, `11-backup-db.sh script`, `PGPASSWORD`, `02-setup-venv.sh script`, `03-install-python-deps.sh script` (+55 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **28 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_sqlite_connection()` connect `Agent & Alert System` to `Tank Reading Monitors`, `Dashboard Web & Data Migration`, `Weather Sync & Reports`, `Device MAC Configuration & Scraper`?**
  _High betweenness centrality (0.075) - this node is a cross-community bridge._
- **Why does `get_weather_forecast()` connect `Weather Sync & Reports` to `Telegram Bot & Database Operations`, `Dashboard Web & Data Migration`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Why does `get_postgres_connection()` connect `Agent & Alert System` to `Dashboard Web & Data Migration`, `Weather Sync & Reports`, `Gompertz Growth Curves & Plotting`, `Database Tools & Python Reports`, `Tank Reading Monitors`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **What connects `aliases.sh script`, `11-backup-db.sh script`, `PGPASSWORD` to the rest of the system?**
  _139 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Agent & Alert System` be split into smaller, more focused modules?**
  _Cohesion score 0.09837837837837837 - nodes in this community are weakly interconnected._
- **Should `Telegram Bot & Database Operations` be split into smaller, more focused modules?**
  _Cohesion score 0.0777928539122569 - nodes in this community are weakly interconnected._
- **Should `Dashboard Web & Data Migration` be split into smaller, more focused modules?**
  _Cohesion score 0.08235294117647059 - nodes in this community are weakly interconnected._