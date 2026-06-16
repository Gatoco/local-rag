# Proyecto Local-RAG

## Descripción

Sistema RAG (Retrieval-Augmented Generation) local multi-provider que permite hacer preguntas en lenguaje natural sobre documentos propios (PDF, DOCX, PPTX, XLSX, HTML, etc.) usando modelos LLM locales (llama.cpp) o en la nube.

## Arquitectura

- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (dev) / `BAAI/bge-large-en-v1.5` (prod)
- **Base de datos vectorial**: ChromaDB
- **LLM Local**: llama.cpp (modelos GGUF como TinyLlama)
- **LLM Cloud**: OpenAI, Anthropic (Claude), Google (Gemini), Groq, MiniMax, DeepSeek
- **Framework**: LangChain 0.3.x
- **UI**: CLI + REPL + FastAPI REST + Streamlit

## Arquitectura Hexagonal

```
src/
├── domain/                    # Modelos de dominio (Document, Query, Answer)
│   └── ports/                 # Interfaces (LLMPort, EmbeddingPort, etc.)
├── application/               # Casos de uso
│   └── services/              # RAGService
└── infrastructure/            # Implementaciones concretas
    ├── adapters/              # ChromaDB, HF Embeddings, LlamaCpp, LangChain
    ├── entrypoints/           # CLI, REPL, FastAPI, CloudChat
    │   └── repl/              # REPL estilo opencode
    ├── security/              # JWT auth, rate limiting
    └── cache/                 # SemanticCache TTL+LRU
```

## Adaptadores Disponibles

| Tipo | Implementaciones |
|---|---|
| LLM Local | `llama_cpp_llm_adapter`, `lmstudio_llm_adapter`, `ollama_llm_adapter` |
| LLM Cloud | `cloud_llm_adapter` (multi-provider) |
| Embeddings | `hf_embedding_adapter` (MiniLM, BGE-Large) |
| Vector Store | `chromadb_adapter` |
| Loader | `langchain_loader_adapter` (PDF, DOCX, PPTX, XLSX, HTML, CSV, TXT, MD) |
| RAG Chain | `langchain_rag_adapter` |

## Endpoints API (`/api/v1`)

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/metrics` | Métricas |
| POST | `/query` | Consulta RAG |
| POST | `/query/stream` | Streaming |
| POST | `/ingest/file` | Ingerir archivo |
| POST | `/ingest/directory` | Ingerir directorio |

## Entry Points

| Archivo | Uso |
|---|---|
| `python main.py` | CLI legacy |
| `python mylocalrag.py` | REPL moderno (local/cloud) |
| `python run_api.py` | API REST FastAPI |
| `python run_ui.py` | UI Streamlit |
| `python scripts/index_documents.py` | Indexador robusto (--reindex, --resume, --workers) |
| `python reindex.py` | Re-indexar con BGE-Large |

## Estructura de Directorios

```
local-rag/
├── src/                       # Código fuente
├── tests/                     # Unit, integration, benchmarks
├── agent/                     # Agente Navi-LocalRAG (MCP server, session manager)
├── agent_context/             # Documentación para el agente
├── memory/                    # Notas diarias del agente
├── prompts/                   # Templates de prompt
├── docs_to_ingest/           # Documentos a indexar
├── chroma_db/                 # Vector database (ignorado en git)
├── models/                    # Modelos GGUF (ignorado en git)
├── backups/                   # Backups automáticos (ignorado en git)
├── logs/                      # Logs de aplicación
└── .venv/                     # Virtual environment
```

## Variables de Entorno (.env)

```
# Seguridad
JWT_SECRET_KEY=<obligatorio>
ADMIN_PASSWORD=<obligatorio>
USER_PASSWORD=<obligatorio>

# LLM Local
LLAMA_CPP_MODEL_PATH=./models/TinyLlama-1.1B-Q4_K_M.gguf
N_GPU_LAYERS=0
N_CTX=4096

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHROMA_DB_PATH=./chroma_db

# Indexación
DOCS_PATH=./docs_to_ingest
CHUNK_SIZE=800
CHUNK_OVERLAP=150
TOP_K_DOCUMENTS=4

# API
API_HOST=0.0.0.0
API_PORT=8000
RATE_LIMIT_PER_MINUTE=60
```
