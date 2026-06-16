# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-06-16

### Added

- **Hexagonal Architecture**: Complete refactor to Ports & Adapters pattern
  - Domain layer with pure models (`Document`, `Query`, `Answer`)
  - Abstract ports for LLMs, embeddings, document stores
  - Infrastructure adapters for ChromaDB, llama.cpp, HuggingFace, LangChain

- **Multi-Provider LLM Support**:
  - Local: llama.cpp (GGUF), LM Studio, Ollama
  - Cloud: OpenAI, Anthropic, Google, Groq, MiniMax, DeepSeek

- **Modern REPL Interface**:
  - Command pattern implementation
  - Rich UI with status bar, themes
  - Streaming responses
  - Local/cloud mode switching
  - RAG toggle with configurable top_k

- **API Security**:
  - JWT authentication with Argon2 password hashing
  - Redis-backed rate limiting (sliding window)
  - Per-IP and per-user rate limits

- **Semantic Cache**:
  - TTL-based expiration
  - LRU eviction policy
  - Query normalization

- **Comprehensive Test Suite**:
  - 170+ tests covering core functionality
  - Unit, integration, and benchmark tests
  - 80% minimum coverage requirement

- **Docker Deployment**:
  - Multi-stage Dockerfile
  - docker-compose with API, UI, Redis, backup services
  - Health checks and resource management

### Changed

- **Repository URL**: Moved from `Gatoco/local-rag` to `iwakura/local-rag`
- **Python Version**: Now requires Python 3.12+ (was 3.11+)

### Deprecated

- **CLI (main.py)**: Legacy CLI deprecated in favor of REPL
- **OllamaLLMAdapter**: Marked as legacy, use LlamaCppLLMAdapter instead

### Fixed

- Session persistence in REPL
- ChromaDB connection handling
- Token expiration validation
- Rate limit header formatting

## [0.9.0] - 2026-05-01

### Added

- Initial release with basic RAG functionality
- ChromaDB integration for vector storage
- llama.cpp local inference support
- Basic FastAPI REST API
- CLI with ingest/query commands

### Known Issues

- No authentication (deprecated in v1.0)
- Single-user only (deprecated in v1.0)
- No streaming support (added in v1.0)
- Limited test coverage (improved in v1.0)

---

## Versioning Strategy

- **Major version (1.0)**: Breaking changes to API or architecture
- **Minor version (1.1)**: New features, backward compatible
- **Patch version (1.0.1)**: Bug fixes, backward compatible

## Release Process

1. All tests must pass
2. Code coverage maintained above 80%
3. Documentation updated
4. CHANGELOG updated
5. GitHub release created with tags
