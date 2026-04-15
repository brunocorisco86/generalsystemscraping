# Solução de Monitoramento e Automação para Piscicultura

## Visão Geral do Projeto
- Sistema robusto para coleta, análise e alerta de dados em tanques de piscicultura.
- Foco em **baixa latência**, **alta disponibilidade** e **baixo custo operacional**.
- Implementação atual em Raspberry Pi 3B com Alpine Linux, garantindo eficiência energética.
- Integração completa com Telegram para controle e notificações em tempo real.

## Arquitetura do Sistema: Fluxo de Dados
- **Coleta (Scraping):** Automação via Selenium Headless extrai dados do portal Noctua IoT a cada 15 minutos.
- **Cache Local:** SQLite armazena dados brutos temporariamente para garantir funcionamento offline.
- **Histórico:** PostgreSQL em Docker consolida dados de longo prazo para análises preditivas.
- **Alertas:** Monitoramento constante de O2 e temperatura com notificações imediatas via Telegram.

## Stack de Hardware: Eficiência no Campo
- **Dispositivo:** Raspberry Pi 3B (Quad-core 1.2GHz, 1GB RAM).
- **Sistema Operacional:** Alpine Linux (ARM64) - Escolhido pela leveza e segurança.
- **Armazenamento:** Cartão SD Industrial para maior durabilidade em ambientes úmidos.
- **Conectividade:** Wi-Fi/Ethernet com suporte a túneis para acesso remoto seguro.
- **Versatilidade:** Arquitetura compatível com migração para VPS (Cloud) sem alteração de código.

## Stack de Software: Robustez e Escalabilidade
- **Linguagem:** Python 3.11+ com bibliotecas especializadas (Pandas, Matplotlib, Aiogram).
- **Automação:** Selenium + Chromium para superação de limitações de API externa.
- **Banco de Dados:** Estratégia híbrida SQLite (Edge) + PostgreSQL (Core).
- **Orquestração:** Docker Compose para isolamento de serviços e facilidade de deploy.
- **Integração:** Node-RED para fluxos visuais e comandos dinâmicos via Telegram.

## Benefícios e Resultados
- **Monitoramento 24/7:** Redução drástica de perdas por falta de oxigenação.
- **Decisões Baseadas em Dados:** Relatórios automáticos de biometria e qualidade da água.
- **Facilidade de Uso:** Interface amigável via bots de Telegram, sem necessidade de apps complexos.
- **Escalabilidade:** Pronto para expansão para múltiplos tanques e integração com novos sensores.

## Próximos Passos e Melhorias
- Implementação de modelos de **Machine Learning** para previsão de anomalias.
- Migração opcional para VPS para centralização de múltiplos pontos de coleta.
- Expansão da interface Node-RED para dashboards web em tempo real.
- Refinamento da stack de hardware com sensores LoRaWAN para maior alcance.

## Identidade Visual e Parceria
- **Cores Institucionais:** Integração das cores C.Vale (Verde e Branco) com detalhes em **Ouro Velho**.
- Foco na excelência técnica e compromisso com a inovação no agronegócio.
- Solução desenvolvida para transformar dados em produtividade real no campo.
