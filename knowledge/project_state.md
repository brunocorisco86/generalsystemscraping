# Project State (AI Context Compression)

## Tech Stack & Runtime

- **OS**: Alpine Linux (ARM64) / Raspberry Pi 3B.
- **Python**: 3.11+ (venv managed by `scripts/setup.sh`).
- **Containers**: Docker Compose (PostgreSQL, Unified Telegram Bot).
- **Automation**: Telegram Command Interface -> Python Scripts.
- **Database**: Hybrid SQLite (Local/Edge cache) + PostgreSQL (Long-term history).
- **UI/UX**: Telegram Bots (Biometria, Qualidade da Água).
- **AI Agent**: Google Gemini (via LangChain Tools) para chat livre, filtragem inteligente de alertas e **predição de arraçoamento (Parecer do Especialista)**.

## Core Data Flow

1. **Scrape**: `src/scrape/monitor_data.py` (via Selenium/Headless Chromium) runs every 10 min (1-59/10) via Cron. Persists to `data/piscicultura_dados.db` (SQLite).
2. **Weather Sync**: `src/jobs/hourly_weather_sync.py` runs every hour (minuto 01) to persist ambient temp, pressure, and humidity to SQLite.
3. **Alerts**: `src/alerts/alert_check.py` and `offline_check.py` run every 15 min.
   - **AI Validation**: Critical alerts analyzed by Gemini.
4. **Feed Prediction**: `src/analysis/feed_prediction.py` (09:00 via Cron).
   - **Data Integration**: Combines water O2/Temp, ambient Temp/Pressure/Humidity.
   - **AI Specialist**: Generates a "Micro-Context" summary for Gemini, obtaining an expert recommendation on whether to feed or wait based on metabolism and environmental stress.
5. **Jobs**: `src/jobs/` handles periodic reporting and data migration (SQLite -> Postgres).

## Critical Knowledge & Recent Fixes

- **Migration Fix**: Ensured `init_db` and `migrate_data` run via `docker exec` in `07-start-containers.sh` to resolve host naming issues (`postgres`) on new Raspberry Pi deployments.
- **Weather Automation**: Consolidated to `hourly_weather_sync` (min 01) and `morning_weather_report` (07:05). Removed redundant weather service cron calls.
- **Feed Prediction Optimization**: Integrated water and ambient temperatures + atmospheric pressure. Added AI-driven icons (✅/⚠️) based on specialist's textual feedback (TDD verified).
- **Timezone Enforcement**: All comparisons use `America/Sao_Paulo`.
- **Environment**: All configuration resides in `.env`. Root path is dynamically detected.

## Domain Concepts

- **Ficha Verde (Green Sheet)**: Standardized data model for fish growth tracking.
- **Biometria**: Weight and health checks logged by users via bot.
- **Qualidade de Água**: Limnology (pH, Ammonia, Nitrite) and Consumption (Chlorine, ORP) metrics.
