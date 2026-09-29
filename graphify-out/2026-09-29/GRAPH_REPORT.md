# Graph Report - generalsystemscraping  (2026-09-29)

## Corpus Check
- 109 files · ~59,976 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 782 nodes · 1323 edges · 123 communities (46 shown, 77 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 51 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `428f300a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- get_sqlite_connection
- main.py
- test_web_dashboard.py
- get_weather_forecast
- agent.py
- collect_via_api
- Tabelas de Monitoramento (Operacional)
- 14-watchdog-resilience.sh
- 08-populate-initial-data.py
- 13-restore-db.sh
- Regra de Filtragem de Lotes Ativos
- 🛠️ Detalhes das Alterações
- send_ntfy_message
- scripts/11-backup-db.sh
- Bot Unificado Container Service
- weekly_maintenance.sh
- Tutorial: Backup e Restauração com Cloudflare R2
- src/bots/requirements.txt
- Configuração do Menu do Bot no BotFather
- knowledge/scripts/11-backup-db.sh
- 01-system-deps.sh
- NoctuaClient
- test_environment_is_isolated
- aliases.sh
- Cron: Alertas Críticos
- Google Gemini API & LangChain
- Stack Tecnológica - Projeto Piscicultura
- 02-setup-venv.sh
- 03-install-python-deps.sh
- 04-setup-env-file.sh
- 06-install-cron.sh
- 07-start-containers.sh
- 08-fix-permissions.sh
- 09-cleanup-logs.sh
- 10-maintenance-docker.sh
- 15-auto-configure-macs.sh script
- setup.sh
- Fluxo de Deploy via Git
- Infraestrutura de Rede e DNS
- Auto-recuperação & Resiliência (Watchdog)
- Unidades de Medida
- Cron: Monitoramento e Coleta
- Cron: Relatórios e Análises (Telegram)
- Flask Web App
- Selenium & ChromeDriver
- Development Requirements Dependencies
- Requirements Dependencies
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
- rules/graphify.md
- workflows/graphify.md
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
- 15-auto-configure-macs.py
- Ideação: integração direta com a API do Noctua IoT
- 🛠️ Ações Executadas
- ROADMAP DO PROJETO: TRANSIÇÃO NOCTUA IOT & CONTAINERIZAÇÃO
- noctua_diagnose.py
- Especificações Técnicas e Arquiteturais do Sistema (System Specifications)
- 🛠️ Ações Executadas
- route
- app.py
- TestPostgresConcurrency
- 🛠️ Ações Executadas
- api_endpoints_list
- api_get_endpoint
- api_mdm_estruturas
- api_update_thresholds
- api_update_timers

## God Nodes (most connected - your core abstractions)
1. `get_sqlite_connection()` - 55 edges
2. `get_postgres_connection()` - 53 edges
3. `get_all_estruturas_map()` - 33 edges
4. `send_telegram_message()` - 32 edges
5. `main()` - 27 edges
6. `send_telegram_photo()` - 26 edges
7. `NoctuaClient` - 25 edges
8. `analyze_custom_report_sync()` - 20 edges
9. `get_local_now()` - 16 edges
10. `is_system_suspended()` - 15 edges

## Surprising Connections (you probably didn't know these)
- `test_send_motor_command_unknown_endpoint()` --uses--> `NoctuaClientException`  [INFERRED]
  tests/test_noctua_client.py → src/services/noctua_client.py
- `test_send_motor_command_readonly_blocked()` --uses--> `NoctuaReadOnlyException`  [INFERRED]
  tests/test_noctua_client.py → src/services/noctua_client.py
- `test_update_thresholds_readonly_blocked()` --uses--> `NoctuaReadOnlyException`  [INFERRED]
  tests/test_noctua_client.py → src/services/noctua_client.py
- `test_update_timer_readonly_blocked()` --uses--> `NoctuaReadOnlyException`  [INFERRED]
  tests/test_noctua_client.py → src/services/noctua_client.py
- `migrate_sqlite()` --calls--> `get_sqlite_connection()`  [EXTRACTED]
  scripts/migrate_add_cloud_cover.py → src/services/database.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Web Application Frontend Templates** — src_web_templates_base, src_web_templates_dashboard, src_web_templates_login [EXTRACTED 1.00]
- **Backup and DB Persistence Layer** — knowledge_backups_guide, knowledge_estrategia_backup_manus, src_services_database [INFERRED 0.85]
- **Fluxo de Coleta e Monitoramento de Telemetria** — docs_architecture_noctua_iot_scraping, docs_architecture_monitoramento_alertas, docs_architecture_consolidacao_migracao, docs_mer_leituras [INFERRED 0.85]
- **System Monitoring and Self-Healing watchdog flow** — scripts_check_network_health, scripts_14_watchdog_resilience, src_alerts_alert_check, src_alerts_offline_check [INFERRED 0.85]
- **Monitoramento de Qualidade da Água** — docs_mer_qualidade_agua_limnologia, docs_mer_qualidade_agua_consumo, docs_tech_stack_stack_aiogram [INFERRED 0.85]

## Communities (123 total, 77 thin omitted)

### Community 0 - "get_sqlite_connection"
Cohesion: 0.06
Nodes (77): datetime, migrate_postgres(), migrate_sqlite(), check_alerts(), Verifica as últimas leituras no banco de dados e dispara alertas se necessário., check_last_reading(), Verifica o tempo da última leitura dos tanques. Envia alerta se o atraso for…, run_production_logic() (+69 more)

### Community 1 - "main.py"
Cohesion: 0.07
Nodes (73): asyncio, CallbackQuery, InlineKeyboardMarkup, Message, Pool, criar_lote_completo(), finalizar_lote_abate(), get_estruturas_ativas() (+65 more)

### Community 2 - "test_web_dashboard.py"
Cohesion: 0.08
Nodes (22): init_web_auth_db(), Inicializa a tabela de usuários web no SQLite., auth_client(), client(), fixture, Garante que a página de lotes carrega para usuário autenticado., Verifica se a página de login carrega corretamente., Garante que a página de configurações carrega para usuário autenticado. (+14 more)

### Community 3 - "get_weather_forecast"
Cohesion: 0.16
Nodes (13): format_morning_report(), main(), Formata o relatório de bom dia com clima detalhado., get_weather_forecast(), log_weather_locally(), Sessão customizada para impor um timeout limite nas requisições HTTP., Salva os dados da previsão em um arquivo JSON local, sobrescrevendo o anterior…, Obtém a previsão do tempo utilizando a API Open-Meteo. Utiliza as coordenadas… (+5 more)

### Community 4 - "agent.py"
Cohesion: 0.07
Nodes (31): AgentExecutor, analyze_alert_data(), analyze_evening_report_sync(), analyze_feed_prediction_sync(), analyze_nightly_report_sync(), ask_agent(), get_agent_executor(), Função para bater papo livremente com o agente via bot do Telegram. (+23 more)

### Community 5 - "collect_via_api"
Cohesion: 0.14
Nodes (17): Exception, collect_via_api(), ensure_leituras_table(), Função principal de tomada de dados. Utiliza preferencialmente a API GraphQL…, Garante que a tabela de leituras exista com o schema correto., Realiza a coleta das leituras dos tanques diretamente via AWS AppSync GraphQL…, scrape_and_save(), generate_sha256() (+9 more)

### Community 6 - "Tabelas de Monitoramento (Operacional)"
Cohesion: 0.18
Nodes (10): Biometria e Qualidade da Água, Clima Histórico, Diagrama, Entidades de Cadastro, Estrutura, Leituras (Telemetria), Lotes (Ciclo de Vida), Modelo de Entidade Relacionamento (MER) (+2 more)

### Community 8 - "08-populate-initial-data.py"
Cohesion: 0.31
Nodes (9): generate_sha256(), get_env_data(), main(), populate_postgres(), populate_sqlite(), Popula o SQLite com os dados do .env., Gera um hash SHA256 a partir de uma string., Recupera e valida dados de cadastro do .env, suportando múltiplas estruturas. (+1 more)

### Community 9 - "13-restore-db.sh"
Cohesion: 0.25
Nodes (7): RCLONE_CONFIG_R2_ACCESS_KEY_ID, RCLONE_CONFIG_R2_ACL, RCLONE_CONFIG_R2_ENDPOINT, RCLONE_CONFIG_R2_PROVIDER, RCLONE_CONFIG_R2_SECRET_ACCESS_KEY, RCLONE_CONFIG_R2_TYPE, 13-restore-db.sh script

### Community 11 - "🛠️ Detalhes das Alterações"
Cohesion: 0.20
Nodes (9): 1. Correção de Resolução de DNS Local (Pi-hole), 2. Validação e Monitoramento de Rede e IP Estático, 3. Filtragem Dinâmica de Lotes Ativos, 4. Correções e Estabilidade na Suíte de Testes (TDD), 5. Limpeza de Dados Legados no SQLite Local, 🛠️ Detalhes das Alterações, Diário de Bordo — 27 de Junho de 2026, 📋 Resumo do Dia (+1 more)

### Community 12 - "send_ntfy_message"
Cohesion: 0.33
Nodes (6): Envia uma notificação push via ntfy.sh para o tópico configurado. Ultraleve,…, send_ntfy_message(), Valida se alertas do Telegram disparam automaticamente push para o ntfy.sh., Valida se o payload e headers do ntfy.sh são montados e enviados corretamente., test_send_ntfy_message_success(), test_send_telegram_mirrors_to_ntfy()

### Community 15 - "weekly_maintenance.sh"
Cohesion: 0.40
Nodes (4): PG_HOST, PG_PORT, PYTHONPATH, weekly_maintenance.sh script

### Community 16 - "Tutorial: Backup e Restauração com Cloudflare R2"
Cohesion: 0.22
Nodes (8): 1. Premissas e Custos (Free Tier), 2. Configuração no Painel da Cloudflare, 3. Configuração do Ambiente (.env), 4. Execução do Backup, 5. Código de Contingência: Restauração em Novo Comissionamento, Agendamento (Cron), O que este script faz:, Tutorial: Backup e Restauração com Cloudflare R2

### Community 21 - "NoctuaClient"
Cohesion: 0.07
Nodes (28): Any, main(), NoctuaClient, NoctuaClientException, NoctuaReadOnlyException, Exceção base para erros de comunicação ou regra de negócio com Noctua IoT., Disparada quando uma operação de escrita é tentada sob NOCTUA_READ_ONLY=true., Cliente HTTP síncrono para o AWS AppSync do Noctua IoT. (+20 more)

### Community 26 - "Stack Tecnológica - Projeto Piscicultura"
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

### Community 68 - "set_test_environment"
Cohesion: 0.50
Nodes (3): fixture, Garante que o ambiente esteja apontando para testes e injeta PROJECT_ROOT. Como…, set_test_environment()

### Community 106 - "🛠️ Detalhes das Alterações"
Cohesion: 0.22
Nodes (8): 1. Auditoria e Grafo de Conhecimento (`graphify`), 2. Sistema de Suspensão de Telemetria e Alertas, 3. Interface de Comandos do Telegram, 4. Deploy no Servidor de Produção (`peixe`), 🛠️ Detalhes das Alterações, Diário de Bordo — 11 de Julho de 2026, 📋 Resumo do Dia, 📈 Status da Suíte de Testes

### Community 107 - "15-auto-configure-macs.py"
Cohesion: 0.67
Nodes (3): main(), Atualiza as variáveis STRUCT_MACS, STRUCT_NAME e STRUCT_PLUSCODE no arquivo…, update_env_file()

### Community 108 - "Ideação: integração direta com a API do Noctua IoT"
Cohesion: 0.08
Nodes (24): 1. Consumir os dados atuais dos sensores, 2. Consumir dados históricos horários, 3. Consultar programação, thresholds e estado dos equipamentos, 4. Alterar threshold ou programação, 5. Acionar ou desligar motores, 6. Operações que devem ser implementadas no cliente, 7. Critérios mínimos de segurança, 8. Ordem recomendada de implementação (+16 more)

### Community 109 - "🛠️ Ações Executadas"
Cohesion: 0.15
Nodes (12): 1. Diagnóstico do Ecossistema e Alinhamento Arquitetural, 2. Criação do ROADMAP.md e Playbook do `.env`, 3. Implementação do Cliente GraphQL (`NoctuaClient`), 4. Saneamento do Coletor (`monitor_data.py`), 5. Expansão do Web Dashboard (Flask + Templates), 6. Script de Autodescoberta e Diagnóstico Dinâmico (`scripts/noctua_diagnose.py`), 7. Auditoria de Recursos e Conteinerização Multi-Serviço, 🛠️ Ações Executadas (+4 more)

### Community 110 - "ROADMAP DO PROJETO: TRANSIÇÃO NOCTUA IOT & CONTAINERIZAÇÃO"
Cohesion: 0.22
Nodes (8): Milestone 0: Preparação de Ambiente & Runbook do `.env`, Milestone 1: Cliente GraphQL & Saneamento da Tomada de Dados, Milestone 2: Gestão de Thresholds e Timers no Dashboard Web, Milestone 3: Acionamento Controlado de Motores (Safe Protocol), Milestone 4: Auditoria de Dependências & Conteinerização Completa, Milestone 5: Deploy e Homologação na VPS, ROADMAP DO PROJETO: TRANSIÇÃO NOCTUA IOT & CONTAINERIZAÇÃO, 📌 Visão Geral dos Marcos (Milestones)

### Community 111 - "noctua_diagnose.py"
Cohesion: 0.42
Nodes (7): Path, extract_graphql_urls(), extract_macs(), main(), read_env(), unique(), update_env()

### Community 112 - "Especificações Técnicas e Arquiteturais do Sistema (System Specifications)"
Cohesion: 0.08
Nodes (23): 1.1 Objetivos Principais, 1. Visão Geral e Escopo, 2. Arquitetura de Alto Nível, 3.1 SQLite (`data/piscicultura_dados.db`) - Camada de Borda e Cache Rápido, 3.2 PostgreSQL (`piscicultura_history`) - Camada Canônica e Histórico Transacional, 3. Modelo de Persistência e Dados, 4.1 Módulo Noctua IoT Client (`src/services/noctua_client.py`), 4.2 Módulo de Coleta e Ingestão (`src/scrape/monitor_data.py`) (+15 more)

### Community 113 - "🛠️ Ações Executadas"
Cohesion: 0.22
Nodes (8): 1. Auditoria e Varredura da Base de Código (Graphify & Análise Estática), 2. Validação da Suíte de Testes (TDD / CI), 3. Redação e Formalização das Especificações Técnicas (`docs/specs.md`), 4. Atualização de Referências e Documentação Cruzada, 🛠️ Ações Executadas, Diário de Bordo - 28/09/2026, 🎯 Objetivo da Sessão, 📌 Próximos Passos

### Community 114 - "route"
Cohesion: 0.11
Nodes (29): login_required, route, api_agent(), api_criar_lote(), api_fechar_lote(), api_get_lotes(), api_mdm_dados(), api_mdm_salvar_propriedade() (+21 more)

### Community 115 - "app.py"
Cohesion: 0.20
Nodes (9): get_user_by_id(), Valida as credenciais do usuário., Retorna dados do usuário pelo ID., validate_user(), load_user(), login(), User, user_loader (+1 more)

### Community 116 - "TestPostgresConcurrency"
Cohesion: 0.15
Nodes (10): pg_pool(), fixture, Valida inserções concorrentes de biometria e mortalidade para o mesmo lote sob…, Testa tentativa de fechamento concorrente garantindo atomicidade sem deadlocks., Pool de conexões thread-safe para testes de concorrência., Cria uma estrutura e um lote temporários dedicados para os testes de estresse., Suíte de Testes de Concorrência, Leitura e Escrita sob Carga no PostgreSQL., Valida que múltiplas threads simultâneas realizam leituras sem contenção ou… (+2 more)

### Community 117 - "🛠️ Ações Executadas"
Cohesion: 0.12
Nodes (15): 1. Front-End: Layout Base & Navegação, 2. Front-End: Interface de Batch Management (`lotes.html`), 3. Front-End: Interface de MDM & Settings (`settings.html`), 4. Backend Flask: Novas Rotas em `src/web/app.py`, 5. Suíte de Testes de Concorrência & Estresse, 🛡️ Auditoria de Recursos, Otimização de CPU & Ativação do Telegram Bot, 🛠️ Ações Executadas, 🕒 Correção de Fuso Horário (UTC vs Horário de Brasília) & Badge Offline (+7 more)

## Knowledge Gaps
- **226 isolated node(s):** `aliases.sh script`, `11-backup-db.sh script`, `PGPASSWORD`, `02-setup-venv.sh script`, `03-install-python-deps.sh script` (+221 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **77 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `NoctuaClient` connect `NoctuaClient` to `get_sqlite_connection`, `collect_via_api`, `app.py`, `api_get_endpoint`, `api_update_thresholds`, `api_update_timers`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Why does `get_sqlite_connection()` connect `get_sqlite_connection` to `test_web_dashboard.py`, `app.py`, `collect_via_api`, `route`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Why does `get_postgres_connection()` connect `get_sqlite_connection` to `api_mdm_estruturas`, `route`, `app.py`, `agent.py`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **What connects `aliases.sh script`, `11-backup-db.sh script`, `PGPASSWORD` to the rest of the system?**
  _226 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `get_sqlite_connection` be split into smaller, more focused modules?**
  _Cohesion score 0.062218515429524605 - nodes in this community are weakly interconnected._
- **Should `main.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06664388243335612 - nodes in this community are weakly interconnected._
- **Should `test_web_dashboard.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07936507936507936 - nodes in this community are weakly interconnected._