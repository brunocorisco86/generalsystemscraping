FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Copia apenas o arquivo de dependências específico do bot
COPY src/bots/qualidade_agua/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código-fonte do bot
COPY src/bots/qualidade_agua/ /app/

ENV PYTHONUNBUFFERED=1

# O comando para iniciar o bot quando o container for executado
CMD ["python3", "-u", "main.py"]
