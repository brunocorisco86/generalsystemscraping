# ROADMAP DO PROJETO: TRANSIÇÃO NOCTUA IOT & CONTAINERIZAÇÃO

Este documento estabelece o roteiro de desenvolvimento iterativo para modernizar a coleta de dados da Piscicultura, migrando do scraping (Selenium/Chromium) para chamadas diretas à API GraphQL (AWS AppSync), implementando controles no frontend e preparando a infraestrutura para conteinerização leve na VPS.

---

## 📌 Visão Geral dos Marcos (Milestones)

```mermaid
flowchart LR
    M0["Milestone 0<br/>Ambiente & .env"] --> M1["Milestone 1<br/>API Noctua (Leitura)<br/>& Fim do Selenium"]
    M1 --> M2["Milestone 2<br/>Thresholds & Timers<br/>no Dashboard"]
    M2 --> M3["Milestone 3<br/>Controle de Motores<br/>(Protocolo Seguro)"]
    M3 --> M4["Milestone 4<br/>Auditoria &<br/>Conteinerização"]
    M4 --> M5["Milestone 5<br/>Deploy VPS, WhatsApp<br/>& UI Hero+Tiles"]
    M5 --> M6["Milestone 6<br/>Usuários da Família<br/>(Auth no PostgreSQL)"]
```

---

## Milestone 0: Preparação de Ambiente & Runbook do `.env`
> **Foco**: Configuração das variáveis de ambiente necessárias, obtenção de credenciais da API e validação dos drivers locais.

- [x] Criar `.env` a partir do modelo atualizado (`.env.example`).
- [x] Documentar obtenção da chave `x-api-key` da AWS AppSync no painel web Noctua e configurar em `NOCTUA_API_KEY`.
- [x] Definir `NOCTUA_READ_ONLY=true` como trava de segurança padrão.
- [x] Configurar credenciais do banco local (SQLite e PostgreSQL de desenvolvimento).
- [x] Validar conectividade inicial de rede com o endpoint AppSync via script de diagnóstico simples.

**Critério de Aceite / Teste**:
- Script de diagnóstico (`python -m src.services.noctua_client --test`) conecta ao endpoint AppSync da AWS sa-east-1 com sucesso (HTTP 401 para chave de placeholder e 200 para chave real).

---

## Milestone 1: Cliente GraphQL & Saneamento da Tomada de Dados
> **Foco**: Substituição completa do Selenium por chamadas HTTP puras para tomada de telemetria dos tanques.

- [x] **Novo Módulo**: Criar `src/services/noctua_client.py` encapsulando as queries GraphQL:
  - `listSensorDataByGatewayIdAndUpdatedAt` (dados atuais: O2, temperatura, saturação, motores, sinal).
  - `listHourlyDataByEndpointIdAndTimestamp` (histórico agregado por hora).
- [x] **Refatoração**: Adaptar `src/scrape/monitor_data.py`:
  - Remover inicialização do ChromeDriver, Selenium e BeautifulSoup.
  - Chamar `NoctuaClient` diretamente, mapeando os MACs dos tanques para as estruturas do banco.
  - Persistir as leituras nas tabelas existentes (`leituras` no SQLite e Postgres).
- [x] **Testes Automatizados**:
  - Criar `tests/test_noctua_client.py` com mocks de resposta GraphQL e testes de parsing de payloads.
  - Testar tratamento de erros (timeout, credencial expirada, retorno nulo).
- [x] **Validação de Regras de Negócio**:
  - Validar se a regra de filtragem de lotes ativos (`data_abate IS NULL`) continua respeitada nos alertas.

**Critério de Aceite / Teste**:
- Executar `pytest tests/test_noctua_client.py` com 100% de aprovação.
- Executar `pytest tests/test_monitor_data.py` garantindo persistência no SQLite e regras de negócio.

---

## Milestone 2: Gestão de Thresholds e Timers no Dashboard Web
> **Foco**: Leitura e edição segura de limiares operacionais e janelas de liga/desliga de aeradores via frontend.

