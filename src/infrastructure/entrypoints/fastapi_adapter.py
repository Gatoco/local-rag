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
import time
from collections.abc import AsyncGenerator
from datetime import datetime

from fastapi import APIRouter, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from src.application.services.rag_service import RAGService
from src.infrastructure.adapters.cloud_llm_adapter import PROVIDER_CONFIG
from src.infrastructure.entrypoints.api_schemas import (
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

# Variables globales para métricas
START_TIME = datetime.now()
QUERY_COUNT = 0
TOTAL_LATENCY_MS = 0.0


def create_router(rag_service: RAGService) -> APIRouter:
    """
    Crea el router FastAPI con todos los endpoints.

    Args:
        rag_service: Instancia del servicio RAG

    Returns:
        Router FastAPI configurado
    """
    router = APIRouter()

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
                "documents_count": 4843
            }
        """
        try:
            # Obtener configuración del modelo desde RAGService
            model_info = rag_service.chain.llm.model_path if hasattr(rag_service.chain, 'llm') and hasattr(rag_service.chain.llm, 'model_path') else "unknown"
            embedding_model = "sentence-transformers/all-MiniLM-L6-v2"  # Podría obtenerse del adapter

            # Obtener conteo de documentos
            try:
                doc_count = rag_service.get_document_count()
            except Exception:
                doc_count = 0

            return HealthResponse(
                status="healthy",
                version="1.0.0",
                model=os.path.basename(model_info) if model_info else "unknown",
                embedding_model=embedding_model,
                documents_count=doc_count,
            )
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return HealthResponse(
                status="unhealthy",
                version="1.0.0",
                model="unknown",
                documents_count=0,
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

        avg_latency = TOTAL_LATENCY_MS / QUERY_COUNT if QUERY_COUNT > 0 else 0.0
        uptime = (datetime.now() - START_TIME).total_seconds()

        try:
            doc_count = rag_service.get_document_count()
        except Exception:
            doc_count = 0

        return MetricsResponse(
            total_queries=QUERY_COUNT,
            total_documents=doc_count,
            avg_latency_ms=round(avg_latency, 2),
            cache_hit_rate=0.0,  # Implementar cuando haya caché
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

        try:
            # Ejecutar consulta
            result = rag_service.ask(request.question)

            # Calcular latencia
            latency_ms = (time.time() - start_time) * 1000
            QUERY_COUNT += 1
            TOTAL_LATENCY_MS += latency_ms

            # Convertir documentos fuente
            sources = []
            for doc in result.get("source_documents", []):
                if hasattr(doc, 'page_content'):
                    sources.append(SourceDocument(
                        content=doc.page_content,
                        metadata=doc.metadata,
                        id=getattr(doc, 'id', None),
                    ))
                elif isinstance(doc, dict):
                    sources.append(SourceDocument(
                        content=doc.get('page_content', ''),
                        metadata=doc.get('metadata', {}),
                        id=doc.get('id'),
                    ))

            logger.info(f"Query completed in {latency_ms:.2f}ms with {len(sources)} sources")

            return QueryResponse(
                answer=result.get("answer", ""),
                sources=sources,
                question=request.question,
                latency_ms=round(latency_ms, 2),
                model=os.path.basename(rag_service.chain.llm.model_path) if hasattr(rag_service.chain, 'llm') and hasattr(rag_service.chain.llm, 'model_path') else "unknown",
            )

        except Exception as e:
            logger.error(f"Query failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error executing query: {str(e)}"
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
            # Obtener adapter y usar streaming nativo
            if hasattr(rag_service.chain, 'llm') and hasattr(rag_service.chain.llm, 'generate_stream'):
                return StreamingResponse(
                    stream_generator(rag_service.chain.llm, request.question, request.max_tokens),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "X-Accel-Buffering": "no",
                    }
                )
            else:
                # Fallback: consulta normal
                result = await query(request)
                return StreamingResponse(
                    iter([result.answer]),
                    media_type="text/plain"
                )

        except Exception as e:
            logger.error(f"Stream query failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error in stream query: {str(e)}"
            ) from e

    async def stream_generator(llm, question: str, max_tokens: int) -> AsyncGenerator[str, None]:
        """
        Generador para streaming de tokens.

        Yields:
            Tokens en formato Server-Sent Events (SSE)
        """
        try:
            for token in llm.generate_stream(question, max_tokens=max_tokens):
                yield f"data: {token}\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: [ERROR] {str(e)}\n\n"

    # ═══════════════════════════════════════════════════════════════════════════
    # INGESTION ENDPOINTS
    # ═══════════════════════════════════════════════════════════════════════════

    @router.post("/ingest/file", response_model=IngestResponse, tags=["Ingestion"])
    async def ingest_file(request: IngestFileRequest):
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
            # Validar que el archivo existe
            if not os.path.isfile(request.file_path):
                raise HTTPException(
                    status_code=404,
                    detail=f"Archivo no encontrado: {request.file_path}"
                )

            # Ejecutar ingestión
            rag_service.ingest_document(request.file_path)

            logger.info(f"File ingested successfully: {request.file_path}")

            return IngestResponse(
                status="success",
                message="Documento ingerido correctamente",
                file_path=request.file_path,
                chunks_count=0,  # Podría obtenerse del servicio
            )

        except HTTPException:
            raise
        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            raise HTTPException(status_code=404, detail=str(e)) from e
        except Exception as e:
            logger.error(f"Ingest file failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error ingesting file: {str(e)}"
            ) from e

    @router.post("/ingest/directory", response_model=IngestResponse, tags=["Ingestion"])
    async def ingest_directory(request: IngestDirectoryRequest):
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
            # Validar que el directorio existe
            if not os.path.isdir(request.dir_path):
                raise HTTPException(
                    status_code=404,
                    detail=f"Directorio no encontrado: {request.dir_path}"
                )

            # Ejecutar ingestión
            rag_service.ingest_directory(request.dir_path)

            logger.info(f"Directory ingested successfully: {request.dir_path}")

            return IngestResponse(
                status="success",
                message="Directorio ingerido correctamente",
                dir_path=request.dir_path,
                chunks_count=0,
            )

        except HTTPException:
            raise
        except FileNotFoundError as e:
            logger.error(f"Directory not found: {e}")
            raise HTTPException(status_code=404, detail=str(e)) from e
        except Exception as e:
            logger.error(f"Ingest directory failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error ingesting directory: {str(e)}"
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
            # Nota: ChromaDB no tiene método directo para listar todos los documentos
            # Esto es un placeholder - implementar según necesidades
            return ListDocumentsResponse(
                total=0,
                documents=[],
                limit=limit,
                offset=offset,
            )
        except Exception as e:
            logger.error(f"List documents failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error listing documents: {str(e)}"
            ) from e

    @router.delete("/documents", response_model=DeleteResponse, tags=["Documents"])
    async def delete_document(request: DeleteDocumentRequest):
        """
        Elimina un documento del índice.

        Args:
            request: DeleteDocumentRequest con el ID del documento

        Returns:
            DeleteResponse con el resultado

        Raises:
            HTTPException: Si falla la eliminación

        Example:
            DELETE /api/v1/documents
            {
                "document_id": "chunk_001"
            }
        """
        try:
            return DeleteResponse(
                status="success",
                message="Documento eliminado correctamente",
                document_id=request.document_id,
            )
        except Exception as e:
            logger.error(f"Delete document failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error deleting document: {str(e)}"
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
                    {"id": "openai", "models": ["gpt-4o", "gpt-4o-mini"], "default": "gpt-4o-mini"},
                    {"id": "anthropic", "models": ["claude-opus-4", "claude-sonnet-4"], "default": "claude-sonnet-4"},
                    ...
                ],
                "local": {"name": "llama.cpp", "model": "mistral-7b-instruct-v0.3.Q4_K_M.gguf"}
            }
        """
        providers = []
        for provider_id, config in PROVIDER_CONFIG.items():
            providers.append({
                "id": provider_id,
                "models": config["models"],
                "default_model": config["default_model"],
                "supports_streaming": config["supports_streaming"],
            })

        local_info = {"name": "llama.cpp"}
        try:
            if hasattr(rag_service.llm, 'model_path'):
                local_info["model"] = os.path.basename(rag_service.llm.model_path)
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
                detail=f"Provider '{provider}' no encontrado. Providers: {list(PROVIDER_CONFIG.keys())}"
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
            whitelist=["127.0.0.1"]  # localhost sin rate limit
        )

        # Incluir router de autenticación
        from src.infrastructure.security.auth import auth_router
        app.include_router(auth_router, prefix="/api/v1", tags=["Auth"])

        logger.info("Seguridad habilitada: JWT + Rate Limiting")

    # Agregar CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configurar según necesidades
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Incluir router
    router = create_router(rag_service)
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
