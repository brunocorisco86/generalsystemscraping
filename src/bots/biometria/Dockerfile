# Use uma imagem base do Python 3.11 slim, que é leve e boa para Alpine
FROM python:3.11-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia apenas o arquivo de dependências específico do bot
COPY src/bots/biometria/requirements.txt .

# Instala as dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código-fonte do bot
COPY src/bots/biometria/ /app/

# O comando para iniciar o bot quando o container for executado
CMD ["python3", "-u", "main.py"]
