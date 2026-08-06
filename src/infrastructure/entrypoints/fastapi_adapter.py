"""
FastAPI Adapter - API REST para el sistema RAG.

Proporciona endpoints HTTP para:
- Consultas RAG (con soporte streaming)
- Ingestión de documentos (archivo/directorio)
- Health checks y métricas
- Gestión del índice vectorial

Uso:
    from fastapi import FastAPI
    from src.infrastructure.entrypoints.fastapi_adapter import create_router

    app = FastAPI()
    app.include_router(create_router(rag_service), prefix="/api/v1")
"""

import logging
import os
import threading
import time
from collections.abc import AsyncGenerator
from datetime import datetime
from pathlib import Path

import chromadb
import redis as redis_lib
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from src.application.services.rag_service import RAGService
from src.infrastructure.adapters.cloud_llm_adapter import PROVIDER_CONFIG
from src.infrastructure.security.auth import require_admin
from src.infrastructure.entrypoints.api_schemas import (
    APIException,
    DeleteDocumentRequest,
    DeleteResponse,
    HealthResponse,
    IngestDirectoryRequest,
    IngestFileRequest,
    IngestResponse,
    ListDocumentsResponse,
    MetricsResponse,
    QueryRequest,
    QueryResponse,
    SourceDocument,
)

logger = logging.getLogger(__name__)

START_TIME = datetime.now()
QUERY_COUNT = 0
TOTAL_LATENCY_MS = 0.0
_metrics_lock = threading.Lock()

# Caché semántico (lazy init)
_semantic_cache: "SemanticCache | None" = None


def _get_cache() -> "SemanticCache":
    """Get or create the semantic cache instance."""
    global _semantic_cache
    if _semantic_cache is None:
        from src.infrastructure.cache.semantic_cache import SemanticCache

        ttl = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
        max_size = int(os.getenv("CACHE_MAX_SIZE", "1000"))
        _semantic_cache = SemanticCache(ttl_seconds=ttl, max_size=max_size)
        logger.info(f"SemanticCache initialized: ttl={ttl}s, max_size={max_size}")
    return _semantic_cache


