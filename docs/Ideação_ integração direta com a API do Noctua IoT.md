# Ideação: integração direta com a API do Noctua IoT

## Objetivo

Substituir o scraping das telas por chamadas diretas à API usada pelo painel Noctua IoT. O projeto deverá permitir:

1. consumir as leituras dos sensores dos dois tanques;
2. consultar programação de liga/desliga;
3. consultar e alterar thresholds de automação;
4. consultar o estado dos motores e equipamentos;
5. enviar comandos de acionamento, desligamento ou alteração de estado;
6. acompanhar o resultado dos comandos.

A integração deve começar em **modo somente leitura**. O envio de comandos e as alterações de configuração devem ser habilitados somente depois da validação do protocolo.

## Identificação dos ativos

| Ativo | `endpointId` | `gatewayId` |
|---|---|---|
| Tanque 1 | `10:20:BA:66:2E:C8` | `10:20:BA:65:3A:B8` |
| Tanque 2 | `10:20:BA:6A:90:00` | `10:20:BA:65:3A:B8` |

## Endpoint de comunicação

O sistema não aparenta expor uma API REST convencional para os sensores. A comunicação é feita por **AWS AppSync GraphQL** através de requisições HTTP `POST`:

```text
POST https://qhurq5cthrd75ppzeyutzcclje.appsync-api.sa-east-1.amazonaws.com/graphql
```

Formato básico da chamada:

```http
Content-Type: application/json
X-Api-Key: <CHAVE_APPSYNC>
```

Corpo:

```json
{
  "query": "<QUERY_OU_MUTATION_GRAPHQL>",
  "variables": {}
}
```

A chave da API deve ser mantida fora do código-fonte, preferencialmente em variável de ambiente ou em um arquivo de credenciais protegido.

## 1. Consumir os dados atuais dos sensores

A operação identificada para leituras recentes é:

```text
listSensorDataByGatewayIdAndUpdatedAt
```

Consulta sugerida:

```graphql
query ListSensorData(
  $gatewayId: ID!,
  $updatedAt: ModelStringKeyConditionInput,
  $limit: Int,
  $nextToken: String,
  $sortDirection: ModelSortDirection
) {
  listSensorDataByGatewayIdAndUpdatedAt(
    gatewayId: $gatewayId
    updatedAt: $updatedAt
    limit: $limit
    nextToken: $nextToken
    sortDirection: $sortDirection
  ) {
    items {
      id
      gatewayId
      endpointId
      bucketId
      ts
      o2
      sat
      temperature
      hpa
      engines
      o2Readings
      probe
      timer
      rssi
      snr
      criticalO2
      criticalO2Max
      errors
      createdAt
      updatedAt
    }
    nextToken
  }
}
```

Variáveis para obter dados recentes dos dois tanques:

```json
{
  "gatewayId": "10:20:BA:65:3A:B8",
  "limit": 100,
  "sortDirection": "DESC"
}
```

Como os dois tanques compartilham o mesmo gateway, o resultado deve ser separado pelo campo `endpointId`.

### Campos principais

| Campo | Significado |
|---|---|
| `o2` | Oxigênio dissolvido em mg/L |
| `sat` | Saturação de oxigênio em percentual |
| `temperature` | Temperatura da água |
| `hpa` | Pressão/indicador HPA reportado pelo dispositivo |
| `engines` | Estado reportado dos motores, aparentemente em string binária |
| `o2Readings` | Leituras individuais ou auxiliares da sonda |
| `rssi` | Intensidade do sinal |
| `snr` | Relação sinal/ruído |
| `errors` | Flags de erro do dispositivo |
| `ts` | Momento da medição |
| `updatedAt` | Momento da atualização no backend |

A coleta deve respeitar `nextToken`. Sem essa paginação, uma consulta com muitos registros poderá retornar somente a primeira página.

## 2. Consumir dados históricos horários

Para histórico agregado por hora, utilizar:

```text
listHourlyDataByEndpointIdAndTimestamp
```

Consulta:

```graphql
query ListHourlyData(
  $endpointId: ID!,
  $timestamp: ModelStringKeyConditionInput,
  $limit: Int,
  $nextToken: String,
  $sortDirection: ModelSortDirection
) {
  listHourlyDataByEndpointIdAndTimestamp(
    endpointId: $endpointId
    timestamp: $timestamp
    limit: $limit
    nextToken: $nextToken
    sortDirection: $sortDirection
  ) {
    items {
      id
      gatewayId
      endpointId
      timestamp
      o2
      sat
      temp
      hpa
      engines
      rssi
      snr
      errors
      createdAt
      updatedAt
    }
    nextToken
  }
}
```