- [x] **Backend (API GraphQL & Flask)**:
  - Adicionar no `NoctuaClient` a operação `get_endpoint_config(id)` para consultar `criticalO2`, `criticalO2Max`, `autoOn` e o JSON de `timer`.
  - Criar rota `GET /api/endpoints` e `GET /api/endpoint/<mac>` no Flask para expor os parâmetros atuais do tanque.
  - Criar rota `POST /api/endpoint/<mac>/thresholds` para atualizar limiares via mutation `updateEndpoint`.
  - Criar rota `POST /api/endpoint/<mac>/timers` para atualizar janelas de funcionamento via mutation `updateEndpoint`.
  - Implementar validação estrita de inputs (ex: limites físicos de O2 permitidos entre 1.0 e 8.0 mg/L).
- [x] **Frontend (`dashboard.html`)**:
  - Adicionar aba/painel "Automação, Thresholds & Acionamento de Motores".
  - Formulário para alteração de threshold mínimo e máximo com confirmação visual.
  - Visualizador/editor de janelas de timers para motores.
- [x] **Testes**:
  - Atualizar `tests/test_web_dashboard.py` testando novas rotas autenticadas de endpoints, thresholds e timers.

**Critério de Aceite / Teste**:
- Dashboard exibe os campos e executa integração com API GraphQL.
- Todos os testes de rotas web aprovados (`pytest tests/test_web_dashboard.py`).

---

## Milestone 3: Acionamento Controlado de Motores (Safe Protocol)
> **Foco**: Envio de comandos manuais para motores/aeradores com travas de segurança e confirmação de entrega.

- [x] **Mapeamento de Protocolo**:
  - Mutation `createCommandMessages` com formato estrito e allowlist de tanques.
- [x] **Backend de Comandos**:
  - Implementar envio via mutation `createCommandMessages` com geração de UUID `messageId`.
  - Criar consulta de status `get_command_status` para acompanhar ciclo de vida (`SENT` -> `DELIVERED`).
  - Bloquear envio se `NOCTUA_READ_ONLY=true` (lançando `NoctuaReadOnlyException`).
- [x] **Frontend**:
  - Adicionar botões de acionamento manual por motor com confirmação explícita de segurança.
  - Feedback visual e mensagens informativas no dashboard.
- [x] **Testes**:
  - Testar bloqueio por `NOCTUA_READ_ONLY` e envio seguro em `tests/test_noctua_client.py` e `tests/test_web_dashboard.py`.

**Critério de Aceite / Teste**:
- Comandos nunca são disparados sem confirmação prévia e respeitam as travas de offline e read-only.

---

## Milestone 4: Auditoria de Dependências & Conteinerização Completa
> **Foco**: Reduzir a pegada computacional para o mínimo absoluto e empacotar a aplicação em containers leves.

- [x] **Auditoria de Recursos**:
  - Remover `selenium`, drivers do Chromium e pacotes órfãos do `requirements.txt`.
  - Adicionar `requests` e `gunicorn` para produção eficiente.
- [x] **Dockerização Multi-Serviço**:
  - Criar `Dockerfile` unificado leve (Python 3.11 Slim com Gunicorn).
  - Criar serviço autônomo `src/jobs/collector_service.py` eliminando cron bare-metal.
  - Atualizar `docker-compose.yml` com suporte a variáveis de portas (`WEB_PORT`) e reutilização de PostgreSQL externo.
- [x] **Validação Local em Containers (Opção 1)**:
  - Stack validada e executada com sucesso via Docker Compose local (`piscicultura_web`, `piscicultura_collector`, `piscicultura_postgres`).
  - Consumo global de memória reduzido para menos de 400 MB RAM total.
  - Ajuste na inicialização do `init_web_auth_db()` para suporte a múltiplos workers no Gunicorn.
- [x] **Robustez & Hardening da Coleta**:
  - Deduplicação de telemetria no coletor (`src/scrape/monitor_data.py`), evitando duplicação ao forçar coleta.
  - Consulta segura com `MAX(id)` no dashboard (`src/web/app.py`), garantindo rigorosamente 1 card por tanque.
  - Badge visual de conectividade em tempo real no frontend (`🟢 ONLINE` / `⚠️ OFFLINE há Xh`).
- [x] **Testes de Regressão**:
  - Executar suíte completa (`bash scripts/run_tests.sh`) com 100% de aprovação (44 testes aprovados).


---

## Milestone 5: Deploy na VPS Hostinger, Integração WhatsApp (Evolution API) & Redesign UI
> **Foco**: Consolidação em container único ultraleve na VPS Hostinger (`179.197.73.80`), exposição HTTPS sem porta (`/psicultura`), substituição do Telegram pelo WhatsApp e modernização visual completa do Dashboard.

