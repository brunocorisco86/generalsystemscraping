# Guia de Comissionamento: Dashboard Web Local

Este documento descreve os passos para instalar, configurar e iniciar o painel de controle web da piscicultura no Raspberry Pi.

## 1. Pré-requisitos
*   Ambiente virtual Python configurado (`.venv`).
*   Banco de dados SQLite existente com a tabela `leituras` (gerada pelo scraper).
*   Variáveis de ambiente configuradas no arquivo `.env`.

## 2. Configuração do Ambiente (.env)
Certifique-se de que as seguintes variáveis existam no seu arquivo `.env`:

```bash
# Credenciais de acesso ao Painel Web
WEB_ADMIN_USER=admin
WEB_ADMIN_PASS=sua_senha_segura
FLASK_SECRET_KEY=uma_chave_aleatoria_longa

# Caminhos (Padrão)
LOGS_DIR=logs
SQLITE_DB_PATH=data/piscicultura_dados.db
```

## 3. Instalação de Dependências
Atualize o seu ambiente virtual para incluir o Flask e as novas bibliotecas:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

## 4. Inicialização do Serviço
O dashboard pode ser iniciado manualmente usando o script utilitário:

```bash
bash scripts/12-start-web.sh
```

O serviço estará disponível no endereço: `http://<IP_DO_RASPBERRY>:5000`

## 5. Verificação e Testes
1.  **Acesso:** Abra o navegador e verifique se a tela de login aparece.
2.  **Login:** Use as credenciais configuradas no passo 2.
3.  **Dados:** Verifique se os cards exibem as últimas leituras de oxigênio.
4.  **Ações:** Tente clicar em "Sincronizar Bancos" e verifique se o alerta de sucesso aparece sem disparar mensagens redundantes no Telegram.

## 6. Logs e Solução de Problemas
Os logs do painel web são salvos separadamente para facilitar a análise:
*   Arquivo: `logs/web_dashboard.log`

Se o servidor não iniciar, verifique se a porta `5000` não está sendo usada por outro processo.
