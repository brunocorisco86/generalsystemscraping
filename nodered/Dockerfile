FROM nodered/node-red:latest

# Voltamos para root para ajustar permissões
USER root

# Garantir que o diretório de dados tenha as permissões corretas (UID 1000)
RUN mkdir -p /data && chown -R 1000:1000 /data

# Volta para o usuário padrão do Node-RED
USER node-red

# Opcional: Instalar pacotes extras se necessário
# RUN npm install node-red-contrib-telegrambot