- [x] **Auditoria e Consolidação de Recursos na VPS**:
  - Container único `piscicultura_web` operando com `~46 MiB` de RAM (limite rígido de `96m`) e `requirements-web.txt` enxuto (sem Pandas/Matplotlib/LangChain/Aiogram).
  - Reuso do container PostgreSQL existente `hermes-db` (database `piscicultura_history`) na rede `hermes_mesh_network`.
- [x] **Exposição HTTPS Sem Porta via Caddy (`https://brunoconter.duckdns.org/psicultura`)**:
  - Configuração de `handle_path /psicultura/*` no `hermes-caddy` com `X-Forwarded-Prefix: /psicultura` e `ProxyFix` no Flask.
- [x] **Mensageria via Evolution API (WhatsApp) e Gestão Dinâmica de Contatos**:
  - Tabela `contatos_whatsapp` no PostgreSQL com seed inicial (**Dirceu Patel** e **Joceli Patel**) e CRUD administrativo em `/settings`.
  - Botão **"Coletar e Enviar no WhatsApp"** (`POST /api/report/whatsapp`) com cálculo sob demanda de médias (1h/6h) e taxa de variação por hora (`src/jobs/manual_report.py`).
- [x] **Padronização Visual Completa (Conceito `Hero + Metric Tiles`) e Favicon**:
  - Novo favicon SVG temático (`src/web/static/favicon.svg`) e redesign completo de todas as seções do `dashboard.html`.
- [x] **Validação Final**:
  - Suíte de testes com **64 testes aprovados** (`bash scripts/run_tests.sh`) e diário de bordo registrado em `knowledge/diario/diary_2026_10_28.md`.

**Critério de Aceite / Teste**:
- Sistema operando 24/7 na VPS em `https://brunoconter.duckdns.org/psicultura` com coleta automática Noctua IoT, envio WhatsApp e consumo mínimo de RAM.

---

## Milestone 6: Gestão de Usuários da Família & Credenciais Seguras no PostgreSQL (`hermes-db`)
> **Foco**: Permitir que cada membro da família possua seu próprio usuário e senha para acessar o painel web, armazenando as credenciais de forma segura e centralizada no PostgreSQL já existente (`piscicultura_history` em `hermes-db`).

- [ ] **Modelagem e Tabela `usuarios_web` no PostgreSQL**:
  - Criar tabela `usuarios_web` no database `piscicultura_history` (`hermes-db`) com campos: `id`, `username` (`UNIQUE`), `nome_exibicao`, `password_hash`, `papel` (`admin`, `familiar`, `visualizador`), `ativo` (`BOOLEAN`), `created_at` e `last_login`.
  - Garantir seed inicial automático a partir de `WEB_ADMIN_USER` / `WEB_ADMIN_PASS` caso a tabela esteja vazia.
- [ ] **Segurança Criptográfica de Senhas**:
  - Armazenar exclusivamente hashes seguros utilizando `werkzeug.security.generate_password_hash` (`scrypt` / `pbkdf2:sha256` com salt aleatório por usuário) e validação via `check_password_hash`.
- [ ] **Refatoração do Serviço de Autenticação (`src/services/web_auth.py`)**:
  - Migrar a leitura/validação de usuários do SQLite local para o PostgreSQL (`get_postgres_connection()`), mantendo fallback resiliente.
  - Exibir o nome do familiar logado na barra de navegação superior (`base.html`).
- [ ] **Painel Administrativo de Usuários da Família (`/settings`)**:
  - Adicionar aba/seção **"Usuários & Acesso da Família"** em `/settings` (e rotas REST `GET/POST /api/usuarios`, `PUT /api/usuarios/<id>/senha`, `DELETE /api/usuarios/<id>`).
  - Permitir criar contas individuais para os familiares (ex: Dirceu, Joceli, Bruno, etc.), alterar senhas e ativar/desativar acessos em tempo real pela interface web.
- [ ] **Testes Automatizados**:
  - Adicionar testes unitários validando criação de usuários familiares, hash de senha (garantindo que a senha em texto puro nunca seja salva), login com credenciais do Postgres e bloqueio de usuários inativos.

**Critério de Aceite / Teste**:
- Familiares conseguem logar com usuário e senha próprios em `https://brunoconter.duckdns.org/psicultura`, com credenciais persistidas com hash criptográfico no PostgreSQL (`hermes-db`) e gerenciamento completo via `/settings`.
