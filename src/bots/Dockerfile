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

# Cria diretórios necessários para logs, dados e relatórios
RUN mkdir -p logs data reports

# Copia todo o código-fonte
COPY src/ /app/src/
# O .env será montado via volume ou injetado, mas mantemos uma cópia se necessário
# COPY .env /app/.env

# Define o PYTHONPATH
ENV PYTHONPATH=/app

# Comando de inicialização
CMD ["python3", "-u", "src/bots/main.py"]
