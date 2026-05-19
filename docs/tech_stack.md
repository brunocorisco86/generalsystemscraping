# Stack Tecnológica - Projeto Piscicultura

Este documento detalha as tecnologias, ferramentas e linguagens utilizadas no desenvolvimento e operação do sistema de monitoramento de piscicultura.

## 1. Linguagem e Runtime
- **Linguagem Principal:** Python 3.12+
- **Ambiente Virtual:** `venv` (isolamento de dependências)
- **Gerenciamento de Pacotes:** `pip`

## 2. Backend e Interface Web
- **Web Framework:** [Flask](https://flask.palletsprojects.com/) - Utilizado para o dashboard de controle e visualização.
- **Autenticação:** [Flask-Login](https://flask-login.readthedocs.io/) - Gerenciamento de sessões e usuários.
- **Segurança:** `werkzeug.security` para hashing de senhas.
- **Template Engine:** Jinja2 (com Bootstrap 5 no front-end).

## 3. Inteligência Artificial e Automação
- **Orquestração de IA:** [LangChain](https://www.langchain.com/) - Utilizado para gerenciar prompts e ferramentas do agente.
- **Modelo de Linguagem:** [Google Gemini API](https://ai.google.dev/) (Flash/Pro) - Cérebro do Especialista IA.
- **Scraping de Dados:** [Selenium](https://www.selenium.dev/) com ChromeDriver - Captura de dados do portal Noctua-IoT.

## 4. Banco de Dados
- **SQLite (Cache de Borda):** Armazenamento local rápido para dados em tempo real e funcionamento offline.
- **PostgreSQL (Histórico):** Banco relacional robusto para análise de longo prazo, executado em container Docker.
- **Migração:** Scripts personalizados para sincronização entre SQLite e Postgres.

## 5. Interface de Usuário e Notificações
- **Telegram Bot:** [Aiogram](https://docs.aiogram.dev/) - Framework assíncrono para interação via chat.
- **Dashboard Web:** Interface responsiva construída com Bootstrap 5 e Chart.js para visualização de séries temporais.

## 6. Infraestrutura e Operação
- **Sistema Operacional:** Alpine Linux (Hardware: Raspberry Pi 3B).
- **Gerenciamento de Processos:** Cron (Agendamentos e execução automática via `@reboot`).
- **Containerização:** [Docker Compose](https://docs.docker.com/compose/) - Para o banco de dados Postgres e PGAdmin.
- **Previsão do Tempo:** [Open-Meteo API](https://open-meteo.com/) - Integração de dados climáticos locais.

## 7. Qualidade de Código e Testes
- **Testes Unitários/Integração:** [Pytest](https://docs.pytest.org/)
- **Isolamento de Ambiente:** `python-dotenv` e `pytest-dotenv`.
- **Análise Estática:** Linter `flake8` (via `# noqa`).
