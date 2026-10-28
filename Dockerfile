# Dockerfile Ultra-Leve (Web Dashboard + Coletor Noctua IoT + Evolution API WhatsApp)
FROM python:3.11-slim

# Instala apenas libpq5 em runtime (psycopg2-binary não exige gcc/python3-dev!)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instala apenas dependências enxutas (Sem Pandas, SciPy, Matplotlib ou LangChain)
COPY requirements-web.txt .
RUN pip install --no-cache-dir -r requirements-web.txt

# Cria diretórios essenciais da aplicação
RUN mkdir -p logs data reports

# Copia todo o código-fonte
COPY src/ /app/src/

# Configura PYTHONPATH
ENV PYTHONPATH=/app

# Exposição da porta web interna (acessada via Caddy Reverse Proxy ou porta local)
EXPOSE 5000

# Gunicorn ultra-leve: 1 worker, 2 threads e reciclagem automática de memória
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "2", "--timeout", "60", "--max-requests", "500", "--max-requests-jitter", "50", "src.web.app:app"]
