# Graph Report - 9_ALPINE_GENERAL  (2026-07-11)

## Corpus Check
- 94 files · ~40,185 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 525 nodes · 872 edges · 109 communities (33 shown, 76 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.55)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0f5cfbe8`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

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
- 🛠️ Detalhes das Alterações
- Guia de Comissionamento: Dashboard Web Local
- Regras e Convenções do Projeto Piscicultura (general-system)
- Arquitetura do Sistema
- Estratégia de Backup: Mentoria e Planejamento
- Estratégia de Backup: Mentoria e Planejamento
- Project State (AI Context Compression)
- Roadmap do Projeto
- Catálogos do Sistema
- Comandos do Telegram para Monitoramento
- Modelo de Crontab para Alpine Linux
- 05-init-sqlite-db.py
- 12-start-web.sh
- set_test_environment
- TestReportSecurity
- graphify.md
- graphify.md
- check_network_health.sh
- run_tests.sh
- Segregação SQLite e PostgreSQL
- Consolidação (Migração) de Dados
- Monitoramento & Alertas
- Noctua IoT Scraping
- Backup Remoto com Cloudflare R2
- Restauração de Backup
- Cron: Manutenção e Inicialização
- Biometria Entity
- Clima Histórico Entity
- Leituras Entity
- Lotes Entity
- Propriedade Entity
- Proprietário Entity
- Qualidade da Água - Consumo Entity
- Qualidade da Água - Limnologia Entity
- Tipo Exploração Entity
- Usuários Telegram Entity
- Aiogram Telegram Bot
- PostgreSQL
- Runtime Python 3.12
- SQLite (Borda)
- Alertas Automáticos Push
- Cloudflare R2
- pg_dump
- Active Batch Isolation
- Biometria
- Ficha Verde (Green Sheet)
- Histórico de Pareceres da IA
- Qualidade de Água
- Watchdog Resilience
- Predição de Arraçoamento com IA
- src/jobs/migrate_data.py
- 🛠️ Detalhes das Alterações
- TestAgentFallback
- run_migration

## God Nodes (most connected - your core abstractions)
1. `get_sqlite_connection()` - 51 edges
2. `get_postgres_connection()` - 43 edges
3. `get_all_estruturas_map()` - 33 edges
4. `send_telegram_message()` - 29 edges
5. `main()` - 26 edges
6. `send_telegram_photo()` - 26 edges
7. `analyze_custom_report_sync()` - 20 edges
8. `is_system_suspended()` - 15 edges
9. `get_weather_forecast()` - 15 edges
10. `handle_messages()` - 14 edges

## Surprising Connections (you probably didn't know these)
- `migrate_sqlite()` --calls--> `get_sqlite_connection()`  [EXTRACTED]
  scripts/migrate_add_cloud_cover.py → src/services/database.py
- `migrate_postgres()` --calls--> `get_postgres_connection()`  [EXTRACTED]
  scripts/migrate_add_cloud_cover.py → src/services/database.py
- `main()` --calls--> `get_driver()`  [EXTRACTED]
  scripts/scrape_produtor.py → src/scrape/monitor_data.py
- `test_clima_historico_table_exists()` --calls--> `get_sqlite_connection()`  [EXTRACTED]
  tests/test_weather_sync.py → src/services/database.py
- `test_hourly_report_includes_weather()` --calls--> `get_sqlite_connection()`  [EXTRACTED]
  tests/test_weather_sync.py → src/services/database.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Fluxo de Coleta e Monitoramento de Telemetria** — docs_architecture_noctua_iot_scraping, docs_architecture_monitoramento_alertas, docs_architecture_consolidacao_migracao, docs_mer_leituras [INFERRED 0.85]
- **Monitoramento de Qualidade da Água** — docs_mer_qualidade_agua_limnologia, docs_mer_qualidade_agua_consumo, docs_tech_stack_stack_aiogram [INFERRED 0.85]
- **Web Application Frontend Templates** — src_web_templates_base, src_web_templates_dashboard, src_web_templates_login [EXTRACTED 1.00]
- **Backup and DB Persistence Layer** — knowledge_backups_guide, knowledge_estrategia_backup_manus, src_services_database [INFERRED 0.85]
- **System Monitoring and Self-Healing watchdog flow** — scripts_check_network_health, scripts_14_watchdog_resilience, src_alerts_alert_check, src_alerts_offline_check [INFERRED 0.85]

## Communities (109 total, 76 thin omitted)

### Community 0 - "Agent & Alert System"
Cohesion: 0.07
Nodes (71): AgentExecutor, migrate_postgres(), migrate_sqlite(), check_alerts(), Verifica as últimas leituras no banco de dados e dispara alertas se necessário., check_last_reading(), Verifica o tempo da última leitura dos tanques.      Envia alerta se o atraso fo, run_production_logic() (+63 more)

### Community 1 - "Telegram Bot & Database Operations"
Cohesion: 0.07
Nodes (68): CallbackQuery, InlineKeyboardMarkup, Message, Pool, criar_lote_completo(), finalizar_lote_abate(), get_estruturas_ativas(), get_lote_por_estrutura() (+60 more)

### Community 2 - "Dashboard Web & Data Migration"
Cohesion: 0.06
Nodes (37): migrate_data(), Migra dados do SQLite para o PostgreSQL., format_morning_report(), main(), Formata o relatório de bom dia com clima detalhado., get_weather_forecast(), log_weather_locally(), Sessão customizada para impor um timeout limite nas requisições HTTP. (+29 more)

### Community 3 - "Weather Sync & Reports"
Cohesion: 0.18
Nodes (12): get_hourly_report(), Gera o relatório estatístico das últimas leituras para cada tanque., Obtém o clima atual e salva na tabela clima_historico., sync_hourly_weather(), Garante que get_hourly_report exclui dados de tanques sem lote ativo no Postgres, test_hourly_report_filters_inactive_batches(), Verifica se a tabela clima_historico foi criada no SQLite., Verifica se o job de sincronização salva dados no banco. (+4 more)

### Community 4 - "Project Logs & System Setup"
Cohesion: 0.29
Nodes (5): format_data_summary_micro(), Versão condensada da lógica que iremos implementar no feed_prediction.py, Valida se o resumo de dados é realmente curto (Micro-contexto)., Testa a nova função do agente (mockada)., TestFeedPredictionAgent

### Community 5 - "Device MAC Configuration & Scraper"
Cohesion: 0.16
Nodes (16): main(), Atualiza as variáveis STRUCT_MACS, STRUCT_NAME e STRUCT_PLUSCODE no arquivo .env, update_env_file(), main(), get_configured_macs(), get_driver(), Carrega os MACs configurados localmente no .env no formato Nome:MAC., Configura o driver do Chrome em modo headless com fallback de localização e otim (+8 more)

### Community 6 - "Database MER Entities & Catalogs"
Cohesion: 0.18
Nodes (10): Biometria e Qualidade da Água, Clima Histórico, Diagrama, Entidades de Cadastro, Estrutura, Leituras (Telemetria), Lotes (Ciclo de Vida), Modelo de Entidade Relacionamento (MER) (+2 more)

### Community 8 - "Database Initialization Scripts"
Cohesion: 0.31
Nodes (9): generate_sha256(), get_env_data(), main(), populate_postgres(), populate_sqlite(), Popula o SQLite com os dados do .env., Gera um hash SHA256 a partir de uma string., Recupera e valida dados de cadastro do .env, suportando múltiplas estruturas. (+1 more)

### Community 9 - "Database Restoration & Cloudflare R2"
Cohesion: 0.25
Nodes (7): RCLONE_CONFIG_R2_ACCESS_KEY_ID, RCLONE_CONFIG_R2_ACL, RCLONE_CONFIG_R2_ENDPOINT, RCLONE_CONFIG_R2_PROVIDER, RCLONE_CONFIG_R2_SECRET_ACCESS_KEY, RCLONE_CONFIG_R2_TYPE, 13-restore-db.sh script

### Community 11 - "Gompertz Growth Curves & Plotting"
Cohesion: 0.20
Nodes (9): 1. Correção de Resolução de DNS Local (Pi-hole), 2. Validação e Monitoramento de Rede e IP Estático, 3. Filtragem Dinâmica de Lotes Ativos, 4. Correções e Estabilidade na Suíte de Testes (TDD), 5. Limpeza de Dados Legados no SQLite Local, 🛠️ Detalhes das Alterações, Diário de Bordo — 27 de Junho de 2026, 📋 Resumo do Dia (+1 more)

### Community 15 - "System Maintenance Scripts"
Cohesion: 0.40
Nodes (4): PG_HOST, PG_PORT, PYTHONPATH, weekly_maintenance.sh script

### Community 16 - "Tank Reading Monitors"
Cohesion: 0.22
Nodes (8): 1. Premissas e Custos (Free Tier), 2. Configuração no Painel da Cloudflare, 3. Configuração do Ambiente (.env), 4. Execução do Backup, 5. Código de Contingência: Restauração em Novo Comissionamento, Agendamento (Cron), O que este script faz:, Tutorial: Backup e Restauração com Cloudflare R2

### Community 17 - "Gemini AI Integrations"
Cohesion: 0.67
Nodes (3): Google Gemini IA, Telegram Bot UI, src/bots/requirements.txt

### Community 26 - "Runtime Python 3.12 Component"
Cohesion: 0.12
Nodes (14): 1. Linguagem e Runtime, 2. Backend e Interface Web, 3. Inteligência Artificial e Automação, 4. Banco de Dados, 5. Interface de Usuário e Notificações, 6. Infraestrutura e Operação, 7. Qualidade de Código e Testes, Stack Tecnológica - Projeto Piscicultura (+6 more)

### Community 55 - "🛠️ Detalhes das Alterações"
Cohesion: 0.22
Nodes (8): 1. Ajuste e Reconstrução do Ambiente de Desenvolvimento (`.venv`), 2. Estabilização e Resolução de Conflitos na Suíte de Testes (TDD), 3. Melhoria no Truncamento de Pareceres no Banco de Dados, 4. Validação na Produção (`peixe`), 🛠️ Detalhes das Alterações, Diário de Bordo — 28 de Junho de 2026, 📋 Resumo do Dia, 📈 Status da Suíte de Testes

### Community 56 - "Guia de Comissionamento: Dashboard Web Local"
Cohesion: 0.25
Nodes (7): 1. Pré-requisitos, 2. Configuração do Ambiente (.env), 3. Instalação de Dependências, 4. Inicialização do Serviço, 5. Verificação e Testes, 6. Logs e Solução de Problemas, Guia de Comissionamento: Dashboard Web Local

### Community 57 - "Regras e Convenções do Projeto Piscicultura (general-system)"
Cohesion: 0.29
Nodes (6): 1. Regra de Filtragem de Lotes Ativos (Urgente/Crítico), 2. Segregação SQLite (Borda) e PostgreSQL (Histórico), 3. Fluxo de Trabalho (Deploy via Git), 4. Infraestrutura de Rede e DNS, 5. Organização de Diários de Bordo (Diários), Regras e Convenções do Projeto Piscicultura (general-system)

### Community 58 - "Arquitetura do Sistema"
Cohesion: 0.33
Nodes (5): 1. Visão Geral & Infraestrutura, 2. Escolhas Tecnológicas Principais, 3. Estrutura Modular (`src/`), 4. Fluxo de Dados, Arquitetura do Sistema

### Community 59 - "Estratégia de Backup: Mentoria e Planejamento"
Cohesion: 0.33
Nodes (5): 1. O Conceito: Por que Cloudflare R2?, 2. Fluxo Planejado, 3. Pré-requisitos (Sua tarefa de casa), 4. Próximos Passos Técnicos (Quando você estiver pronto), Estratégia de Backup: Mentoria e Planejamento

### Community 60 - "Estratégia de Backup: Mentoria e Planejamento"
Cohesion: 0.33
Nodes (5): 1. O Conceito: Por que Cloudflare R2?, 2. Fluxo Planejado, 3. Pré-requisitos (Sua tarefa de casa), 4. Próximos Passos Técnicos (Quando você estiver pronto), Estratégia de Backup: Mentoria e Planejamento

### Community 61 - "Project State (AI Context Compression)"
Cohesion: 0.33
Nodes (5): Core Data Flow, Critical Knowledge & Recent Fixes, Domain Concepts, Project State (AI Context Compression), Tech Stack & Runtime

### Community 62 - "Roadmap do Projeto"
Cohesion: 0.40
Nodes (4): ✅ Concluído (Q2 2026), 🚀 Próximos Passos (Q3 2026), Roadmap do Projeto, 🔮 Visão de Longo Prazo (Q4 2026+)

### Community 63 - "Catálogos do Sistema"
Cohesion: 0.50
Nodes (3): Catálogos do Sistema, Tipos de Exploração, Unidades de Medida Sugeridas

### Community 64 - "Comandos do Telegram para Monitoramento"
Cohesion: 0.50
Nodes (3): Alertas Automáticos (Push):, Comandos Disponíveis:, Comandos do Telegram para Monitoramento

### Community 106 - "🛠️ Detalhes das Alterações"
Cohesion: 0.22
Nodes (8): 1. Auditoria e Grafo de Conhecimento (`graphify`), 2. Sistema de Suspensão de Telemetria e Alertas, 3. Interface de Comandos do Telegram, 4. Deploy no Servidor de Produção (`peixe`), 🛠️ Detalhes das Alterações, Diário de Bordo — 11 de Julho de 2026, 📋 Resumo do Dia, 📈 Status da Suíte de Testes

## Knowledge Gaps
- **157 isolated node(s):** `aliases.sh script`, `11-backup-db.sh script`, `PGPASSWORD`, `02-setup-venv.sh script`, `03-install-python-deps.sh script` (+152 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **76 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_sqlite_connection()` connect `Agent & Alert System` to `Dashboard Web & Data Migration`, `Weather Sync & Reports`, `Device MAC Configuration & Scraper`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `get_weather_forecast()` connect `Dashboard Web & Data Migration` to `Telegram Bot & Database Operations`, `Weather Sync & Reports`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Why does `get_postgres_connection()` connect `Agent & Alert System` to `Dashboard Web & Data Migration`, `Weather Sync & Reports`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Are the 25 inferred relationships involving `main()` (e.g. with `callback_agua_uid()` and `callback_bio_finish()`) actually correct?**
  _`main()` has 25 INFERRED edges - model-reasoned connections that need verification._
- **What connects `aliases.sh script`, `11-backup-db.sh script`, `PGPASSWORD` to the rest of the system?**
  _239 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Agent & Alert System` be split into smaller, more focused modules?**
  _Cohesion score 0.07278835386338185 - nodes in this community are weakly interconnected._
- **Should `Telegram Bot & Database Operations` be split into smaller, more focused modules?**
  _Cohesion score 0.07364185110663984 - nodes in this community are weakly interconnected._