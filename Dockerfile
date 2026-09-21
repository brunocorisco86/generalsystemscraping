# Dockerfile Multi-serviço (Web Dashboard & Coletor IoT)
FROM python:3.11-slim

# Instala apenas dependências do SO necessárias para psycopg2 e compilação básica
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia e instala dependências enxutas do projeto
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Cria diretórios essenciais da aplicação
RUN mkdir -p logs data reports

# Copia todo o código-fonte
COPY src/ /app/src/

# Configura PYTHONPATH
ENV PYTHONPATH=/app

# Exposição da porta web padrão interna
EXPOSE 5000

# Comando padrão (Web com Gunicorn)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "60", "src.web.app:app"]