Variáveis para o Tanque 1:

```json
{
  "endpointId": "10:20:BA:66:2E:C8",
  "limit": 168,
  "sortDirection": "DESC"
}
```

Para o Tanque 2, trocar o `endpointId` por:

```text
10:20:BA:6A:90:00
```

## 3. Consultar programação, thresholds e estado dos equipamentos

A configuração parece estar no modelo `Endpoint`. Os campos relevantes são:

```text
timer
autoOn
engines
criticalO2
criticalO2Max
o2Ajusted
```

Consulta sugerida:

```graphql
query GetEndpoint($id: ID!) {
  getEndpoint(id: $id) {
    id
    gatewayId
    name
    timer
    autoOn
    engines
    criticalO2
    criticalO2Max
    o2Ajusted
    createdAt
    updatedAt
  }
}
```

Variável para o Tanque 1:

```json
{
  "id": "10:20:BA:66:2E:C8"
}
```

Variável para o Tanque 2:

```json
{
  "id": "10:20:BA:6A:90:00"
}
```

### Programação de liga/desliga

O campo `timer` contém um JSON com as janelas de funcionamento. A estrutura observada possui elementos como:

```json
{
  "enabled": false,
  "timers": [
    {
      "id": 0,
      "timeOn": "14:00",
      "timeOff": "14:20",
      "enabled": false,
      "motors": {
        "0": true,
        "1": true,
        "2": true,
        "3": true,
        "4": true
      }
    }
  ]
}
```

Antes de alterar o campo, deve-se preservar o JSON inteiro. Não é recomendável enviar somente um fragmento, porque isso pode apagar outras janelas ou configurações.

### Thresholds

Os campos identificados para controle de oxigênio são:

```text
criticalO2
criticalO2Max
```

Também devem ser considerados:

```text
autoOn
o2Ajusted
```

A semântica exata de `criticalO2Max` e `o2Ajusted` deve ser confirmada comparando os valores da tela, o comportamento da automação e os registros de `EngineLogs`. O nome do campo sozinho não é suficiente para definir uma lógica operacional segura.

## 4. Alterar threshold ou programação

A alteração provavelmente será feita por uma mutation GraphQL gerada pelo Amplify:

```text
updateEndpoint
```

Estrutura provável:

```graphql
mutation UpdateEndpoint($input: UpdateEndpointInput!) {
  updateEndpoint(input: $input) {
    id
    gatewayId
    name
    timer
    autoOn
    engines
    criticalO2
    criticalO2Max
    o2Ajusted
    updatedAt
  }
}
```

Exemplo conceitual para alterar o threshold mínimo do Tanque 1:

```json
{
  "input": {
    "id": "10:20:BA:66:2E:C8",
    "criticalO2": 2.5
  }
}
```

Exemplo conceitual para habilitar a automação:

```json
{
  "input": {
    "id": "10:20:BA:66:2E:C8",
    "autoOn": true
  }
}
```

Exemplo conceitual para alterar a programação:

```json
{
  "input": {
    "id": "10:20:BA:66:2E:C8",
    "timer": "{\"enabled\":true,\"timers\":[{\"id\":0,\"timeOn\":\"14:00\",\"timeOff\":\"14:20\",\"enabled\":true,\"motors\":{\"0\":true,\"1\":true,\"2\":true,\"3\":true,\"4\":true}}]}"
  }
}
```

Esses exemplos representam o formato provável. Antes de executar uma alteração real, é necessário confirmar no schema ativo se os tipos de entrada, campos obrigatórios e permissões estão exatamente assim.

### Procedimento seguro para alteração

1. Consultar o `Endpoint` atual.
2. Salvar uma cópia do JSON original.
3. Validar o novo valor dentro de limites operacionais aprovados.
4. Enviar a mutation.
5. Consultar novamente o `Endpoint`.
6. Registrar quem alterou, quando alterou, valor anterior e valor novo.
7. Confirmar a mudança nos logs e na telemetria.

## 5. Acionar ou desligar motores

O schema possui o modelo:

```text
CommandMessages
```

Campos identificados:

```text
messageId
endpointId
gatewayId
command
message
status
createdAt
updatedAt
```

Os status possíveis incluem:

```text
SENT
GATEWAY_OFFLINE
ENDPOINT_OFFLINE
DELIVERED
```

Isso indica que o acionamento provavelmente ocorre por uma mutation GraphQL que cria uma mensagem de comando, em vez de um `PATCH` REST.

Mutation provável:

```graphql
mutation CreateCommand($input: CreateCommandMessagesInput!) {
  createCommandMessages(input: $input) {
    messageId
    endpointId
    gatewayId
    command
    message
    status
    createdAt
    updatedAt
  }
}
```