def create_router(rag_service: RAGService, auth_dependency=None) -> APIRouter:
    """
    Crea el router FastAPI con todos los endpoints.

    Args:
        rag_service: Instancia del servicio RAG
        auth_dependency: Dependency for authentication (e.g., get_current_user).
                         If None, no auth is applied.

    Returns:
        Router FastAPI configurado
    """
    deps = [Depends(auth_dependency)] if auth_dependency else []
    router = APIRouter(dependencies=deps)

    # ═══════════════════════════════════════════════════════════════════════════
    # HEALTH & METRICS
    # ═══════════════════════════════════════════════════════════════════════════

    @router.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health_check():
        """
        Verifica el estado del sistema.

        Retorna:
            HealthResponse con estado del sistema, modelo cargado y conteo de documentos

        Example:
            GET /api/v1/health

            Response:
            {
                "status": "healthy",
                "version": "1.0.0",
                "model": "mistral-7b-instruct-v0.3.Q4_K_M.gguf",
                "documents_count": 4843,
                "chromadb_status": "healthy",
                "redis_status": "healthy"
            }
        """
        try:
            model_info = (
                rag_service.chain.llm.model_path
                if hasattr(rag_service.chain, "llm")
                and hasattr(rag_service.chain.llm, "model_path")
                else "unknown"
            )
            embedding_model = "sentence-transformers/all-MiniLM-L6-v2"

            chromadb_status = "unknown"
            doc_count = 0
            try:
                chroma_client = chromadb.PersistentClient(
                    path=rag_service.doc_store.persist_directory,
                    settings=chromadb.config.Settings(anonymized_telemetry=False),
                )
                chroma_client.peek(limit=1)
                chromadb_status = "healthy"
                doc_count = rag_service.get_document_count()
            except Exception as e:
                chromadb_status = f"unhealthy: {e}"

            redis_status = "none"
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            if redis_url:
                try:
                    r = redis_lib.from_url(redis_url)
                    r.ping()
                    redis_status = "healthy"
                except Exception as e:
                    redis_status = f"unhealthy: {e}"

            overall_status = "healthy"
            if "unhealthy" in chromadb_status or "unhealthy" in redis_status:
                overall_status = "degraded"
            if "unhealthy:" in chromadb_status and "unhealthy:" in redis_status:
                overall_status = "unhealthy"

            response = HealthResponse(
                status=overall_status,
                version="1.0.0",
                model=os.path.basename(model_info) if model_info else "unknown",
                embedding_model=embedding_model,
                documents_count=doc_count,
                chromadb_status=chromadb_status,
                redis_status=redis_status,
            )
            if overall_status == "unhealthy":
                return JSONResponse(
                    status_code=503,
                    content=response.model_dump(),
                )
            return response
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return JSONResponse(
                status_code=503,
                content=HealthResponse(
                    status="unhealthy",
                    version="1.0.0",
                    model="unknown",
                    documents_count=0,
                    chromadb_status="unknown",
                    redis_status="unknown",
                ).model_dump(),
            )

    @router.get("/metrics", response_model=MetricsResponse, tags=["Health"])
    async def get_metrics():
        """
        Obtiene métricas del sistema.

        Retorna:
            MetricsResponse con estadísticas de uso

        Example:
            GET /api/v1/metrics
        """
        global QUERY_COUNT, TOTAL_LATENCY_MS

        with _metrics_lock:
            current_count = QUERY_COUNT
            current_latency = TOTAL_LATENCY_MS

        avg_latency = current_latency / current_count if current_count > 0 else 0.0
        uptime = (datetime.now() - START_TIME).total_seconds()

        try:
            doc_count = rag_service.get_document_count()
        except Exception:
            doc_count = 0

        cache = _get_cache()
        cache_stats = cache.get_stats()

        return MetricsResponse(
            total_queries=current_count,
            total_documents=doc_count,
            avg_latency_ms=round(avg_latency, 2),
            cache_hit_rate=cache_stats.get("hit_rate", 0.0),
            uptime_seconds=round(uptime, 2),
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # QUERY ENDPOINTS
    # ═══════════════════════════════════════════════════════════════════════════

    @router.post("/query", response_model=QueryResponse, tags=["Query"])
    async def query(request: QueryRequest):
        """
        Ejecuta una consulta RAG.

        Args:
            request: QueryRequest con la pregunta y parámetros

        Returns:
            QueryResponse con la respuesta y fuentes

        Raises:
            HTTPException: Si la consulta falla

        Example:
            POST /api/v1/query
            {
                "question": "¿Qué es el cálculo diferencial?",
                "top_k": 4,
                "max_tokens": 512
            }
        """
        global QUERY_COUNT, TOTAL_LATENCY_MS

        start_time = time.time()
        logger.info(f"Query received: {request.question[:100]}...")

        cache = _get_cache()
        cached_result = cache.get(request.question)

        try:
            if cached_result:
                logger.info(f"Cache hit for query: {request.question[:50]}...")
                latency_ms = (time.time() - start_time) * 1000
                with _metrics_lock:
                    QUERY_COUNT += 1
                    TOTAL_LATENCY_MS += latency_ms

                sources = []
                for doc in cached_result.get("source_documents", []):
                    if hasattr(doc, "page_content"):
                        sources.append(SourceDocument(
                            content=doc.page_content,
                            metadata=doc.metadata,
                            id=getattr(doc, "id", None),
                        ))
                    elif isinstance(doc, dict):
                        sources.append(SourceDocument(
                            content=doc.get("page_content", ""),
                            metadata=doc.get("metadata", {}),
                            id=doc.get("id"),
                        ))

                return QueryResponse(
                    answer=cached_result.get("answer", ""),
                    sources=sources,
                    question=request.question,
                    latency_ms=round(latency_ms, 2),
                    model="cached",
                )

            if request.top_k and request.top_k != rag_service.top_k:
                rag_service.update_top_k(request.top_k)

            result = await rag_service.ask(
                question=request.question,
                provider=request.provider,
                model=request.model,
                api_key=request.api_key,
                max_tokens=request.max_tokens,
            )

            cache.set(request.question, result)

            latency_ms = (time.time() - start_time) * 1000
            with _metrics_lock:
                QUERY_COUNT += 1
                TOTAL_LATENCY_MS += latency_ms

            sources = []
            for doc in result.get("source_documents", []):
                if hasattr(doc, "page_content"):
                    sources.append(
                        SourceDocument(
                            content=doc.page_content,
                            metadata=doc.metadata,
                            id=getattr(doc, "id", None),
                        )
                    )
                elif isinstance(doc, dict):
                    sources.append(
                        SourceDocument(
                            content=doc.get("page_content", ""),
                            metadata=doc.get("metadata", {}),
                            id=doc.get("id"),
                        )
                    )

            model_name = request.provider or "local"
            if request.model:
                model_name = f"{request.provider}/{request.model}"

            logger.info(f"Query completed in {latency_ms:.2f}ms with {len(sources)} sources")

            return QueryResponse(
                answer=result.get("answer", ""),
                sources=sources,
                question=request.question,
                latency_ms=round(latency_ms, 2),
                model=model_name,
            )

        except Exception as e:
            logger.error(f"Query failed: {e}", exc_info=True)
            raise APIException(
                error="query_error",
                message="Error executing query",
                detail=str(e),
            ) from e

    @router.post("/query/stream", tags=["Query"])
    async def query_stream(request: QueryRequest):
        """
        Ejecuta una consulta RAG con streaming de tokens.

        Args:
            request: QueryRequest con la pregunta y parámetros

        Returns:
            StreamingResponse con tokens generados uno por uno

        Example:
            POST /api/v1/query/stream
            {
                "question": "¿Qué es Python?",
                "stream": true
            }
        """
        logger.info(f"Stream query received: {request.question[:100]}...")

        try:
            return StreamingResponse(
                stream_generator(
                    rag_service=rag_service,
                    question=request.question,
                    provider=request.provider,
                    max_tokens=request.max_tokens,
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                },
            )

        except Exception as e:
            logger.error(f"Stream query failed: {e}", exc_info=True)
            raise APIException(
                error="stream_error",
                message="Error in stream query",
                detail=str(e),
            ) from e

    async def _stream_answer(answer: str) -> AsyncGenerator[str, None]:
        """Stream a fully-generated answer token-by-token (fallback for non-streaming LLMs)."""
        import json
        words = answer.split()
        for i, word in enumerate(words):
            if i < len(words) - 1:
                yield f"data: {json.dumps({'token': word + ' '})}\n\n"
            else:
                yield f"data: {json.dumps({'token': word})}\n\n"
        yield "data: [DONE]\n\n"

    async def stream_generator(
        rag_service, question: str, provider: str | None = None, max_tokens: int | None = None
    ) -> AsyncGenerator[str, None]:
        """
        Generador para streaming de tokens via RAGService.ask_stream().

        Real streaming: cada token se emite según lo genera el LLM,
        no espera la respuesta completa.

        Yields:
            Tokens en formato Server-Sent Events (SSE)
        """
        import json

        try:
            for token in rag_service.ask_stream(question, provider=provider, max_tokens=max_tokens):
                yield f"data: {json.dumps({'token': token})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f'data: {json.dumps({"error": "Stream interrupted", "detail": str(e)})}\n\n'

    # ═══════════════════════════════════════════════════════════════════════════
    # INGESTION ENDPOINTS
    # ═══════════════════════════════════════════════════════════════════════════

    @router.post("/ingest/file", response_model=IngestResponse, tags=["Ingestion"])
    async def ingest_file(
        request: IngestFileRequest,
        current_user=Depends(require_admin),
    ):
        """
        Ingiere un archivo individual al índice vectorial.

        Args:
            request: IngestFileRequest con la ruta del archivo

        Returns:
            IngestResponse con el resultado de la ingestión

        Raises:
            HTTPException: Si el archivo no existe o falla la ingestión

        Example:
            POST /api/v1/ingest/file
            {
                "file_path": "./docs_to_ingest/matematicas.pdf"
            }
        """
        logger.info(f"Ingest file request: {request.file_path}")

        try:
            request_path = Path(request.file_path).resolve()
            if not request_path.is_file():
                raise HTTPException(
                    status_code=404, detail="Archivo no encontrado"
                )

            # Ejecutar ingestión
            chunks_count = rag_service.ingest_document(str(request_path))

            logger.info(f"File ingested successfully: {request.file_path}")

            return IngestResponse(
                status="success",
                message="Documento ingerido correctamente",
                file_path=str(request_path),
                chunks_count=chunks_count,
            )

        except HTTPException:
            raise
        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            raise APIException(
                error="not_found",
                message="File not found",
                detail=str(e),
                status_code=404,
            ) from e
        except Exception as e:
            logger.error(f"Ingest file failed: {e}", exc_info=True)
            raise APIException(
                error="ingest_error",
                message="Error ingesting file",
                detail=str(e),
            ) from e

    @router.post("/ingest/directory", response_model=IngestResponse, tags=["Ingestion"])
    async def ingest_directory(
        request: IngestDirectoryRequest,
        current_user=Depends(require_admin),
    ):
        """
        Ingiere todos los documentos de un directorio.

        Args:
            request: IngestDirectoryRequest con la ruta del directorio

        Returns:
            IngestResponse con el resultado de la ingestión

        Raises:
            HTTPException: Si el directorio no existe o falla la ingestión

        Example:
            POST /api/v1/ingest/directory
            {
                "dir_path": "./docs_to_ingest",
                "recursive": true
            }
        """
        logger.info(f"Ingest directory request: {request.dir_path}")

        try:
            request_path = Path(request.dir_path).resolve()
            if not request_path.is_dir():
                raise HTTPException(
                    status_code=404, detail="Directorio no encontrado"
                )

            # Ejecutar ingestión
            chunks_count = rag_service.ingest_directory(str(request_path))

            logger.info(f"Directory ingested successfully: {request.dir_path}")

            return IngestResponse(
                status="success",
                message="Directorio ingerido correctamente",
                dir_path=request.dir_path,
                chunks_count=chunks_count,
            )

        except HTTPException:
            raise
        except FileNotFoundError as e:
            logger.error(f"Directory not found: {e}")
            raise APIException(
                error="not_found",
                message="Directory not found",
                detail=str(e),
                status_code=404,
            ) from e
        except Exception as e:
            logger.error(f"Ingest directory failed: {e}", exc_info=True)
            raise APIException(
                error="ingest_error",
                message="Error ingesting directory",
                detail=str(e),
            ) from e

    # ═══════════════════════════════════════════════════════════════════════════
    # DOCUMENT MANAGEMENT ENDPOINTS
    # ═══════════════════════════════════════════════════════════════════════════

    @router.get("/documents", response_model=ListDocumentsResponse, tags=["Documents"])
    async def list_documents(
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
    ):
        """
        Lista documentos indexados.

        Args:
            limit: Máximo de documentos a retornar
            offset: Offset para paginación

        Returns:
            ListDocumentsResponse con lista de documentos

        Example:
            GET /api/v1/documents?limit=20&offset=0
        """
        try:
            result = rag_service.list_documents(limit=limit, offset=offset)
            docs = []
            for doc in result["documents"]:
                docs.append(SourceDocument(
                    id=doc["id"],
                    content="",
                    metadata=doc.get("metadata", {}),
                ))
            return ListDocumentsResponse(
                total=result["total"],
                documents=docs,
                limit=limit,
                offset=offset,
            )
        except Exception as e:
            logger.error(f"List documents failed: {e}")
            raise APIException(
                error="list_error",
                message="Error listing documents",
                detail=str(e),
            ) from e

    @router.delete("/documents/{document_id}", response_model=DeleteResponse, tags=["Documents"])
    async def delete_document(
        document_id: str,
        current_user=Depends(require_admin),
    ):
        """
        Elimina un documento del índice.

        Args:
            document_id: ID del documento a eliminar (path param)

        Returns:
            DeleteResponse con el resultado

        Raises:
            HTTPException: Si falla la eliminación (404 si no existe)

        Example:
            DELETE /api/v1/documents/chunk_001
        """
        try:
            deleted = rag_service.delete_document(document_id)
            if not deleted:
                raise HTTPException(
                    status_code=404,
                    detail=f"Documento no encontrado: {document_id}",
                )
            return DeleteResponse(
                status="success",
                message="Documento eliminado correctamente",
                document_id=document_id,
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Delete document failed: {e}")
            raise APIException(
                error="delete_error",
                message="Error deleting document",
                detail=str(e),
            ) from e

    @router.get("/llm/providers", tags=["LLM"])
    async def get_llm_providers():
        """
        Lista providers de LLM disponibles (cloud + local).

        Returns:
            Lista de providers con sus modelos y configuración

        Example:
            GET /api/v1/llm/providers

            Response:
            {
                "providers": [
                    {
                        "id": "openai",
                        "models": ["gpt-4o", "gpt-4o-mini"],
                        "default": "gpt-4o-mini",
                    },
                    {
                        "id": "anthropic",
                        "models": ["claude-opus-4", "claude-sonnet-4"],
                        "default": "claude-sonnet-4",
                    },
                    ...
                ],
                "local": {
                    "name": "llama.cpp",
                    "model": "mistral-7b-instruct-v0.3.Q4_K_M.gguf"
                }
        """
        providers = []
        for provider_id, config in PROVIDER_CONFIG.items():
            providers.append(
                {
                    "id": provider_id,
                    "models": config["models"],
                    "default_model": config["default_model"],
                    "supports_streaming": config["supports_streaming"],
                }
            )

        local_info = {"name": "llama.cpp"}
        try:
            chain_llm = getattr(rag_service.chain, "llm", None)
            if chain_llm and hasattr(chain_llm, "model_path"):
                local_info["model"] = os.path.basename(chain_llm.model_path)
        except Exception:
            pass

        return {"providers": providers, "local": local_info}

    @router.get("/llm/models/{provider}", tags=["LLM"])
    async def get_provider_models(provider: str):
        """
        Lista modelos disponibles para un provider cloud.

        Args:
            provider: Nombre del provider (openai, anthropic, google, groq, minimax, deepseek)

        Returns:
            Lista de modelos y modelo default

        Example:
            GET /api/v1/llm/models/openai

            Response:
            {
                "provider": "openai",
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
                "default": "gpt-4o-mini"
            }
        """
        provider = provider.lower()
        if provider not in PROVIDER_CONFIG:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Provider '{provider}' no encontrado. "
                    f"Providers: {list(PROVIDER_CONFIG.keys())}"
                ),
            )

        config = PROVIDER_CONFIG[provider]
        return {
            "provider": provider,
            "models": config["models"],
            "default": config["default_model"],
        }

    return router


