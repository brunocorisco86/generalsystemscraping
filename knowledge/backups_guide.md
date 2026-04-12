# Estratégia de Backup: Mentoria e Planejamento

Este documento descreve a estratégia de preservação de dados do projeto de Piscicultura.

## 1. O Conceito: Por que Cloudflare R2?
O banco de dados PostgreSQL armazena todo o seu histórico. Se o cartão SD do seu Raspberry Pi falhar, você perde tudo. 
Usaremos o Cloudflare R2 como um "cofre externo". Ele é compatível com o padrão S3 (usado pela Amazon), mas é gratuito até 10GB para sempre.

## 2. Fluxo Planejado
1.  **Geração**: Um script extrai uma "foto" do banco de dados (`pg_dump`).
2.  **Compactação**: O arquivo é zipado para economizar espaço.
3.  **Armazenamento Local**: Uma cópia é guardada na pasta `data/backups/`.
4.  **Sincronização Cloud**: O arquivo é enviado para o Cloudflare R2.
5.  **Retenção**:
    *   **Local**: Manteremos os últimos 30 backups.
    *   **Nuvem**: Manteremos o histórico eterno (ou até atingir 10GB).

## 3. Pré-requisitos (Sua tarefa de casa)
Para prosseguirmos com a implementação, você precisará:
1.  Criar uma conta em [cloudflare.com](https://dash.cloudflare.com/sign-up).
2.  No menu lateral, vá em **R2** e ative o serviço (pode pedir um cartão de crédito para validação, mas não haverá cobrança se ficar abaixo de 10GB).
3.  Criar um "Bucket" chamado `piscicultura-backups`.
4.  Gerar as **API Tokens** (R2 API Tokens) com permissão de "Edit". Você receberá:
    *   `Access Key ID`
    *   `Secret Access Key`
    *   `Endpoint URL` (algo como `https://<account-id>.r2.cloudflarestorage.com`)

## 4. Próximos Passos Técnicos (Quando você estiver pronto)
- Criar a pasta local `data/backups`.
- Instalar a ferramenta `rclone` ou `aws-cli` no servidor.
- Configurar as credenciais no arquivo `.env`.
- Criar o script `scripts/11-backup-db.sh`.
- Agendar no Cron.

---
*Status atual: Aguardando criação da conta Cloudflare pelo usuário.*
