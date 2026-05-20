# Tutorial: Backup e Restauração com Cloudflare R2

Este guia explica como configurar e utilizar o sistema de backup remoto para garantir a segurança dos dados históricos da piscicultura, utilizando o Cloudflare R2 de forma gratuita.

## 1. Premissas e Custos (Free Tier)
O Cloudflare R2 é compatível com a API S3 da Amazon. O plano gratuito inclui:
- **10 GB** de armazenamento por mês.
- **1 milhão** de operações de classe A (escrita/lista) por mês.
- **10 milhões** de operações de classe B (leitura) por mês.

**Nossa Estratégia:** Ao realizar backups diários (ou semanais), consumiremos apenas ~30 operações de escrita por mês, mantendo-nos com folga dentro do limite gratuito.

## 2. Configuração no Painel da Cloudflare
1.  Acesse [dash.cloudflare.com](https://dash.cloudflare.com).
2.  Vá em **R2** no menu lateral.
3.  Clique em **Create Bucket** e nomeie como `piscicultura-backups`.
4.  Clique em **Manage R2 API Tokens** no lado direito.
5.  Clique em **Create API Token**.
    - Nome: `piscicultura-backup-token`.
    - Permissão: **Object Read & Write**.
    - Bucket: Selecione `piscicultura-backups`.
6.  Copie e salve em local seguro:
    - **Access Key ID**
    - **Secret Access Key**
    - **Jurisdiction-specific Endpoint** (Ex: `https://<account-id>.r2.cloudflarestorage.com`)

## 3. Configuração do Ambiente (.env)
Adicione as seguintes variáveis ao seu arquivo `.env` na raiz do projeto:

```env
# Cloudflare R2 Settings
R2_ACCESS_KEY_ID=seu_access_key_id
R2_SECRET_ACCESS_KEY=sua_secret_access_key
R2_ENDPOINT_URL=https://seu_account_id.r2.cloudflarestorage.com
R2_BUCKET_NAME=piscicultura-backups
```

## 4. Execução do Backup
O backup é realizado pelo script `scripts/11-backup-db.sh`. Ele faz o dump do PostgreSQL, compacta e envia para o R2 usando o `rclone`.

Para rodar manualmente:
```bash
sh scripts/11-backup-db.sh
```

### Agendamento (Cron)
Para garantir o backup **semanal** automático (ex: todo domingo às 03:00 da manhã), adicione ao seu crontab (`crontab -e`):
```cron
0 3 * * 0 cd /home/bruno/generalsystemscraping && sh scripts/11-backup-db.sh >> /home/bruno/generalsystemscraping/logs/backup.log 2>&1
```

## 5. Código de Contingência: Restauração em Novo Comissionamento
Se você precisar restaurar os dados em uma nova máquina ou após uma falha catastrófica, utilize o script de restauração:

```bash
sh scripts/13-restore-db.sh
```

### O que este script faz:
1.  Conecta ao R2 e lista os backups disponíveis.
2.  Baixa o backup mais recente para a pasta `data/backups/`.
3.  Descompacta e injeta os dados no container `piscicultura_postgres` utilizando `psql`.
4.  Garante que o banco de dados atual seja atualizado com todo o histórico recuperado.

---
**Nota de Segurança:** Nunca compartilhe seu arquivo `.env` ou suas chaves da Cloudflare. Elas dão acesso total aos seus backups históricos.
