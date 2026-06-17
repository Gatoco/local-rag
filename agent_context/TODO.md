# TODO - Navi-LocalRAG

## Pendiente (backlog)

- [ ] Implementar `DELETE /documents` y `GET /documents` (placeholders en API)
- [ ] Sistema de cache semántico con Redis (RAGServiceWithCache no se usa)
- [ ] Eliminar `mylocalrag.py` duplicado (existe en raíz y en `src/infrastructure/entrypoints/`)
- [ ] Evaluar si `RAGServiceWithCache` debe usarse o eliminarse
- [ ] Evaluar si `cli_adapter.py` (legacy) debe consolidarse con el REPL
- [ ] Reducir los 159 `print()` en src/ (reemplazar por logger)
- [ ] Auditar CORS en FastAPI (orígenes específicos vs `*`)

## En Progreso

- [ ] Limpiar archivos de agente/contexto (en curso)

## Completados (mantener como historial)

- [x] Crear sistema de prompts
- [x] Crear agent_context/PROJECT.md (2026-06-16)
- [x] Crear agent_context/STANDARDS.md (2026-06-16)
- [x] Configurar MCP server (14 tools: git, tests, CI)
- [x] Configurar session manager con urgencia
- [x] Mantenimiento 2026-06-16:
  - Dockerfile multi-stage build
  - Redis puerto interno (no expuesto al host)
  - requirements.txt pineado con uv export
  - uv.lock trackeado
  - datetime.utcnow() → datetime.now(timezone.utc)
  - sys.path.insert eliminados de 9 archivos
  - langchain_loader_adapter bug fix (.docx/.txt/.md/.xlsx/.pptx/.html)
  - Dependabot + gitleaks workflows
  - 87 tests nuevos (security, rate_limiter, semantic_cache,
    dependency_validator, langchain_loader_adapter)

## Notas Técnicas

- El agente usa venv en `/home/iwakura/Documentos/github-projects/local-rag/.venv/bin/activate`
- Siempre ejecutar tests antes de commit: `pytest tests/ -v`
- Para approval, esperar confirmación del usuario antes de acciones destructivas
- Redis está en red interna — acceder con `docker compose exec redis redis-cli`
- `scripts/index_documents.py` es el indexador robusto (reemplaza `index_docs.py` root)
