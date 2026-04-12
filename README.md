# Projeto de Monitoramento e Automação para Piscicultura

Este repositório contém o código para um sistema completo de monitoramento e automação para tanques de piscicultura. Desenvolvido com foco em portabilidade e eficiência, ideal para implantação em ambientes como Raspberry Pi com Alpine Linux.

## Funcionalidades

*   **Coleta de Dados Automatizada (Scraping):** Integração via Selenium para extrair dados em tempo real de plataformas externas (Noctua IoT), automatizando a captura de Oxigênio, Temperatura e estado dos Aeradores.
*   **Sistema de Alertas Inteligente:** Monitoramento constante que dispara notificações imediatas via Telegram para níveis críticos de Oxigênio ou detecção de sistema offline.
*   **Relatórios Automáticos:** Geração de relatórios periódicos (diários, horários) com gráficos de tendência e resumos enviados via Telegram.
*   **Bots Telegram Dedicados:** Bots para `Biometria` e `Qualidade da Água` que permitem registro de dados e consultas rápidas diretamente pelo chat.
*   **Integração Node-RED:** Comandos via Telegram para disparar relatórios sob demanda e ações de manutenção (ex: backup de dados).
*   **Armazenamento Híbrido:** SQLite para cache local e dados em tempo real; PostgreSQL para histórico de longo prazo e análises complexas.
*   **Análise Preditiva:** Scripts para projeção de curvas de crescimento e previsão de padrões ambientais.

## Estrutura do Projeto

```
/
├── .env.example             # Template de configuração (Copiar para .env)
├── docker-compose.yml       # Orquestrador de serviços (Postgres, Bots)
├── requirements.txt         # Dependências Python
│
├── data/                    # Banco de dados SQLite local
├── docs/                    # Documentação técnica e guias
├── knowledge/               # Visão estratégica e roadmap
├── logs/                    # Logs de execução e erros
├── nodered/                 # Fluxos de integração Telegram/Scripts
├── reports/                 # Imagens e PDFs de relatórios gerados
│
├── scripts/                 # Utilitários de sistema (Sequência de Comissionamento)
│   ├── setup.sh             # [Master] Executa etapas 01 a 06
│   ├── 01-system-deps.sh    # Dependências do SO (Alpine/Debian)
│   ├── 02-setup-venv.sh     # Criação do ambiente virtual Python
│   ├── 03-install-python-deps.sh # Instalação de libs Python
│   ├── 04-setup-env-file.sh # Configuração inicial do .env
│   ├── 05-init-sqlite-db.py # Inicialização do banco SQLite local
│   ├── 06-install-cron.sh   # Agendamento de tarefas automáticas
│   ├── 07-start-containers.sh # Inicialização do Docker (Postgres/Bots)
│   ├── 08-fix-permissions.sh # Ajuste de permissões e criação de logs
│   ├── 09-cleanup-logs.sh   # Limpeza automática de logs antigos
│   └── 10-maintenance-docker.sh # Ferramenta de manutenção Docker
│
└── src/                     # Código-fonte principal
    ├── alerts/              # Verificadores de limites e status (Telegram)
    ├── analysis/            # Modelos matemáticos e gráficos preditivos
    ├── bots/                # Código dos bots Biometria/Água
    ├── jobs/                # Tarefas agendadas (Relatórios, Migração)
    ├── reports/             # Geradores de relatórios sob demanda
    ├── scrape/              # Captura de dados via Selenium (Chrome Headless)
    └── services/            # Serviços compartilhados (DB, Notificação)
```

## Sequência de Comissionamento

Para colocar o sistema em operação, siga estas etapas na ordem:

1.  **Instalação Base (Etapas 01 a 06):**
    Execute o script mestre para preparar o ambiente, dependências e agendamentos:
    ```bash
    bash scripts/setup.sh
    ```
    *Este script detecta o sistema operacional, cria o ambiente virtual, instala dependências e configura o crontab.*

2.  **Configuração de Credenciais:**
    *   Edite o arquivo `.env` gerado na raiz do projeto.
    *   Preencha os tokens do Telegram, credenciais do banco e acessos ao portal Noctua IoT.

3.  **Inicialização de Serviços Docker (Etapa 07):**
    Inicie o PostgreSQL e os bots de suporte:
    ```bash
    bash scripts/07-start-containers.sh
    ```
    *Este comando também inicializa o schema do banco de dados PostgreSQL automaticamente.*

4.  **Ajuste Final de Permissões (Etapa 08):**
    Garanta que todos os diretórios e arquivos de log tenham permissões corretas:
    ```bash
    bash scripts/08-fix-permissions.sh
    ```

## Verificação e Saúde do Sistema

Após o comissionamento, valide a operação com os seguintes comandos:

*   **Status dos Containers:** `docker compose ps`
*   **Logs do Monitoramento:** `tail -f logs/scrape.log`
*   **Logs de Alertas:** `tail -f logs/alerts.log`
*   **Agendamentos Ativos:** `crontab -l`

## Manutenção

*   **Limpeza de Logs:** O sistema limpa logs automaticamente via cron (`09-cleanup-logs.sh`), mas você pode executar manualmente se necessário.
*   **Reinicialização/Limpeza Docker:** Utilize `bash scripts/10-maintenance-docker.sh` para gerenciar a limpeza de imagens e containers órfãos de forma segura.
*   **Atualização de Permissões:** O script `08-fix-permissions.sh` é executado automaticamente em cada boot do sistema via `@reboot` no cron.

## Estrutura de Dados e Portabilidade

*   **PostgreSQL Local:** Os dados do banco de histórico são persistidos em `data/postgres/` dentro do repositório, facilitando backups e migrações.
*   **Caminhos Dinâmicos:** Todos os scripts Python e automações do Node-RED utilizam caminhos relativos ou variáveis de ambiente, permitindo que o projeto funcione em qualquer diretório sem alterações manuais.

## Manutenção

*   **Logs:** Verifique `logs/scrape.log` e `logs/alerts.log` para monitorar a saúde do sistema.
*   **Banco de Dados:** O sistema migra automaticamente dados do SQLite para o Postgres diariamente para evitar crescimento excessivo do arquivo local.

---
*Desenvolvido para máxima resiliência em hardware limitado.*
