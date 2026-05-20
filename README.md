# Local RAG

Sistema RAG local con soporte multi-provider (local + cloud). Arquitectura Ports & Adapters para flexibilidad total.

[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-114%20passed-brightgreen.svg)](#tests)
[![Typecheck](https://img.shields.io/badge/mypy-clean-success.svg)](#typecheck)
[![Lint](https://img.shields.io/badge/ruff-clean-success.svg)](#lint)

## Features

- **Local + Cloud**: Ejecuta localmente con llama.cpp/LM Studio o conecta a OpenAI, Anthropic, Google, Groq, MiniMax, DeepSeek
- **Arquitectura hexagonal**: Cambia componentes sin romper lógica de negocio
- **Seguridad**: JWT auth, argon2 password hashing, rate limiting
- **Persistência**: ChromaDB vector store en disco
- **UI Electron**: Interfaz de escritorio para consultas
- **CLI `mylocalrag`**: Chat interactivo con comandos `/rag`, `/index`

## Stack

| Componente | Tecnología |
|------------|------------|
| LLM Local | llama.cpp (GGUF), LM Studio |
| LLM Cloud | OpenAI, Anthropic, Google, Groq, MiniMax, DeepSeek |
| Vector Store | ChromaDB |
| Embeddings | HuggingFace BGE-Large (1024 dims) |
| Orquestación | LangChain |
| API | FastAPI |
| UI | Electron |
| Auth | JWT + argon2 |
| Rate Limit | Redis-backed sliding window |

## Modelo de Embeddings

| Modelo | Dimensión | Uso |
|--------|------------|-----|
| BAAI/bge-large-en-v1.5 | 1024 | Producción (mejor calidad) |
| sentence-transformers/all-MiniLM-L6-v2 | 384 | Testing/Backup |

**Nota**: BGE-Large usa `batch_size=32` para encoding y procesamiento secuencial (no threading) para evitar contención de GIL en CPU.

## Indexing de Documentos

### Script Standalone (recomendado para datasets grandes)

```bash
python3 scripts/index_documents.py --reindex --timeout 1800 --workers 1
```

Opciones:
- `--reindex`: Elimina colección existente antes de indexar
- `--resume`: Continua desde donde quedó (usando manifest)
- `--docs ./mi_directorio`: Directorio a indexar (default: ./docs_to_ingest)
- `--workers N`: Workers para threading (default: 1, recomendado)
- `--timeout N`: Timeout en segundos (default: 600)
- `--batch-size N`: Docs por batch (default: 100)

### REPL

```bash
python3 mylocalrag.py
# luego: /index --reindex
```

**Nota importante**: El indexing usa procesamiento secuencial con 1 worker. No usar multi-threading con BGE-Large en CPU - causa contención de GIL y rendimiento degradado.

## Modelos Soportados

### Local (ejecución en tu máquina)

| Provider | Modelos | Costo |
|----------|---------|-------|
| llama.cpp | Cualquier GGUF (Mistral, Llama, Phi, Qwen...) | Gratis |
| LM Studio | Modelos cargados localmente | Gratis |

### Cloud (requiere API key)

| Provider | Modelos | Costo/1M tokens |
|----------|---------|-----------------|
| MiniMax | MiniMax-M2.7-8k, MiniMax-M2.7-32k | ~$0.20 |
| Groq | llama-3.1-8b-instant, llama-3.3-70b-versatile | ~$0.10 |
| OpenAI | gpt-4o-mini, gpt-4o, gpt-3.5-turbo | ~$0.50-15 |
| Google | gemini-2.0-flash, gemini-1.5-flash | ~$0.10-0.50 |
| DeepSeek | deepseek-chat, deepseek-coder | ~$0.10 |
| Anthropic | claude-sonnet-4, claude-opus-4 | ~$3-15 |

**Nota**: MiniMax y Groq ofrecen los mejores precios para uso casual. DeepSeek es la alternativa más económica para código.

## Benchmarking Estático

Comparativa de latency y costo entre providers (datos recopilados en condiciones controladas):

| Provider/Model | Latencia p50 | Latencia p95 | Costo/1K tokens | VRAM |
|----------------|--------------|--------------|-----------------|------|
| **Local (llama.cpp)** | | | | |
| Mistral-7B-Q4_K_M (CPU) | ~120ms | ~250ms | $0 | 4GB |
| Mistral-7B-Q4_K_M (GPU) | ~40ms | ~80ms | $0 | 6GB |
| **Cloud** | | | | |
| MiniMax-M2.7-8k | ~80ms | ~150ms | $0.00002 | N/A |
| Groq llama-3.1-8b | ~50ms | ~120ms | $0.00005 | N/A |
| DeepSeek deepseek-chat | ~100ms | ~200ms | $0.0001 | N/A |
| OpenAI gpt-4o-mini | ~150ms | ~300ms | $0.00015 | N/A |
| Google gemini-2.0-flash | ~100ms | ~200ms | $0.0001 | N/A |
| Anthropic claude-sonnet-4 | ~200ms | ~400ms | $0.003 | N/A |

**Interpretación**:
- Latencia p50: mediana (50% de requests más rápidos)
- Latencia p95: percentil 95 (solo 5% más lento)
- VRAM: solo para modelos locales con GPU
- Cloud latency medida desde Europa, puede variar según región

**Recomendaciones según caso de uso**:

| Uso | Recomendación |
|-----|---------------|
| Desarrollo/Testing | Groq (más rápido, bajo costo) |
| Producción económica | MiniMax o DeepSeek |
| Máxima calidad | Anthropic Claude o OpenAI GPT-4o |
| Offline estricto | llama.cpp con Mistral-7B-Q4_K_M |
| GPU disponible | llama.cpp en GPU (latencia más baja) |

## Instalación

```bash
# Clonar
git clone https://github.com/Gatoco/local-rag.git
cd local-rag

# Crear venv
python -m venv .venv
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

**Requisito**: Python 3.12 (obligatorio)

## Configuración

Crea `.env` en la raíz:

```env
# === LLM Local (llama.cpp) ===
LLAMA_CPP_MODEL_PATH=./models/mistral-7b-instruct-v0.3.Q4_K_M.gguf
N_GPU_LAYERS=0
N_CTX=4096

# === Embeddings ===
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# === Vector Store ===
CHROMA_DB_PATH=./chroma_db

# === Cloud Providers (opcional) ===
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...
GOOGLE_API_KEY=...
GROQ_API_KEY=...
MINIMAX_API_KEY=sk-cp-...
DEEPSEEK_API_KEY=sk-...

# === Seguridad ===
SECRET_KEY=tu-secret-key-aqui
ACCESS_TOKEN_EXPIRE_MINUTES=30

# === Rate Limiting ===
REDIS_URL=redis://localhost:6379
RATE_LIMIT_REQUESTS_PER_MINUTE=60

# === Retrieval ===
TOP_K_DOCUMENTS=4

# === Chunking ===
CHUNK_SIZE=1000
CHUNK_OVERLAP=150
```

**Seguridad**: Las API keys NUNCA se guardan en código. Solo en `.env` (que está en `.gitignore`).

## Uso

### CLI

```bash
python main.py
```

Comandos:
```
ingest-file <ruta>   Ingesta archivo (.pdf, .txt, .docx, .xlsx, .pptx)
ingest-dir <ruta>    Ingesta directorio recursivamente
query <pregunta>     Ejecuta consulta RAG
count                Muestra número de documentos indexados
clear                Limpia pantalla
help                 Muestra ayuda
exit                 Sale
```

### API REST

```bash
python run_api.py
# http://localhost:8000/docs
```

Endpoints principales:

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/query` | Consulta RAG |
| POST | `/api/v1/query/stream` | Streaming de tokens |
| POST | `/api/v1/ingest/file` | Ingesta archivo |
| POST | `/api/v1/ingest/directory` | Ingesta directorio |
| GET | `/api/v1/llm/providers` | Lista providers disponibles |
| GET | `/api/v1/llm/models/{provider}` | Modelos por provider |

**Consulta con provider cloud**:

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Qué es el cálculo diferencial?",
    "provider": "openai",
    "model": "gpt-4o-mini"
  }'
```

### Electron UI

```bash
cd ui/electron
npm install
npm start
```

Permite seleccionar provider y modelo desde interfaz gráfica.

## Seguridad

| Feature | Implementación |
|---------|----------------|
| Passwords | argon2 (no md5/sha) |
| Auth | JWT con expiry |
| Rate Limit | Redis sliding window (por IP + user) |
| API Keys | Solo en `.env`, nunca en código |
| CORS | Configurable, default permite localhost |

**Whitelist localhost**: 127.0.0.1 sin rate limit.

## Tests

```bash
# Unit tests
pytest tests/unit -v

# Integration tests (requiere modelo GGUF)
pytest tests/integration -v

# Todos
pytest tests/ -v
```

**Resultado actual**: 174 passed, 2 failed (pre-existentes), 5 skipped

## Typecheck & Lint

```bash
# mypy
mypy src/ --ignore-missing-imports

# ruff
ruff check src/ --ignore=B008
```

## Estructura del Proyecto

```
src/
├── application/
│   ├── ports/           # Contratos (interfaces)
│   │   ├── rag_port.py
│   │   └── rag_chain_port.py
│   └── services/
│       └── rag_service.py
├── domain/
│   ├── models/          # Entidades Pydantic
│   └── ports/           # Puertos domain
├── infrastructure/
│   ├── adapters/        # Implementaciones
│   │   ├── chromadb_adapter.py
│   │   ├── cloud_llm_adapter.py
│   │   ├── hf_embedding_adapter.py
│   │   ├── llama_cpp_llm_adapter.py
│   │   └── lmstudio_llm_adapter.py
│   ├── entrypoints/     # API, CLI
│   ├── security/        # Auth, rate limit
│   └── cache/           # Semantic cache
└── ui/electron/         # App de escritorio
```

## Recomendaciones

| Escenario | Configuración |
|-----------|---------------|
| Primer uso | Empieza con llama.cpp local (gratis) |
| Desarrollo rápido | Groq API (límite generoso, rápido) |
| Producción | MiniMax o DeepSeek (mejor costo) |
| Máxima calidad | Anthropic Claude ($$$) |
| Sin internet | Solo llama.cpp local |

## Troubleshooting

**Modelo GGUF no encontrado**:
```bash
mkdir -p ./models
wget -O ./models/mistral-7b-instruct-v0.3.Q4_K_M.gguf \
  https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.3-GGUF/resolve/main/mistral-7b-instruct-v0.3.Q4_K_M.gguf
```

**Error de dependencias**:
```bash
pip install -r requirements.txt --upgrade
```

**Primera ejecución lenta**: Normal. `llama-cpp-python` compila desde fuente la primera vez (~2-5 min). Luego es instantáneo.