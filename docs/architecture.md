# Arquitetura do Sistema

Este documento descreve a arquitetura geral do sistema de monitoramento de piscicultura, detalhando as escolhas tecnológicas, o fluxo de dados e a interação entre os diversos componentes.

## 1. Visão Geral

O sistema é projetado para operar em um ambiente de baixo custo e baixo consumo de energia, como um Raspberry Pi 3B (ARM64) executando Alpine Linux. A modularidade é um princípio chave para garantir manutenibilidade e escalabilidade.

## 2. Escolhas Tecnológicas Principais

*   **Sistema Operacional:** Alpine Linux (ARM64)
    *   **Motivação:** Leveza, segurança e eficiência de recursos, ideal para hardware embarcado como o Raspberry Pi. A compatibilidade com `apk` simplifica a gestão de pacotes de sistema.
*   **Linguagem de Programação:** Python 3
    *   **Motivação:** Vasta gama de bibliotecas para processamento de dados (Pandas, NumPy, Matplotlib), automação e desenvolvimento de bots (Aiogram, python-dotenv).
*   **Automação e Coleta de Dados:** Selenium + Chromium (Headless)
    *   **Motivação:** Permite a captura de dados em tempo real de plataformas externas (Noctua IoT) através de scraping automatizado, superando a falta de APIs diretas.
*   **Banco de Dados:**
    *   **SQLite:** Para dados em tempo real ou coletados localmente. Simples, serverless e eficiente para o uso local no Raspberry Pi.
    *   **PostgreSQL:** Utilizado em um container Docker para armazenamento de histórico de longo prazo e dados transacionais (biometria, qualidade da água). Oferece robustez, integridade de dados e recursos avançados para consultas.
*   **Containerização:** Docker e Docker Compose
    *   **Motivação:** Facilita a implantação, isolamento de serviços (PostgreSQL, Bots) e portabilidade entre diferentes ambientes. Simplifica a gestão de dependências e garante um ambiente de execução consistente.
*   **Interface de Automação:** Node-RED
    *   **Motivação:** Plataforma visual para programação de fluxos, ideal para integrar eventos do Telegram (comandos) com a execução de scripts Python para relatórios e ações específicas.
*   **Comunicação:** Telegram API
    *   **Motivação:** Plataforma de mensagens segura e amplamente utilizada para notificações, relatórios e interação com os bots.

## 3. Estrutura Modular do Código (`src/`)

O código-fonte Python é organizado em módulos lógicos dentro do diretório `src/`:

*   **`src/scrape/`**: Scripts de automação via Selenium para extração de dados brutos da plataforma Noctua IoT e persistência inicial no SQLite local.
*   **`src/alerts/`**: Verificadores constantes que monitoram o banco de dados em busca de anomalias (O2 crítico, sistema offline) e disparam notificações via Telegram.
*   **`src/bots/`**: Contém os bots de Telegram independentes (Biometria e Qualidade da Água). Cada bot gerencia sua própria lógica de interação e persistência de dados específicos.
*   **`src/jobs/`**: Scripts Python projetados para execução agendada via cron (ex: geração de relatórios diários, migração de dados).
*   **`src/analysis/`**: Scripts focados em processamento de dados, modelos de previsão e geração de gráficos mais complexos (ex: curva de crescimento).
*   **`src/reports/`**: Scripts Python que geram relatórios específicos, muitas vezes acionados por comandos do Telegram via Node-RED.
*   **`src/services/`**: Módulos que encapsulam lógica compartilhada, como conexão com bancos de dados (`database.py`) e envio de notificações (`notification.py`), promovendo a reutilização de código e a separação de preocupações.

## 4. Fluxo de Dados e Interação entre Componentes

1.  **Coleta de Dados (Scraping):** O script `src/scrape/monitor_data.py` executa a cada 15 minutos via cron, acessando a plataforma Noctua via Selenium Headless e salvando leituras de O2, Temp e Aeradores em `data/piscicultura_dados.db`.
2.  **Monitoramento de Alertas:** Scripts em `src/alerts/` consultam o SQLite local em busca de valores críticos ou falta de novos dados, disparando alertas imediatos para o Telegram via `src/services/notification.py`.
3.  **Bots Telegram (`src/bots/`):**
    *   Interagem diretamente com os usuários para registrar novas biometrias ou dados de qualidade da água.
    *   Utilizam `src/services/database.py` para persistir dados no PostgreSQL (via Docker).
4.  **Cron Jobs (`src/jobs/`):**
    *   Executam scripts em horários pré-definidos para:
        *   Gerar relatórios periódicos (ex: `evening_report.py`).
        *   Migrar dados do SQLite local para o PostgreSQL de histórico (`migrate_data.py`).
        *   A saída de logs é centralizada em `logs/` e gerenciada por `scripts/cleanup_logs.sh`.
5.  **Node-RED (`nodered/`):**
    *   Recebe comandos específicos do Telegram.
    *   Aciona scripts Python em `src/reports/` para gerar relatórios visuais sob demanda.

## 5. Portabilidade e Implantação

A utilização de Docker Compose para serviços de banco de dados e bots, juntamente com o script `setup.sh` adaptado para Alpine Linux e a configuração centralizada via `.env`, garante que o sistema possa ser facilmente replicado e implantado em diferentes instâncias do Raspberry Pi com Alpine, minimizando o esforço de configuração manual.
