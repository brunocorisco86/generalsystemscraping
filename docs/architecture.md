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
- **Interface:** Telegram API (Bots).

## 3. Estrutura Modular (`src/`)

- `scrape/`: Automação de captura de dados.
- `alerts/`: Monitoramento constante e disparos de emergência.
- `bots/`: Interface de usuário para Biometria e Qualidade da Água.
- `jobs/`: Tarefas agendadas (Relatórios, Migração de dados).
- `services/`: Lógica compartilhada (DB, Notificações).

## 4. Fluxo de Dados

1.  **Captura**: O robô de scraping realiza login no site Noctua-IoT, audita os MACs dos tanques na tela `/produtor` comparando-os com o configurado localmente (`STRUCT_MACS`) para alertar sobre novos tanques em produção, e navega diretamente para as URLs das estruturas para extrair as telemetrias, salvando-as no SQLite local.
2.  **Monitoramento & Alertas**: Scripts de checagem (`alert_check.py` e `offline_check.py`) verificam o SQLite local a cada 15 min, filtrando para emitir alertas de oxigênio crítico ou sensores inativos apenas para estruturas com lotes ativos no PostgreSQL.
3.  **Interação via Bot**: O Bot do Telegram grava biometrias e dados de qualidade da água diretamente no PostgreSQL de produção, validando previamente se a estrutura tem um lote ativo para impedir lançamentos incorretos.
4.  **Consolidação (Migração)**: O script `migrate_data.py` transfere novas leituras do SQLite para o PostgreSQL seletivamente (apenas de estruturas ativas). Ele utiliza a tabela `controle_migracao` no PostgreSQL para registrar o progresso de IDs lidos do SQLite e evitar retrabalho com registros inativos.
5.  **Relatórios**: Relatórios horários e consolidados periódicos filtram os dados lidos do SQLite exibindo no Telegram apenas as telemetrias dos tanques com lotes ativos no PostgreSQL.
6.  **Auto-recuperação & Resiliência (Watchdog)**: Um script watchdog (`scripts/14-watchdog-resilience.sh`) executa periodicamente para resolver falhas de infraestrutura comum em dispositivos de borda (ex: Raspberry Pi):
    - **Falta de Memória (Swap)**: Garante que o arquivo de swap local (/swapfile) esteja ativo para evitar travamentos de OOM pelo Chromium/Selenium.
    - **Sincronização de Data/Hora Circular**: Se a data do relógio cair no passado (impedindo validações TLS/SSL), o watchdog busca a hora atual via HTTP puro do Google e ajusta o sistema operacional, restaurando a comunicação HTTPS do Tailscale e do Bot do Telegram.
    - **Serviços Críticos**: Reinicia a resolução DNS via resolvconf, e reinicia o Flask e o container Docker do bot Telegram se inativos.

---
*Foco na resiliência e produtividade real no campo.*

