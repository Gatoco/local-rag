# Dockerfile para Sistema RAG Local
# Build: docker build -t local-rag .
# Run: docker-compose up -d

FROM python:3.12-slim

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero (mejor cache)
COPY requirements.txt .
COPY pyproject.toml .

# Instalar dependencias de Python (dev incluye pytest, ruff, mypy)
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir ruff pytest pytest-cov mypy

# Copiar código de la aplicación
COPY . .

# Crear directorios para datos persistentes
RUN mkdir -p /app/chroma_db /app/models /app/logs /app/prompts

# Exponer puertos
# 8000: API REST
# 8501: UI Web (Streamlit)
EXPOSE 8000 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Usuario no-root (seguridad)
RUN useradd -m -u 1000 raguser && \
    chown -R raguser:raguser /app
USER raguser

# Comando por defecto
CMD ["python", "run_api.py"]
