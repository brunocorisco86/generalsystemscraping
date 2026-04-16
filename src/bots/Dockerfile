# Dockerfile para o Bot Telegram Unificado
FROM python:3.11-slim

# Instalar dependências do sistema para Matplotlib e PostgreSQL
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instala dependências
COPY src/bots/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código-fonte (necessário para os scripts de relatórios e análises)
COPY src/ /app/src/
COPY .env /app/.env

# Define o PYTHONPATH para permitir importações do diretório /app
ENV PYTHONPATH=/app

# Comando de inicialização apontando para o bot unificado
CMD ["python3", "-u", "src/bots/main.py"]
