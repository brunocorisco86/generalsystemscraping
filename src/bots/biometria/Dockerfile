# Use uma imagem base do Python 3.11 slim, que é leve e boa para Alpine
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o arquivo de dependências consolidado da raiz do projeto para o container
# O Dockerfile é executado a partir do contexto definido no docker-compose.yml,
# que será a raiz do projeto.
COPY requirements.txt .

# Instala as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código-fonte do bot para o diretório de trabalho no container
# Copiamos a pasta inteira do bot para dentro do /app
COPY src/bots/biometria/ /app/

# O comando para iniciar o bot quando o container for executado
CMD ["python3", "-u", "main.py"]