Estrutura provável:

```json
{
  "input": {
    "messageId": "uuid-gerado",
    "endpointId": "10:20:BA:66:2E:C8",
    "gatewayId": "10:20:BA:65:3A:B8",
    "command": "<comando-do-protocolo>",
    "message": "Acionamento manual autorizado"
  }
}
```

### Limitação crítica

O formato exato de `command` ainda não foi confirmado. Não é seguro assumir que o sistema aceite textos como:

```text
MOTOR_1_ON
MOTOR_1_OFF
```

O valor pode ser um opcode, uma string codificada ou um JSON específico do gateway. O protocolo deve ser descoberto capturando uma operação real da interface ou analisando os comandos registrados em `EngineLogs` e `CommandMessages`.

### Confirmação do resultado

Depois de enviar um comando, não basta considerar a resposta HTTP como sucesso. O processo deve:

1. guardar o `messageId`;
2. consultar o status em `CommandMessages`;
3. verificar se o resultado foi `DELIVERED`;
4. consultar `EngineLogs`;
5. conferir a telemetria `SensorData.engines`;
6. registrar divergências entre o comando enviado e o estado efetivamente reportado.

Consultas auxiliares identificadas:

```text
getCommandByMessageId
listCommandsByEndpoint
listCommandsByStatus
enginesEndpointIdTimestampIndex
```

## 6. Operações que devem ser implementadas no cliente

O cliente Python, Node-RED ou outra ferramenta de integração deverá expor funções separadas:

```python
def get_latest_sensor_data(gateway_id, limit=100): ...

def get_hourly_sensor_data(endpoint_id, start, end): ...

def get_endpoint_config(endpoint_id): ...

def update_endpoint_threshold(endpoint_id, critical_o2, critical_o2_max): ...

def update_endpoint_timer(endpoint_id, timer_json): ...

def send_motor_command(endpoint_id, command): ...

def get_command_status(message_id): ...
```

As funções de leitura podem ser utilizadas pelo scraping substituto imediatamente. As funções de alteração e comando devem permanecer bloqueadas até que o schema e o protocolo tenham sido validados.

## 7. Critérios mínimos de segurança

- Usar allowlist dos dois `endpointId` conhecidos.
- Rejeitar comandos para endpoints desconhecidos.
- Não permitir que uma entrada livre do usuário seja enviada diretamente como `command`.
- Limitar valores de threshold a faixas aprovadas.
- Exigir confirmação explícita antes de qualquer acionamento.
- Registrar usuário, horário, payload, resposta e status final.
- Bloquear comandos quando `GATEWAY_OFFLINE` ou `ENDPOINT_OFFLINE` estiverem presentes.
- Separar credenciais de leitura das credenciais de alteração, se o AppSync permitir.
- Nunca executar automaticamente um comando baseado apenas em uma leitura isolada.
- Implementar timeout, idempotência e prevenção de reenvio acidental.

## 8. Ordem recomendada de implementação

### Etapa 1 — Leitura

Implementar as queries de `SensorData`, `HourlySensorData` e `Endpoint`. Salvar respostas brutas e normalizadas.

### Etapa 2 — Configuração

Implementar somente a consulta de `timer`, `autoOn`, `criticalO2`, `criticalO2Max` e `o2Ajusted`. Comparar os valores com o painel.

### Etapa 3 — Alteração controlada

Implementar `updateEndpoint` em modo protegido, começando por uma alteração reversível e documentada em um único tanque.

### Etapa 4 — Comandos

Descobrir e validar o protocolo de `CommandMessages`. Depois, implementar uma allowlist de comandos e acompanhar a confirmação em `EngineLogs` e `SensorData`.

## Conclusão

O projeto pode deixar de fazer scraping e consumir diretamente o GraphQL do Noctua IoT. A leitura dos sensores e da configuração já está suficientemente mapeada. Alterar thresholds e programação provavelmente será feito por `updateEndpoint`. Acionar motores provavelmente será feito por `createCommandMessages`.

A única parte que ainda não deve ser automatizada é o valor exato do campo `command`. Esse protocolo precisa ser confirmado antes de qualquer liga/desliga real.

## Referências

[1]: https://general-system.noctua-iot.com/ "Painel General System / Noctua IoT"
[2]: https://docs.aws.amazon.com/appsync/latest/devguide/graphql-overview.html "AWS AppSync GraphQL API overview"
[3]: https://docs.amplify.aws/gen1/javascript/build-a-backend/graphqlapi/mutate-data/ "AWS Amplify GraphQL mutations"
