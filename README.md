# Monitoramento e Automação para Piscicultura

Sistema completo de monitoramento para tanques de piscicultura, otimizado para Raspberry Pi com Alpine Linux.

## 🚀 Quick Start (Setup)

1.  **Instalação Base:**
    ```bash
    bash scripts/setup.sh
    ```
2.  **Configuração:** Edite o arquivo `.env` com as credenciais necessárias.
3.  **Containers:** Inicie o banco de dados e bots:
    ```bash
    bash scripts/07-start-containers.sh
    ```
4.  **Verificação:**
    - `docker compose ps`
    - `tail -f logs/scrape.log`
    - `crontab -l`

## 🧪 Ambiente de Testes (Desenvolvimento)

Para garantir a estabilidade do código antes de ir para produção, possuímos um ambiente de testes isolado que utiliza variáveis e bancos *dummy* (via arquivo `.env.test`), protegendo seus dados reais.

1.  **Ative o ambiente virtual (se necessário):**
    ```bash
    source .venv/bin/activate
    ```
2.  **Instale as dependências de desenvolvimento:**
    ```bash
    pip install -r requirements-dev.txt
    ```
3.  **Execute a suíte de testes:**
    Este script garantirá que tudo seja testado de forma segura sem vazar para a produção.
    ```bash
    bash scripts/run_tests.sh
    ```

## 📂 Estrutura do Projeto

- `src/`: Código-fonte (Scrape, Alertas, Bots, Análise).
- `scripts/`: Utilitários de comissionamento e manutenção.
- `docs/`: Documentação técnica e MER.
- `knowledge/`: Estado do projeto e roadmap.
- `data/`: Bancos de dados persistentes.

## 🛠 Tech Stack

- **Linguagem:** Python 3.11+ (Aiogram, Pandas, Scipy, Selenium).
- **Infra:** Docker Compose (PostgreSQL), Alpine Linux.
- **Integração:** Telegram Bot API.

---
Para detalhes arquiteturais e estado atual, consulte `docs/architecture.md` e `knowledge/project_state.md`.
