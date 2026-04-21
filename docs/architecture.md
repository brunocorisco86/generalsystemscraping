# Arquitetura do Sistema

Este documento descreve a arquitetura geral do sistema de monitoramento de piscicultura, detalhando as escolhas tecnológicas, o fluxo de dados e a infraestrutura.

## 1. Visão Geral & Infraestrutura

O sistema é projetado para operar em um ambiente de baixo custo e baixo consumo de energia, focado em alta disponibilidade para prevenção de perdas por falta de oxigenação.

- **Dispositivo:** Raspberry Pi 3B (ARM64).
- **S.O.:** Alpine Linux - Escolhido pela leveza e segurança.
- **Armazenamento:** Cartão SD Industrial.

## 2. Escolhas Tecnológicas Principais

- **Linguagem:** Python 3.11+ (Pandas, NumPy, Matplotlib, Aiogram).
- **Coleta:** Selenium + Chromium (Headless) para scraping do portal Noctua IoT.
- **Banco de Dados:**
    - **SQLite:** Cache local para garantir funcionamento offline e rapidez na borda.
    - **PostgreSQL:** Armazenamento de histórico de longo prazo (Docker).
- **Interface:** Telegram API (Bots) e Node-RED (Fluxos visuais e comandos).

## 3. Estrutura Modular (`src/`)

- `scrape/`: Automação de captura de dados.
- `alerts/`: Monitoramento constante e disparos de emergência.
- `bots/`: Interface de usuário para Biometria e Qualidade da Água.
- `jobs/`: Tarefas agendadas (Relatórios, Migração de dados).
- `services/`: Lógica compartilhada (DB, Notificações).

## 4. Fluxo de Dados

1.  **Captura:** Scraper extrai dados a cada 15 min e salva no SQLite local.
2.  **Monitoramento:** Scripts de alerta verificam o SQLite continuamente.
3.  **Interação:** Usuários registram biometrias via Bot; dados vão para o Postgres.
4.  **Consolidação:** Jobs migram dados do SQLite para o Postgres diariamente.
5.  **Comando:** Node-RED recebe comandos do Telegram e executa scripts de relatório sob demanda.

---
*Foco na resiliência e produtividade real no campo.*
