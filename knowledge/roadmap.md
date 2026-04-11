# Roadmap do Projeto

## Curto Prazo (Q2 2026)

*   [x] Estruturação inicial do repositório.
*   [x] Refatoração completa do código para usar a nova estrutura.
*   [x] Implementação de logs centralizados e limpeza programada por cron.
*   [x] Adaptação dos scripts de setup para Alpine Linux e Raspberry Pi.
*   [x] Implementação de Coleta de Dados via Selenium (Scraping).
*   [x] Sistema de Alertas Críticos via Telegram (O2 e Offline).
* [x] Restauração e integração dos fluxos Node-RED e scripts Python relacionados.
* [x] Automatização completa do Setup (01-06) e Crontab.
* [x] Portabilidade total do projeto (Caminhos relativos e detecção automática de PROJECT_ROOT).
* [x] Centralização dos volumes do PostgreSQL no repositório (`data/postgres`).
* [ ] Testes finais de resiliência e tratamento de erros no scraping.


## Médio Prazo (Q3 2026)

*   [ ] Adicionar testes unitários para as funções críticas (Scrape, Alerts, DB).
*   [ ] Melhorar o gerenciamento de estado do bot (atualmente em memória).
*   [ ] Criar um dashboard web simples (Streamlit ou similar) para visualização local.

## Longo Prazo (Q4 2026+)

*   [ ] Explorar modelos de Machine Learning para detecção de anomalias preditiva.
*   [ ] Criar um sistema de alerta mais robusto e configurável (limites via Telegram).
*   [ ] Integração com outros sensores via MQTT.
