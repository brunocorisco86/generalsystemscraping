# Regras e Convenções do Projeto Piscicultura (general-system)

Este arquivo define as regras de desenvolvimento e operação para agentes trabalhando neste repositório.

## 1. Regra de Filtragem de Lotes Ativos (Urgente/Crítico)
*   **Premissa**: Nunca exiba relatórios, envie fotos ou dispare alertas (oxigênio crítico, offline) para estruturas (tanques) que não possuam um lote ativo.
*   **Banco de Dados**: Os lotes ativos são controlados no PostgreSQL de produção. Uma estrutura possui lote ativo se `data_abate IS NULL` na tabela `lotes`.
*   **Implementação**:
    *   Sempre consulte o PostgreSQL utilizando `get_postgres_connection()` para obter as `estruturas_ativas`.
    *   Faça o mapeamento do nome da estrutura para seu UID usando `get_all_estruturas_map()`.
    *   Sempre valide o fallback: se a conexão com o Postgres falhar (`estruturas_ativas` for `None`), não filtre nada para garantir que os alertas não fiquem mudos se o banco cair.
    *   Exemplo de padrão de verificação:
        ```python
        estruturas_map = get_all_estruturas_map()
        uid = estruturas_map.get(nome_estrutura)
        if estruturas_ativas is not None and (not uid or uid not in estruturas_ativas):
            # Ignora telemetria / alerta para estrutura inativa
            continue
        ```

## 2. Segregação SQLite (Borda) e PostgreSQL (Histórico)
*   **SQLite** (`data/piscicultura_dados.db`): Funciona como cache rápido de leitura local e coleta offline para o Selenium. O scraper insere todas as leituras brutas aqui.
*   **PostgreSQL** (`piscicultura_history`): É o banco transacional centralizado e histórico. Contém as definições de proprietários, estruturas, lotes, biometria e limnologia.
*   **Higienização**: O scraper e o script de migração devem ativamente ignorar nomes de tanques nulos, contendo `'N/A'` ou `'DESCONHECIDO'`.

## 3. Fluxo de Trabalho (Deploy via Git)
*   As modificações de código e infraestrutura no ambiente de produção devem ser efetuadas **exclusivamente via Git**.
*   Fluxo de deploy recomendado:
    1.  Efetuar as modificações no ambiente local de desenvolvimento.
    2.  Rodar a suíte de testes locais (`bash scripts/run_tests.sh`).
    3.  Realizar o commit e push para o repositório remoto (`origin main`).
    4.  No servidor de produção (`peixe`), puxar as alterações (`git pull`).
    5.  Reiniciar os serviços correspondentes (ex: `docker restart peixe_patel_bot` ou o processo do Flask web app).

## 4. Infraestrutura de Rede e DNS
*   **Servidor DNS Local**: O servidor `192.168.1.7` (`alpine`) é responsável por mapear o hostname `peixe` e `peixe.lan` para o IP estático `192.168.1.99`.
*   **Script de Saúde**: O script `scripts/check_network_health.sh` deve ser mantido no cron para auditar diariamente o status do IP estático e da resolução de nomes local.

## 5. Organização de Diários de Bordo (Diários)
*   **Localização**: Todos os diários de bordo (com o padrão de nome `diary_YYYY_MM_DD.md`) devem ser salvos exclusivamente no diretório `knowledge/diario/`.
*   **Atualização**: Ao registrar o andamento, correções ou finalização de tarefas, crie ou atualize o diário correspondente na subpasta correta para manter o histórico centralizado e organizado.