def create_app(rag_service: RAGService, enable_auth: bool = True) -> "FastAPI":
    """
    Crea la aplicación FastAPI completa con middleware y routers.

    Args:
        rag_service: Instancia del servicio RAG
        enable_auth: Si True, habilita autenticación JWT y rate limiting

    Returns:
        Aplicación FastAPI configurada
    """
    from fastapi import FastAPI

    app = FastAPI(
        title="RAG API Local",
        description="API REST para sistema RAG local con llama.cpp",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Habilitar seguridad
    if enable_auth:
        # Agregar middleware de rate limiting
        from src.infrastructure.security.rate_limiter import RateLimitMiddleware

        app.add_middleware(
            RateLimitMiddleware,
            requests_per_minute=60,
            requests_per_hour=1000,
            burst_limit=10,
            whitelist=["127.0.0.1"],  # localhost sin rate limit
        )

        # Incluir router de autenticación
        from src.infrastructure.security.auth import auth_router, get_current_user

        app.include_router(auth_router, prefix="/api/v1", tags=["Auth"])

        logger.info("Seguridad habilitada: JWT + Rate Limiting")

    # Agregar CORS middleware
    # CORS_ALLOWED_ORIGINS: comma-separated list of allowed origins, or "*" for all (dev only)
    # Empty (default) means no CORS - most secure for production
    cors_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "").strip()
    if cors_origins_env == "*":
        cors_origins = ["*"]
        allow_credentials = False
        logger.warning("CORS: allowing all origins (*) without credentials - development mode only")
    elif cors_origins_env:
        cors_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
        allow_credentials = True
    else:
        cors_origins = []
        allow_credentials = False

    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=allow_credentials,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Incluir router
    auth_dep = get_current_user if enable_auth else None
    router = create_router(rag_service, auth_dependency=auth_dep)
    app.include_router(router, prefix="/api/v1")

    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """Redirecciona a la documentación de la API."""
        return {
            "message": "RAG API Local",
            "docs": "/docs",
            "health": "/api/v1/health",
            "auth": "/api/v1/token",  # Nuevo endpoint de auth
        }

    return app
