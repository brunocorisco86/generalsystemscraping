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
├── scripts/                 # Utilitários de sistema
│   ├── setup.sh             # Instalação completa (Alpine/Python)
│   ├── setup_cron.sh        # Configurador de agendamentos (Crontab)
│   └── cleanup_logs.sh      # Manutenção de armazenamento
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

## Como Começar

1.  **Instalação Inicial:**
    ```bash
    bash scripts/setup.sh
    ```
    *Este script configura dependências do Alpine Linux (Chromium, Docker, etc) e o ambiente Python.*

2.  **Configuração de Credenciais:**
    *   Copie `.env.example` para `.env`.
    *   Preencha os tokens do Telegram e as credenciais de acesso ao sistema de monitoramento externo (Noctua).

3.  **Inicie os Serviços:**
    ```bash
    docker-compose up --build -d
    ```

4.  **Agende as Tarefas (CRITICAL):**
    ```bash
    bash scripts/setup_cron.sh
    ```
    *Siga as instruções para adicionar as linhas ao seu `crontab -e`. Isso ativa o scraping a cada 15min e os alertas automáticos.*

## Manutenção

*   **Logs:** Verifique `logs/scrape.log` e `logs/alerts.log` para monitorar a saúde do sistema.
*   **Banco de Dados:** O sistema migra automaticamente dados do SQLite para o Postgres diariamente para evitar crescimento excessivo do arquivo local.

---
*Desenvolvido para máxima resiliência em hardware limitado.*
