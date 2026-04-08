# Projeto de Monitoramento e Automação para Piscicultura

Este repositório contém o código para um sistema completo de monitoramento e automação para tanques de piscicultura. Desenvolvido com foco em portabilidade e eficiência, ideal para implantação em ambientes como Raspberry Pi com Alpine Linux.

## Funcionalidades

*   **Monitoramento Contínuo:** Scripts que coletam dados de sensores (Oxigênio, Temperatura) de dispositivos externos.
*   **Relatórios Automáticos:** Geração de relatórios diários (final de tarde, noturno, horário) com gráficos de tendência e resumos, enviados via Telegram.
*   **Bots Telegram Dedicados:** Dois bots (`Biometria` e `Qualidade da Água`) para interação direta, permitindo o registro de dados e consultas.
*   **Comandos Telegram via Node-RED:** Integração com Node-RED para disparar relatórios específicos (ex: histórico de Oxigênio/Temperatura) e ações (ex: backup de dados) através de comandos simples no Telegram.
*   **Armazenamento de Dados Híbrido:** Utiliza SQLite para dados em tempo real (no dispositivo local) e PostgreSQL (via Docker) para histórico de longo prazo e análises.
*   **Previsão e Análise:** Scripts para projetar curvas de crescimento de peixes e prever padrões, auxiliando na tomada de decisão.

## Estrutura do Projeto

A organização do projeto segue a seguinte estrutura para melhor modularidade e manutenção:

```
/
├── .env.example             # Exemplo de variáveis de ambiente para configuração
├── .gitignore               # Ignorar arquivos de segredo, logs e de ambiente local
├── README.md                # Visão geral do projeto e instruções de configuração
├── docker-compose.yml       # Orquestrador principal dos serviços Docker (Postgres, Bots)
├── requirements.txt         # Dependências Python consolidadas
│
├── data/                    # (Ignorado pelo Git) Para bancos de dados SQLite e outros dados voláteis
│   └── piscicultura_dados.db
│
├── docs/                    # Documentação geral sobre a arquitetura, comandos Telegram
│   ├── architecture.md
│   └── telegram_commands.md
│
├── knowledge/               # Documentos de alto nível, como o roadmap do projeto
│   └── roadmap.md
│
├── logs/                    # (Ignorado pelo Git) Para todos os arquivos de log gerados pelos scripts
│   ├── cron.log
│   └── ...
│
├── nodered/                 # Fluxos do Node-RED para a integração com Telegram
│   └── flows.json
│
├── reports/                 # (Ignorado pelo Git) Onde os relatórios gerados (imagens) são salvos
│   ├── evening_plot.png
│   └── ...
│
├── scripts/                 # Scripts de automação e utilitários
│   ├── setup.sh             # Script principal de instalação
│   ├── setup_cron.sh        # Script para auxiliar na configuração dos cron jobs
│   ├── cleanup_logs.sh      # Script para limpeza de logs antigos
│   └── fix_permissions.sh   # Script de permissões (original do projeto)
│
└── src/                     # Todo o código-fonte Python
    ├── __init__.py
    │
    ├── analysis/            # Scripts de análise e previsão (ex: plot_curva.py)
    │   ├── __init__.py
    │   ├── feed_prediction.py
    │   ├── plot_curva.py
    │   └── predict_oxygen.py
    │
    ├── bots/                # Aplicações dos bots Telegram (Biometria, Qualidade da Água)
    │   ├── biometria/
    │   │   ├── main.py
    │   │   └── db.py
    │   │
    │   └── qualidade_agua/
    │       ├── main.py
    │       ├── db.py
    │       └── Dockerfile
    │
    ├── jobs/                # Scripts destinados a serem executados por Cron (ex: relatórios, migração)
    │   ├── evening_report.py
    │   ├── hourly_report.py
    │   ├── migrate_data.py
    │   └── nightly_report.py
    │
    ├── reports/             # Scripts Python que geram relatórios acionados pelo Node-RED/Telegram
    │   ├── bot_query_ox_15d.py
    │   ├── bot_query_ox_7d.py
    │   ├── bot_query_oxygen.py
    │   └── bot_query_temp_7d.py
    │
    └── services/            # Lógica compartilhada entre diferentes partes do sistema (BD, notificações)
        ├── database.py
        └── notification.py
```

## Requisitos do Sistema

Este projeto foi otimizado para **Alpine Linux em Raspberry Pi (ARM64)**. Certifique-se de ter um sistema operacional Alpine Linux instalado em seu Raspberry Pi.

## Como Começar

Siga os passos abaixo para configurar e iniciar o sistema:

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/seu_usuario/seu_repositorio.git # Substitua pela URL real
    cd seu_repositorio
    ```

2.  **Configure o ambiente (Sistema e Python):**
    *   Execute o script de instalação. Ele detectará se você está no Alpine Linux e instalará as dependências de sistema necessárias (git, docker, python3, build-base, chromium, etc.) via `apk add`. Em seguida, configurará o ambiente virtual Python e instalará as bibliotecas.
    ```bash
    bash scripts/setup.sh
    ```

3.  **Configure suas credenciais:**
    *   Renomeie o arquivo `.env.example` para `.env`.
    *   Edite o arquivo `.env` e preencha todas as variáveis de ambiente com seus tokens do Telegram, credenciais de banco de dados PostgreSQL, caminhos de diretório, etc. **Não comite o arquivo `.env` para o Git!**

4.  **Inicie os serviços Docker (PostgreSQL e Bots):**
    *   O `docker-compose.yml` na raiz do projeto irá orquestrar o banco de dados PostgreSQL e os dois bots do Telegram.
    *   Certifique-se de que o serviço Docker está rodando em seu sistema.
    ```bash
    docker-compose up --build -d
    ```
    *   `--build` garantirá que as imagens dos bots sejam construídas com as últimas dependências. `-d` para rodar em segundo plano.

5.  **Configure os Cron Jobs:**
    *   Os relatórios automáticos e a migração de dados são executados via `cron`. Use o script auxiliar para obter as entradas de cron a serem adicionadas.
    ```bash
    bash scripts/setup_cron.sh
    ```
    *   Copie as linhas de saída e adicione-as ao seu `crontab` digitando `crontab -e`.

6.  **Configure o Node-RED:**
    *   Se você estiver usando Node-RED, importe o arquivo `nodered/flows.json` em sua instância.
    *   Configure o nó "telegram bot" dentro do Node-RED com seu `BOT_TOKEN` e `CHAT_ID` (se diferente do `.env` ou se você usa um bot dedicado para o Node-RED).
    *   Certifique-se de que o Node-RED tem acesso ao `PROJECT_ROOT` e pode executar os scripts Python.

## Scripts de Automação

*   `scripts/setup.sh`: Automatiza a configuração inicial do ambiente (dependências do sistema, ambiente Python).
*   `scripts/setup_cron.sh`: Gera entradas de crontab para automação de tarefas.
*   `scripts/cleanup_logs.sh`: Mantém a pasta `logs/` limpa, removendo arquivos antigos.
*   `scripts/fix_permissions.sh`: Script original do projeto para correção de permissões.

## Gerenciamento de Logs

Todos os scripts Python agora utilizam um sistema de logging centralizado, gravando em arquivos `.log` dentro da pasta `logs/` na raiz do projeto. Um cron job diário (configurado via `setup_cron.sh`) é responsável por limpar logs com mais de 7 dias, garantindo que o armazenamento não seja exaurido.

## Próximos Passos (Desenvolvimento)

Consulte `knowledge/roadmap.md` para o roadmap do projeto e `docs/architecture.md` para detalhes sobre a arquitetura.

