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

## 📂 Estrutura do Projeto

- `src/`: Código-fonte (Scrape, Alertas, Bots, Análise).
- `scripts/`: Utilitários de comissionamento e manutenção.
- `docs/`: Documentação técnica e MER.
- `knowledge/`: Estado do projeto e roadmap.
- `nodered/`: Fluxos de integração Telegram.
- `data/`: Bancos de dados persistentes.

## 🛠 Tech Stack

- **Linguagem:** Python 3.11+ (Aiogram, Pandas, Scipy, Selenium).
- **Infra:** Docker Compose (PostgreSQL), Alpine Linux.
- **Integração:** Telegram Bot API, Node-RED.

---
Para detalhes arquiteturais e estado atual, consulte `docs/architecture.md` e `knowledge/project_state.md`.
