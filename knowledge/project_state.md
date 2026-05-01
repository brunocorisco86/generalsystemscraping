# Project State (AI Context Compression)

## Tech Stack & Runtime

- **OS**: Alpine Linux (ARM64) / Raspberry Pi 3B.
- **Python**: 3.11+ (venv managed by `scripts/setup.sh`).
- **Containers**: Docker Compose (PostgreSQL, Unified Telegram Bot).
- **Automation**: Telegram Command Interface -> Python Scripts.
- **Database**: Hybrid SQLite (Local/Edge cache) + PostgreSQL (Long-term history).
- **UI/UX**: Telegram Bots (Biometria, Qualidade da Água).
- **AI Agent**: Google Gemini (via LangChain Tools) para chat livre e filtragem inteligente de alertas (evitar falsos positivos).

## Core Data Flow

1. **Scrape**: `src/scrape/monitor_data.py` (via Selenium/Headless Chromium) runs every 15 min via Cron. Persists to `data/piscicultura_dados.db` (SQLite).
2. **Alerts**: `src/alerts/alert_check.py` and `offline_check.py` run via Cron. 
   - **AI Validation**: Alertas críticos são analisados pela IA (Gemini) contra os dados recentes (intervalos de confiança e aeradores_ativos) via ferramentas LangChain. Se for um falso positivo, o alerta é suprimido; caso contrário, é enviado via `src/services/notification.py`.
- **Jobs**: `src/jobs/` handles periodic reporting and data migration (SQLite -> Postgres).
- **Analysis/Reports**: `src/reports/` and `src/analysis/` generate visual trends. Recent addition: `/curvapeso` (Projeção Linear de Crescimento).
- **Bots**: `src/bots/main.py` (Unified Bot) handles Biometry/Water Quality input, persisting to Postgres via `src/services/database.py`.


## Critical Knowledge & Recent Fixes

- **Dependency Fix**: Added `scipy` to `requirements.txt` and `src/bots/requirements.txt` to fix `ModuleNotFoundError` in `src/analysis/plot_curva.py` when called by the Biometry bot.
- **Database Architecture**: PostgreSQL schema includes `PROPRIETARIO`, `PROPRIEDADE`, `ESTRUTURA`, `LOTES`, and operational tables (`LEITURAS`, `BIOMETRIA`, etc.).
- **Environment**: All configuration resides in `.env`. Root path is dynamically detected.

## Domain Concepts

- **Ficha Verde (Green Sheet)**: Standardized data model for fish growth tracking.
- **Biometria**: Weight and health checks logged by users via bot.
- **Qualidade de Água**: Limnology (pH, Ammonia, Nitrite) and Consumption (Chlorine, ORP) metrics.
