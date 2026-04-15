# Modelo de Entidade Relacionamento (MER)

Este documento descreve a estrutura de dados atualizada do sistema de monitoramento de piscicultura, refletindo o padrão técnico C.VALE / PATEL e a arquitetura multilocação (propriedades e estruturas).

## Diagrama

```mermaid
erDiagram
    PROPRIETARIO ||--o{ PROPRIEDADE : possui
    PROPRIETARIO ||--o{ USUARIOS_TELEGRAM : vinculado
    PROPRIEDADE ||--o{ ESTRUTURA : contem
    TIPO_EXPLORACAO ||--o{ ESTRUTURA : define
    ESTRUTURA ||--o{ LOTES : abriga
    ESTRUTURA ||--o{ LEITURAS : registra
    ESTRUTURA ||--o{ BIOMETRIA : monitora
    ESTRUTURA ||--o{ QUALIDADE_AGUA_LIMNOLOGIA : analisa
    ESTRUTURA ||--o{ QUALIDADE_AGUA_CONSUMO : analisa

    PROPRIETARIO {
        string uid PK "Hash SHA256(Nome + CPF)"
        string nome
        string cpf
    }

    USUARIOS_TELEGRAM {
        bigint telegram_id PK
        string proprietario_uid FK
        string username
        string nome_completo
    }

    PROPRIEDADE {
        string uid PK "Hash SHA256(Endereco + CADPRO)"
        string proprietario_uid FK
        string nome
        string endereco
        string cadpro
    }

    TIPO_EXPLORACAO {
        integer id PK
        string nome
    }

    ESTRUTURA {
        string uid PK "Hash SHA256(Nome + Pluscode)"
        string propriedade_uid FK
        integer tipo_exploracao_id FK
        string nome
        string pluscode
    }

    LOTES {
        serial id PK
        string estrutura_uid FK
        string lote "Identificador textual (ex: 2024/01)"
        date data_alojamento
        date data_abate "Nulo se ativo"
        integer peixes_alojados
        float peso_medio "Peso inicial (g)"
        float area_acude "m²"
        float densidade "peixes/m²"
        integer qtd_peixes_entregues
        float peso_entregue "kg"
        float pct_rend_file "Rendimento %"
        float reais_por_peixe
        text descricao
    }

    LEITURAS {
        integer id PK
        string estrutura_uid FK
        string nome_estrutura "Nome amigável (ex: Tanque 01)"
        float oxigenio
        float temperatura
        timestamp timestamp_site "Data vinda do hardware"
        timestamp data_coleta "Data da gravação no BD"
        integer aeradores_ativos
    }

    BIOMETRIA {
        integer id PK
        string estrutura_uid FK
        string lote FK
        date data_biometria
        integer quantidade "Estoque estimado"
        float peso_medio "g"
        integer mortalidade
        float consumo_racao "kg"
        timestamp created_at
    }

    QUALIDADE_AGUA_LIMNOLOGIA {
        serial id PK
        string estrutura_uid FK
        date data_coleta
        time hora_coleta
        float ph
        float amonia
        float nitrito
        float alcalinidade
        float transparencia
        timestamp created_at
    }

    QUALIDADE_AGUA_CONSUMO {
        serial id PK
        string estrutura_uid FK
        date data_coleta
        time hora_coleta
        float ph
        float sdt
        float orp
        float ppm_cloro
        timestamp created_at
    }
```

## Entidades de Cadastro

### Proprietário e Usuários
Gestão de acesso e vínculo. O UID é imutável e gerado por hash para garantir privacidade e unicidade.

### Estrutura
Unidade física produtiva. O campo `nome` é o que aparece no dashboard, enquanto o `uid` garante a integridade dos dados históricos mesmo se o tanque for renomeado.

## Tabelas de Monitoramento (Operacional)

### Lotes (Ciclo de Vida)
Implementa o padrão de "Ficha Verde". Registra desde a entrada (alojamento) com densidade automática até o fechamento financeiro (abate/rendimento).

### Leituras (Telemetria)
Armazena os dados vindos do Scraper. Inclui `nome_estrutura` para facilitar relatórios rápidos e `aeradores_ativos` para monitoramento de automação.

### Biometria e Qualidade da Água
Registros manuais feitos via Bots Telegram. Estão vinculados à estrutura e, no caso da biometria, ao lote vigente para cálculo de Conversão Alimentar (CA).
