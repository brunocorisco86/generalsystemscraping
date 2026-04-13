# Modelo de Entidade Relacionamento (MER)

Este documento descreve a nova estrutura de dados do sistema de monitoramento de piscicultura e outras explorações.

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
        string lote
        date data_alojamento
        date data_abate
    }

    LEITURAS {
        integer id PK
        string estrutura_uid FK
        float oxigenio
        float temperatura
        timestamp timestamp_site
    }

    BIOMETRIA {
        integer id PK
        string estrutura_uid FK
        string lote
        date data_biometria
        integer quantidade
        float peso_medio
        integer mortalidade
        float consumo_racao
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
    }
```

## Entidades de Cadastro

### Proprietário
Armazena as informações do dono das propriedades. O UID é gerado via SHA256 concatenando Nome e CPF.

### Propriedade
Representa uma fazenda ou unidade produtiva. Vinculada a um proprietário. UID gerado via SHA256 concatenando Endereço e CADPRO.

### Estrutura
Unidade física onde ocorre a exploração (ex: Tanque 01, Aviário A). Vinculada a uma propriedade e a um tipo de exploração. UID gerado via SHA256 concatenando Nome e Pluscode.

### Tipo de Exploração
Catálogo de atividades suportadas (Piscicultura, Avicultura, etc).

## Tabelas de Monitoramento (Dimensionalidades)

As tabelas de `leituras`, `biometria` e `lotes` agora referenciam `estrutura_uid` em vez de nomes de tanques genéricos, permitindo rastreabilidade entre diferentes propriedades e tipos de exploração.

A qualidade da água foi dividida em duas categorias:
- **Limnologia**: Para ambientes aquáticos (peixes).
- **Consumo**: Para água de bebida animal (aves, suínos, etc).
