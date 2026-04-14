# Use the official Node-RED image as a base (Alpine based)
FROM nodered/node-red:latest

# Switch to root to install system dependencies
USER root

# Install bash and python3 (needed for your exec nodes)
RUN apk add --no-cache bash python3

# Switch back to node-red user
USER node-red

# Set the working directory
WORKDIR /usr/src/node-red

# Copy Node-RED flows
COPY --chown=node-red:node-red flows.json /data/flows.json

# Install Node-RED dependencies
RUN npm install node-red-contrib-telegrambot

# Expose the Node-RED port
EXPOSE 1880

# Start Node-RED
CMD ["npm", "start", "--", "--userDir", "/data"]
