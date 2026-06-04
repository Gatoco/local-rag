# Proyecto Local-RAG

## Descripción

Sistema RAG (Retrieval-Augmented Generation) local que permite hacer preguntas sobre documentos PDF usando modelos de lenguaje locales.

## Arquitectura

- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2) via HuggingFace
- **Base de datos vectorial**: ChromaDB
- **LLM**: Modelos GGUF (Mistral, TinyLlama, etc.) ejecutados via llama.cpp
- **Framework**: LangChain
- **UI**: CLI interactiva + Electron (opcional)

## Estructura de Directorios

```
local-rag/
├── src/
│   ├── infrastructure/
│   │   ├── adapters/         # ChromaDB, HF Embeddings, LlamaCpp, LangChain
│   │   ├── entrypoints/      # CLI, REPL
│   │   ├── utils/            # Logging, validators
│   │   └── security/         # Rate limiters
│   └── application/
│       └── services/         # RAG Service
├── tests/
│   ├── unit/
│   ├── integration/
│   └── benchmarks/
├── models/                   # GGUF models
├── chroma_db/               # Vector database
├── docs_to_ingest/          # PDFs para indexar
├── logs/                    # Logs de aplicación
└── agent/                   # Archivos del agente
```

## Dependencias Principales

- `langchain>=0.3.28`
- `chromadb>=1.5.5`
- `llama-cpp-python`
- `sentence-transformers`
- `huggingface-hub`

## Uso

```bash
cd /home/iwakura/Documentos/github-projects/local-rag
source .venv/bin/activate
python main.py
```

## Comandos Útiles

- `ingest-dir <path>` - Indexar documentos
- `ask <pregunta>` - Hacer preguntas
- `exit` - Salir

## Variables de Entorno (.env)

- `EMBEDDING_MODEL`: sentence-transformers/all-MiniLM-L6-v2
- `LLAMA_CPP_MODEL_PATH`: ./models/mistral-7b-instruct-v0.3.Q4_K_M.gguf
- `CHROMA_DB_PATH`: ./chroma_db
- `DOCS_PATH`: ./docs_to_ingest
- `N_GPU_LAYERS`: 0 (CPU) o más para GPU
- `N_CTX`: 4096 (contexto del modelo)