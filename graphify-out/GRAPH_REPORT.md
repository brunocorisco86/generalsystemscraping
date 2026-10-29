# Graph Report - generalsystemscraping  (2026-10-28)

## Corpus Check
- 113 files · ~69,807 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 880 nodes · 1520 edges · 146 communities (54 shown, 84 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 53 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1806a719`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- get_sqlite_connection
- main.py
- test_web_dashboard.py
- get_weather_forecast
- test_feed_prediction_agent.py
- listar_contatos_whatsapp
- Tabelas de Monitoramento (Operacional)
- 14-watchdog-resilience.sh
- 08-populate-initial-data.py
- 13-restore-db.sh
- Regra de Filtragem de Lotes Ativos
- 🛠️ Detalhes das Alterações
- 🛠️ Ações Executadas
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
- 4. Especificações dos Módulos e Componentes
- Ideação: integração direta com a API do Noctua IoT
- 🛠️ Ações Executadas
- ROADMAP DO PROJETO: TRANSIÇÃO NOCTUA IOT & CONTAINERIZAÇÃO
- noctua_diagnose.py
- Especificações Técnicas e Arquiteturais do Sistema (System Specifications)
- 🛠️ Ações Executadas
- app.py
- collector_service.py
- TestPostgresConcurrency
- Diário de Bordo - 29/09/2026
- Monitoramento e Automação para Piscicultura
- monitor_data.py
- 5. Regras de Negócio Críticas
- 6. Infraestrutura, Containerização e Resiliência
- commission_cron_jobs.sh
- get_local_now
- sync_hourly_weather
- agent_tools.py
- manual_report.py
- 15-auto-configure-macs.py
- get_hourly_report
- get_estrutura_uid
- test_noctua_client.py
- web_auth.py
- User
- api_testar_contato_whatsapp
- auth_client
- Exception
- api_get_endpoint
- test_lotes_page_loads
- test_login_page_loads
- test_settings_page_loads
- test_api_settings_db_status_route
- test_subpath_reverse_proxy_support
- test_dashboard_redirect_without_login
- test_mdm_uid_cascade_proprietario_and_propriedade
- test_favicon_and_weather_card_markup
- test_api_endpoints_protected

## God Nodes (most connected - your core abstractions)
1. `get_sqlite_connection()` - 63 edges
2. `get_postgres_connection()` - 59 edges
3. `get_all_estruturas_map()` - 35 edges
4. `send_telegram_message()` - 33 edges
5. `main()` - 27 edges
6. `send_telegram_photo()` - 27 edges
7. `NoctuaClient` - 26 edges
8. `get_local_now()` - 20 edges
9. `analyze_custom_report_sync()` - 18 edges
10. `check_last_reading()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `test_send_motor_command_unknown_endpoint()` --uses--> `NoctuaClientException`  [INFERRED]
  tests/test_noctua_client.py → src/services/noctua_client.py
- `test_send_motor_command_readonly_blocked()` --uses--> `NoctuaReadOnlyException`  [INFERRED]
  tests/test_noctua_client.py → src/services/noctua_client.py
- `test_update_thresholds_readonly_blocked()` --uses--> `NoctuaReadOnlyException`  [INFERRED]
  tests/test_noctua_client.py → src/services/noctua_client.py
- `test_update_timer_readonly_blocked()` --uses--> `NoctuaReadOnlyException`  [INFERRED]
  tests/test_noctua_client.py → src/services/noctua_client.py
- `client_readonly()` --uses--> `NoctuaClient`  [INFERRED]
  tests/test_noctua_client.py → src/services/noctua_client.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Web Application Frontend Templates** — src_web_templates_base, src_web_templates_dashboard, src_web_templates_login [EXTRACTED 1.00]
- **Backup and DB Persistence Layer** — knowledge_backups_guide, knowledge_estrategia_backup_manus, src_services_database [INFERRED 0.85]
- **Fluxo de Coleta e Monitoramento de Telemetria** — docs_architecture_noctua_iot_scraping, docs_architecture_monitoramento_alertas, docs_architecture_consolidacao_migracao, docs_mer_leituras [INFERRED 0.85]
- **System Monitoring and Self-Healing watchdog flow** — scripts_check_network_health, scripts_14_watchdog_resilience, src_alerts_alert_check, src_alerts_offline_check [INFERRED 0.85]
- **Monitoramento de Qualidade da Água** — docs_mer_qualidade_agua_limnologia, docs_mer_qualidade_agua_consumo, docs_tech_stack_stack_aiogram [INFERRED 0.85]

## Communities (146 total, 84 thin omitted)

### Community 0 - "get_sqlite_connection"
Cohesion: 0.07
Nodes (74): AgentExecutor, datetime, migrate_postgres(), migrate_sqlite(), check_alerts(), Verifica as últimas leituras no banco de dados e dispara alertas se necessário., run_production_logic(), ajustar_gompertz() (+66 more)

### Community 1 - "main.py"
Cohesion: 0.07
Nodes (73): asyncio, CallbackQuery, InlineKeyboardMarkup, Message, Pool, criar_lote_completo(), finalizar_lote_abate(), get_estruturas_ativas() (+65 more)

### Community 2 - "test_web_dashboard.py"
Cohesion: 0.15
Nodes (4): Testa endpoint GET /api/lotes com mock do postgres., Testa listagem do seed (Dirceu/Joceli), adição, edição, teste WhatsApp e…, test_api_get_lotes_route(), test_crud_contatos_whatsapp_dynamic()

### Community 3 - "get_weather_forecast"
Cohesion: 0.21
Nodes (10): get_weather_forecast(), log_weather_locally(), Sessão customizada para impor um timeout limite nas requisições HTTP., Salva os dados da previsão em um arquivo JSON local, sobrescrevendo o anterior…, Obtém a previsão do tempo utilizando a API Open-Meteo. Utiliza as coordenadas…, TimeoutCachedSession, patch, Verifica se o serviço utiliza as coordenadas do .env corretamente. (+2 more)

### Community 4 - "test_feed_prediction_agent.py"
Cohesion: 0.25
Nodes (6): format_data_summary_micro(), patch, Versão condensada da lógica que iremos implementar no feed_prediction.py, Valida se o resumo de dados é realmente curto (Micro-contexto)., Testa a nova função do agente (mockada)., TestFeedPredictionAgent

### Community 5 - "listar_contatos_whatsapp"
Cohesion: 0.11
Nodes (26): listar_contatos_whatsapp(), Retorna lista de contatos WhatsApp do PostgreSQL (ou SQLite em fallback)., _extract_evolution_error(), get_brazilian_phone_variants(), normalize_whatsapp_number(), Envia mensagem de texto via Evolution API v2 (WhatsApp). Se 'phone' for…, Envia uma imagem com legenda via Evolution API v2 (WhatsApp) para contatos…, Envia uma notificação push via ntfy.sh para o tópico configurado. Ultraleve,… (+18 more)

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

### Community 12 - "🛠️ Ações Executadas"
Cohesion: 0.17
Nodes (11): 1. Enxugamento Drástico do Container e Dependências (`requirements-web.txt` & `Dockerfile`), 2. Integração Evolution API (WhatsApp) e Gestão Dinâmica de Contatos (`contatos_whatsapp`), 3. Exposição Sem Porta via Caddy Reverse Proxy (`https://brunoconter.duckdns.org/psicultura`), 4. Correção de Persistência MDM (CPF/CADPRO com Migração de UID em Cascata) e Diagnóstico WhatsApp, 5. Testes Automatizados, 6. Botão "Coletar e Enviar no WhatsApp", 7. Redesign do Card "Clima Local" e Favicon Temático de Piscicultura, 8. Padronização Visual Completa do Dashboard (Hero + Metric Tiles) (+3 more)

### Community 15 - "weekly_maintenance.sh"
Cohesion: 0.40
Nodes (4): PG_HOST, PG_PORT, PYTHONPATH, weekly_maintenance.sh script

### Community 16 - "Tutorial: Backup e Restauração com Cloudflare R2"
Cohesion: 0.22
Nodes (8): 1. Premissas e Custos (Free Tier), 2. Configuração no Painel da Cloudflare, 3. Configuração do Ambiente (.env), 4. Execução do Backup, 5. Código de Contingência: Restauração em Novo Comissionamento, Agendamento (Cron), O que este script faz:, Tutorial: Backup e Restauração com Cloudflare R2

### Community 21 - "NoctuaClient"
Cohesion: 0.13
Nodes (14): Any, main(), NoctuaClient, Cliente HTTP síncrono para o AWS AppSync do Noctua IoT., Extrai dinamicamente a chave x-api-key (da2-...) dos chunks estáticos do portal…, Executa uma chamada GraphQL no AWS AppSync com tratamento de status,…, Testa se as credenciais e o endpoint GraphQL respondem com sucesso., Consulta as leituras mais recentes registradas para o gateway. (+6 more)

### Community 26 - "Stack Tecnológica - Projeto Piscicultura"
Cohesion: 0.25
Nodes (8): 1. Linguagem e Runtime, 2. Backend e Interface Web, 3. Inteligência Artificial e Automação, 4. Banco de Dados, 5. Interface de Usuário e Notificações, 6. Infraestrutura e Operação, 7. Qualidade de Código e Testes, Stack Tecnológica - Projeto Piscicultura

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
Cohesion: 0.22
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

### Community 107 - "4. Especificações dos Módulos e Componentes"
Cohesion: 0.29
Nodes (7): 4.1 Módulo Noctua IoT Client (`src/services/noctua_client.py`), 4.2 Módulo de Coleta e Ingestão (`src/scrape/monitor_data.py`), 4.3 Coletor Autônomo Daemon (`src/jobs/collector_service.py`), 4.4 Dashboard Web (`src/web/app.py` & `src/web/templates/`), 4.5 Bot Telegram Unificado (`src/bots/`), 4.6 Módulo de Predição de Arraçoamento e IA (`src/analysis/feed_prediction.py`), 4. Especificações dos Módulos e Componentes

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
Cohesion: 0.25
Nodes (8): 1.1 Objetivos Principais, 1. Visão Geral e Escopo, 2. Arquitetura de Alto Nível, 3.1 SQLite (`data/piscicultura_dados.db`) - Camada de Borda e Cache Rápido, 3.2 PostgreSQL (`piscicultura_history`) - Camada Canônica e Histórico Transacional, 3. Modelo de Persistência e Dados, 7. Critérios de Qualidade e Testabilidade, Especificações Técnicas e Arquiteturais do Sistema (System Specifications)

### Community 113 - "🛠️ Ações Executadas"
Cohesion: 0.22
Nodes (8): 1. Auditoria e Varredura da Base de Código (Graphify & Análise Estática), 2. Validação da Suíte de Testes (TDD / CI), 3. Redação e Formalização das Especificações Técnicas (`docs/specs.md`), 4. Atualização de Referências e Documentação Cruzada, 🛠️ Ações Executadas, Diário de Bordo - 28/09/2026, 🎯 Objetivo da Sessão, 📌 Próximos Passos

### Community 114 - "app.py"
Cohesion: 0.08
Nodes (45): login_required, route, api_contatos_whatsapp(), api_criar_lote(), api_endpoints_list(), api_excluir_contato_whatsapp(), api_fechar_lote(), api_get_lotes() (+37 more)

### Community 115 - "collector_service.py"
Cohesion: 0.25
Nodes (7): migrate_data(), Migra dados do SQLite para o PostgreSQL., run_collector_loop(), _background_scheduler_loop(), Executa coleta Noctua, checagem de alertas/offline, clima e sync em background., Inicia a thread daemon de coleta e alertas se ENABLE_INTERNAL_SCHEDULER=true., start_background_scheduler()

### Community 116 - "TestPostgresConcurrency"
Cohesion: 0.15
Nodes (10): pg_pool(), fixture, Valida inserções concorrentes de biometria e mortalidade para o mesmo lote sob…, Testa tentativa de fechamento concorrente garantindo atomicidade sem deadlocks., Pool de conexões thread-safe para testes de concorrência., Cria uma estrutura e um lote temporários dedicados para os testes de estresse., Suíte de Testes de Concorrência, Leitura e Escrita sob Carga no PostgreSQL., Valida que múltiplas threads simultâneas realizam leituras sem contenção ou… (+2 more)

### Community 117 - "Diário de Bordo - 29/09/2026"
Cohesion: 0.10
Nodes (19): 1. Front-End: Layout Base & Navegação, 2. Front-End: Interface de Batch Management (`lotes.html`), 3. Front-End: Interface de MDM & Settings (`settings.html`), 4. Backend Flask: Novas Rotas em `src/web/app.py`, 5. Suíte de Testes de Concorrência & Estresse, 🛡️ Auditoria de Recursos, Otimização de CPU & Ativação do Telegram Bot, 🛠️ Ações Executadas, Ações Implementadas (+11 more)

### Community 118 - "Monitoramento e Automação para Piscicultura"
Cohesion: 0.33
Nodes (6): 🧪 Ambiente de Testes (Desenvolvimento), 📂 Estrutura do Projeto, Monitoramento e Automação para Piscicultura, 🧠 Predição de Arraçoamento com IA, 🚀 Quick Start (Setup), 🛠 Tech Stack

### Community 119 - "monitor_data.py"
Cohesion: 0.16
Nodes (14): collect_via_api(), ensure_leituras_table(), Função principal de tomada de dados. Utiliza preferencialmente a API GraphQL…, Garante que a tabela de leituras exista com o schema correto., Realiza a coleta das leituras dos tanques diretamente via AWS AppSync GraphQL…, scrape_and_save(), get_default_estrutura_info(), Retorna as informações da estrutura configurada no .env. (+6 more)

### Community 120 - "5. Regras de Negócio Críticas"
Cohesion: 0.50
Nodes (4): 5.1 Regra de Isolamento de Lotes Ativos (Urgente/Crítico), 5.2 Regra de Suspensão Operacional do Monitoramento, 5.3 Regra de Timezone e Padronização Temporal, 5. Regras de Negócio Críticas

### Community 121 - "6. Infraestrutura, Containerização e Resiliência"
Cohesion: 0.50
Nodes (4): 6.1 Especificação dos Containers Docker (`docker-compose.yml`), 6.2 Resiliência de Borda e Watchdog (`scripts/14-watchdog-resilience.sh`), 6.3 Política de Backup Remoto, 6. Infraestrutura, Containerização e Resiliência

### Community 123 - "get_local_now"
Cohesion: 0.21
Nodes (12): check_last_reading(), Verifica o tempo da última leitura dos tanques. Envia alerta se o atraso for…, get_local_now(), Retorna datetime ingênuo representando o horário local de Brasília…, Garante que check_last_reading não gera alertas offline para tanques sem lote…, test_offline_check_filters_inactive_batches(), Simula o cálculo do dashboard para leituras recentes vs antigas., Valida se offline_check usa get_local_now sem gerar falsos positivos para… (+4 more)

### Community 124 - "sync_hourly_weather"
Cohesion: 0.23
Nodes (10): fetch_openmeteo_json(), Obtém o clima atual e salva na tabela clima_historico e no cache JSON., Busca previsão do tempo da Open-Meteo via HTTP JSON puro (0 MB de overhead de…, sync_hourly_weather(), Verifica se a tabela clima_historico foi criada no SQLite., Verifica se o job de sincronização salva dados no banco., Verifica se o relatório horário contém a linha de clima., test_clima_historico_table_exists() (+2 more)

### Community 125 - "agent_tools.py"
Cohesion: 0.20
Nodes (8): execute_python_report(), query_postgres(), Aciona o script de migração de dados do SQLite (onde os dados brutos chegam)…, Executa uma consulta SELECT de leitura no banco de dados PostgreSQL e retorna…, Executa um script Python da pasta src/reports/ e retorna o resultado no…, run_migration(), tool(), TestAgentFallback

### Community 126 - "manual_report.py"
Cohesion: 0.16
Nodes (18): br(), build_manual_report(), _estruturas_ativas(), fmt_taxa(), Relatório manual (disparado pelo botão do painel) com leitura atual, médias…, Formata número no padrão brasileiro (vírgula decimal)., Calcula (último - primeiro) / horas entre eles. pontos = [(datetime, valor)]., Retorna set de UIDs com lote ativo, ou None se o Postgres estiver indisponível. (+10 more)

### Community 127 - "15-auto-configure-macs.py"
Cohesion: 0.67
Nodes (3): main(), Atualiza as variáveis STRUCT_MACS, STRUCT_NAME e STRUCT_PLUSCODE no arquivo…, update_env_file()

### Community 128 - "get_hourly_report"
Cohesion: 0.50
Nodes (4): get_hourly_report(), Gera o relatório estatístico das últimas leituras para cada tanque., Garante que get_hourly_report exclui dados de tanques sem lote ativo no…, test_hourly_report_filters_inactive_batches()

### Community 129 - "get_estrutura_uid"
Cohesion: 0.50
Nodes (4): generate_sha256(), get_estrutura_uid(), Gera um hash SHA256 a partir de uma string., Gera o UID para uma estrutura baseado no nome e pluscode.

### Community 130 - "test_noctua_client.py"
Cohesion: 0.11
Nodes (15): NoctuaClientException, NoctuaReadOnlyException, Exceção base para erros de comunicação ou regra de negócio com Noctua IoT., Disparada quando uma operação de escrita é tentada sob NOCTUA_READ_ONLY=true., Envia mensagem de comando para o gateway/endpoint do tanque. Bloqueado…, api_send_motor_command(), Envia comando de motor para o endpoint respeitando travas de segurança., client_readonly() (+7 more)

### Community 131 - "web_auth.py"
Cohesion: 0.25
Nodes (8): get_user_by_id(), init_web_auth_db(), Inicializa a tabela de usuários web no SQLite., Valida as credenciais do usuário., Retorna dados do usuário pelo ID., validate_user(), Testa o serviço de autenticação web., test_web_auth_service()

### Community 132 - "User"
Cohesion: 0.40
Nodes (4): load_user(), User, user_loader, UserMixin

### Community 133 - "api_testar_contato_whatsapp"
Cohesion: 0.50
Nodes (4): obter_contato_whatsapp(), Busca um contato WhatsApp específico pelo ID., api_testar_contato_whatsapp(), Dispara mensagem de teste imediata via Evolution API para o contato informado.

### Community 134 - "auth_client"
Cohesion: 0.50
Nodes (4): auth_client(), client(), fixture, Cria um cliente logado para testar rotas protegidas.

## Knowledge Gaps
- **238 isolated node(s):** `aliases.sh script`, `11-backup-db.sh script`, `PGPASSWORD`, `02-setup-venv.sh script`, `03-install-python-deps.sh script` (+233 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 489 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **84 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `NoctuaClient` connect `NoctuaClient` to `api_get_endpoint`, `test_noctua_client.py`, `app.py`, `monitor_data.py`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Why does `get_sqlite_connection()` connect `get_sqlite_connection` to `get_hourly_report`, `web_auth.py`, `listar_contatos_whatsapp`, `app.py`, `collector_service.py`, `monitor_data.py`, `get_local_now`, `sync_hourly_weather`, `manual_report.py`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Why does `get_postgres_connection()` connect `get_sqlite_connection` to `get_hourly_report`, `listar_contatos_whatsapp`, `app.py`, `collector_service.py`, `get_local_now`, `agent_tools.py`, `manual_report.py`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **What connects `aliases.sh script`, `11-backup-db.sh script`, `PGPASSWORD` to the rest of the system?**
  _238 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `get_sqlite_connection` be split into smaller, more focused modules?**
  _Cohesion score 0.07321691563223227 - nodes in this community are weakly interconnected._
- **Should `main.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06664388243335612 - nodes in this community are weakly interconnected._
- **Should `listar_contatos_whatsapp` be split into smaller, more focused modules?**
  _Cohesion score 0.1111111111111111 - nodes in this community are weakly interconnected._