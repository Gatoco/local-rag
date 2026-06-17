# Dockerfile multi-stage para Sistema RAG Local
# Build: docker build -t local-rag .
# Run: docker-compose up -d

# ============================================================
# Stage 1: builder - compila dependencias con herramientas
# ============================================================
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /build

# Herramientas de compilación + runtime libs (llama-cpp requiere libgomp1)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Instalar uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copiar lockfile y pyproject
COPY uv.lock pyproject.toml ./

# Instalar dependencias en /install
RUN uv sync --frozen --no-dev --no-editable --python 3.12 --prefix=/install

# ============================================================
# Stage 2: runtime - imagen final limpia
# ============================================================
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

# Solo libs de runtime (sin build-essential, gcc)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependencias compiladas desde builder
COPY --from=builder /install/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /root/.local/bin/uv /usr/local/bin/uv

# Copiar código de la aplicación
COPY src ./src
COPY run_api.py run_ui.py mylocalrag.py index_docs.py reindex.py ./
COPY pyproject.toml ./

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
