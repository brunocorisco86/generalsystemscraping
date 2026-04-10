# Comandos do Telegram para Monitoramento

Este documento lista os comandos que podem ser enviados ao bot do Telegram configurado via Node-RED para obter relatórios e informações sobre a piscicultura.

## Comandos Disponíveis:

*   `/oxigenio` - Traz as leituras de oxigênio das últimas 12h.
*   `/temperatura` - Traz as leituras de temperatura das últimas 12h.
*   `/ox7d` - Traz o histórico de 7 dias de oxigênio.
*   `/ox15d` - Traz o histórico de 15 dias de oxigênio.
*   `/temp7d` - Traz o histórico de 7 dias de temperatura.
*   `/backup` - Aciona o script de migração de dados (SQLite para PostgreSQL).
*   `/previsao` - Aciona um script para plotar alguma curva ou previsão (detalhes a serem confirmados pelo script `plot_curva.py`).

## Alertas Automáticos (Push):

Além dos comandos manuais, o sistema monitora constantemente os dados e envia notificações automáticas em caso de:

1.  **Oxigênio Crítico:** Disparado quando o nível de O2 cai abaixo do limite configurado (ex: 1.5 Mg/L).
2.  **Sistema Offline:** Disparado se o sistema de coleta (scraping) não registrar novos dados por mais de 30 minutos.

Esses alertas são configurados via variáveis de ambiente (`.env`) e executados automaticamente pelo cron.
