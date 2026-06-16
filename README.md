# Local RAG

Sistema RAG local con soporte multi-provider (local + cloud). Arquitectura hexagonal (Ports & Adapters).

[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-170%2B%20passed-brightgreen.svg)](#tests)

## Features

- **Local + Cloud**: llama.cpp/LM Studio (local) o OpenAI, Anthropic, Google, Groq, MiniMax, DeepSeek (cloud)
- **Arquitectura hexagonal**: Cambia componentes sin romper la lógica de negocio
- **Seguridad**: JWT auth, argon2 hashing, rate limiting con Redis
- **Persistência**: ChromaDB vector store en disco
- **UI**: REPL interactivo, FastAPI REST, Streamlit

## Stack

| Componente | Tecnología |
|------------|------------|
| LLM Local | llama.cpp (GGUF), LM Studio |
| LLM Cloud | OpenAI, Anthropic, Google, Groq, MiniMax, DeepSeek |
| Vector Store | ChromaDB |
| Embeddings | BAAI/bge-large-en-v1.5 (1024 dims) |
| Framework | LangChain 0.3.x |
| API | FastAPI |
| Auth | JWT + argon2 |

## Modelos Soportados

### Local (gratis)

| Provider | Modelos |
|----------|---------|
| llama.cpp | Cualquier GGUF (Mistral, Llama, Phi, Qwen...) |
| LM Studio | Modelos cargados localmente |

### Cloud (requiere API key)

| Provider | Costo/1M tokens |
|----------|-----------------|
| MiniMax | ~$0.20 |
| Groq | ~$0.10 |
| DeepSeek | ~$0.10 |
| Google | ~$0.10-0.50 |
| OpenAI | ~$0.50-15 |
| Anthropic | ~$3-15 |

## Instalación

```bash
git clone https://github.com/iwakura/local-rag.git
cd local-rag
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

**Requisito**: Python 3.12

## Configuración

```bash
cp .env.example .env
# Editar .env con tus API keys y configuración
```

Variables principales:
```env
LLAMA_CPP_MODEL_PATH=./models/mistral-7b-instruct-v0.3.Q4_K_M.gguf
JWT_SECRET_KEY=tu-secret-key
ADMIN_PASSWORD=tu-password
MINIMAX_API_KEY=sk-cp-...
```

## Uso

### REPL (recomendado)

```bash
python -m src.infrastructure.entrypoints.repl.repl
```

```
╭─ local-rag ──────────────────────────────────────╮
│ cloud | minimax | RAG | docs:2400                │
╰───────────────────────────────────────────────────╯
> _
```

| Comando | Descripción |
|---------|-------------|
| `mode local/cloud` | Cambiar entre local y cloud |
| `provider <name>` | Cambiar provider cloud |
| `model <name>` | Cambiar modelo |
| `rag on/off` | Toggle RAG |
| `rag topk <n>` | Cambiar top_k (1-20) |
| `index --reindex` | Indexar documentos |
| `stats` | Ver estadísticas |

### API REST

```bash
python run_api.py
# http://localhost:8000/docs
```

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/query` | Consulta RAG |
| POST | `/api/v1/query/stream` | Streaming |
| POST | `/api/v1/ingest/file` | Ingestar archivo |
| POST | `/api/v1/ingest/directory` | Ingestar directorio |
| GET | `/api/v1/llm/providers` | Providers disponibles |

### Indexing de Documentos

```bash
# Script standalone (para datasets grandes)
python scripts/index_documents.py --reindex --timeout 1800

# Opciones: --reindex, --resume, --docs ./dir, --batch-size N
```

## Tests

```bash
pytest tests/ -v
```

## Estructura

```
src/
├── domain/           # Models (Document, Query, Answer)
│   └── ports/        # Interfaces (LLMPort, EmbeddingPort, etc.)
├── application/      # RAGService
│   └── services/
└── infrastructure/
    ├── adapters/     # ChromaDB, LLM adapters, etc.
    ├── entrypoints/   # REPL, FastAPI, CLI
    ├── security/      # JWT, rate limiting
    └── cache/        # Semantic cache
```

## Recomendaciones

| Uso | Recomendación |
|-----|---------------|
| Desarrollo/Testing | Groq (rápido, bajo costo) |
| Producción económica | MiniMax o DeepSeek |
| Máxima calidad | Anthropic Claude |
| Offline | llama.cpp local |

## Troubleshooting

**Modelo GGUF no encontrado**: Descargar de HuggingFace y colocar en `./models/`

**Primera ejecución lenta**: Normal. `llama-cpp-python` compila desde fuente (~2-5 min).

**Dependencias**: `pip install -r requirements.txt --upgrade`
