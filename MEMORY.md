# MEMORY.md - Long-term Memory

This file serves as the curated long-term memory for the Navi-LocalRAG agent.

## Project Identity

**Name**: Navi (ナビゲ)
**Role**: AI spirit guide for Local RAG project
**Personality**: Meticulous, communicative, orderly, cautious
**Language**: Bilingual (Japanese 🇯🇵 / English 🇺🇸)

## Project Overview

Local RAG is a local-first Retrieval-Augmented Generation system that allows natural language queries over personal documents using local or cloud LLMs.

### Tech Stack

- **Architecture**: Hexagonal (Ports & Adapters)
- **Python**: 3.12+
- **Vector DB**: ChromaDB
- **LLM**: llama.cpp (local), Multi-provider cloud (OpenAI, Anthropic, etc.)
- **Embeddings**: BAAI/bge-large-en-v1.5 (1024 dims)
- **Framework**: LangChain 0.3.x
- **API**: FastAPI
- **UI**: Streamlit, Electron (optional), REPL

### Key Paths

```
PROJECT_ROOT: /home/iwakura/Documentos/github-projects/local-rag
SRC: /home/iwakura/Documentos/github-projects/local-rag/src
TESTS: /home/iwakura/Documentos/github-projects/local-rag/tests
CHROMA_DB: /home/iwakura/Documentos/github-projects/local-rag/chroma_db
MODELS: /home/iwakura/Documentos/github-projects/local-rag/models
AGENT: /home/iwakura/Documentos/github-projects/local-rag/agent
```

## Architecture Decisions

### Hexagonal Architecture (v1.0.0)

Implemented to achieve:
- Clear separation between domain and infrastructure
- Easy swapping of components (e.g., ChromaDB → other vector DB)
- Testability through port abstractions
- Dependency inversion (infrastructure depends on domain)

### Adapter Strategy

| Adapter | Purpose | Status |
|---------|---------|--------|
| `LlamaCppLLMAdapter` | Local GGUF inference | Primary local |
| `CloudLLMAdapter` | Multi-cloud provider | Primary cloud |
| `LMStudioLLMAdapter` | LM Studio HTTP API | Alternative local |
| `OllamaLLMAdapter` | Ollama HTTP API | Legacy |
| `HFEmbeddingAdapter` | HuggingFace embeddings | Production |
| `ChromaDBAdapter` | Vector storage | Production |
| `LangChainLoaderAdapter` | Document loading | Production |
| `LangChainRAGAdapter` | RAG chain orchestration | Production |

## User Preferences

### Deployment

- Primary: Development machine
- Docker: Used for testing production-like environments
- Cloud providers: MiniMax (primary), Groq (backup for speed)

### Workflow

1. **Agent work**: Uses MCP server for code-aware interactions
2. **Session management**: Tracks pending approvals and urgency
3. **Notifications**: Telegram for critical alerts

## Lessons Learned

### DO

- Run tests before committing (enforced in agent rules)
- Use dependency injection for testability
- Document architecture decisions
- Maintain 80% minimum test coverage

### DON'T

- Hardcode credentials (always use `.env`)
- Use `print()` instead of logger (see STANDARDS.md)
- Skip tests for "simple" changes
- Commit directly to main (always use PRs)

## Pending Technical Debt

| Item | Priority | Notes |
|------|----------|-------|
| REPL should use RAGService | High | Currently duplicates RAG logic |
| LangChainLoaderAdapter violates SRP | High | Does too much (load, parse, OCR, chunk) |
| MCP tools duplicated | High | agent/tools/ vs mcp_server.py |
| LangChainRAGAdapter untested | High | No unit tests |
| SemanticCache is hash-based, not semantic | Medium | Named "semantic" but uses hashing |
| Session stuck from 2026-06-09 | Medium | Needs cleanup |

## Contact & Context

- **Owner**: iwakura
- **Repository**: https://github.com/iwakura/local-rag
- **Primary Language**: Japanese (documentation), English (code comments)

## Update Log

| Date | Change |
|------|--------|
| 2026-06-16 | Initial MEMORY.md creation, project v1.0.0 |
| 2026-06-09 | Session management system added |
| 2026-05-01 | Project inception |
