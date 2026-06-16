"""
Schemas Pydantic para la API REST del sistema RAG.

Estos schemas definen la estructura de requests y responses de los endpoints FastAPI.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ═══════════════════════════════════════════════════════════════════════════
# REQUEST SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════


class QueryRequest(BaseModel):
    """
    Request para consultar el sistema RAG.

    Attributes:
        question: La pregunta del usuario
        top_k: Número de documentos a recuperar (default: 4)
        max_tokens: Máximo de tokens en la respuesta (default: 512)
        stream: Si True, retorna respuesta en streaming (default: False)
        # provider: Proveedor cloud
        # (openai, anthropic, google, groq, minimax, deepseek). None = local
        api_key: API key para provider cloud (None = usa variable de entorno)
        model: Modelo específico del provider (None = usa default)

    Example:
        {
            "question": "¿Qué es el cálculo diferencial?",
            "top_k": 4,
            "max_tokens": 512,
            "stream": false,
            "provider": "openai",
            "api_key": "sk-...",
            "model": "gpt-4o-mini"
        }
    """

    question: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="La pregunta del usuario",
        examples=["¿Qué es el cálculo diferencial?"],
    )
    top_k: int = Field(
        default=4, ge=1, le=20, description="Número de documentos a recuperar", examples=[4]
    )
    max_tokens: int = Field(
        default=512, ge=1, le=4096, description="Máximo de tokens en la respuesta", examples=[512]
    )
    stream: bool = Field(
        default=False, description="Si True, retorna respuesta en streaming", examples=[False]
    )
    provider: str | None = Field(
        default=None,
        description=(
            "Proveedor cloud (openai, anthropic, google, groq, minimax, deepseek). None = local"
        ),
        examples=[None, "openai", "minimax"],
    )
    api_key: str | None = Field(
        default=None,
        description="API key para provider cloud. None = usa variable de entorno",
        examples=[None],
    )
    model: str | None = Field(
        default=None,
        description="Modelo específico del provider. None = usa default",
        examples=[None, "gpt-4o-mini", "MiniMax-M2.7-8k"],
    )

    @field_validator("question")
    @classmethod
    def validate_question_not_empty(cls, v: str) -> str:
        """Valida que la pregunta no esté vacía."""
        if not v.strip():
            raise ValueError("La pregunta no puede estar vacía")
        return v.strip()


class IngestFileRequest(BaseModel):
    """
    Request para ingerir un archivo individual.

    Attributes:
        file_path: Ruta absoluta o relativa al archivo
        force: Si True, re-ingesta incluso si ya existe (default: False)

    Example:
        {
            "file_path": "./docs_to_ingest/matematicas.pdf",
            "force": false
        }
    """

    file_path: str = Field(
        ...,
        min_length=1,
        description="Ruta al archivo a ingerir",
        examples=["./docs_to_ingest/matematicas.pdf"],
    )
    force: bool = Field(
        default=False, description="Si True, re-ingesta incluso si ya existe", examples=[False]
    )


class IngestDirectoryRequest(BaseModel):
    """
    Request para ingerir un directorio completo.

    Attributes:
        dir_path: Ruta absoluta o relativa al directorio
        recursive: Si True, busca recursivamente en subdirectorios (default: True)
        force: Si True, re-ingesta incluso si ya existe (default: False)

    Example:
        {
            "dir_path": "./docs_to_ingest",
            "recursive": true,
            "force": false
        }
    """

    dir_path: str = Field(
        ...,
        min_length=1,
        description="Ruta al directorio a ingerir",
        examples=["./docs_to_ingest"],
    )
    recursive: bool = Field(
        default=True, description="Búsqueda recursiva en subdirectorios", examples=[True]
    )
    force: bool = Field(
        default=False, description="Si True, re-ingesta incluso si ya existe", examples=[False]
    )


class DeleteDocumentRequest(BaseModel):
    """
    Request para eliminar un documento del índice.

    Attributes:
        document_id: ID del documento a eliminar

    Example:
        {
            "document_id": "chunk_001"
        }
    """

    document_id: str = Field(
        ..., min_length=1, description="ID del documento a eliminar", examples=["chunk_001"]
    )


# ═══════════════════════════════════════════════════════════════════════════
# RESPONSE SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════


class SourceDocument(BaseModel):
    """
    Documento fuente utilizado en una respuesta.

    Attributes:
        content: Contenido del documento
        metadata: Metadatos del documento (fuente, página, etc.)
        id: ID único del documento
        score: Score de similitud (si está disponible)

    Example:
        {
            "content": "El cálculo diferencial estudia las tasas de cambio...",
            "metadata": {"source": "matematicas.pdf", "page": 1},
            "id": "chunk_001",
            "score": 0.85
        }
    """

    model_config = ConfigDict(from_attributes=True)

    content: str = Field(..., description="Contenido del documento")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadatos")
    id: str | None = Field(default=None, description="ID único")
    score: float | None = Field(default=None, description="Score de similitud")


class QueryResponse(BaseModel):
    """
    Response de una consulta RAG exitosa.

    Attributes:
        answer: La respuesta generada por el LLM
        sources: Lista de documentos fuente utilizados
        question: La pregunta original (eco)
        timestamp: Fecha y hora de la consulta
        latency_ms: Latencia de la consulta en milisegundos
        model: Nombre del modelo utilizado

    Example:
        {
            "answer": "El cálculo diferencial estudia las tasas de cambio instantáneo...",
            "sources": [
                {
                    "content": "El cálculo diferencial estudia...",
                    "metadata": {"source": "matematicas.pdf"},
                    "id": "chunk_001"
                }
            ],
            "question": "¿Qué es el cálculo diferencial?",
            "timestamp": "2026-03-25T10:30:45.123456",
            "latency_ms": 2345.67,
            "model": "mistral-7b-instruct-v0.3.Q4_K_M.gguf"
        }
    """

    answer: str = Field(..., description="La respuesta generada por el LLM")
    sources: list[SourceDocument] = Field(default_factory=list, description="Documentos fuente")
    question: str = Field(..., description="La pregunta original")
    timestamp: datetime = Field(default_factory=datetime.now, description="Fecha y hora")
    latency_ms: float = Field(default=0.0, description="Latencia en milisegundos")
    model: str = Field(default="unknown", description="Nombre del modelo")


class QueryError(BaseModel):
    """
    Response de error en consulta.

    Attributes:
        error: Tipo de error
        message: Mensaje descriptivo
        detail: Detalles adicionales (opcional)

    Example:
        {
            "error": "QueryError",
            "message": "No se encontraron documentos relevantes",
            "detail": "La consulta no retornó resultados con score > 0.5"
        }
    """

    error: str = Field(..., description="Tipo de error")
    message: str = Field(..., description="Mensaje descriptivo")
    detail: str | None = Field(default=None, description="Detalles adicionales")


class IngestResponse(BaseModel):
    """
    Response de ingestión exitosa.

    Attributes:
        status: Estado de la operación ("success")
        message: Mensaje descriptivo
        file_path: Ruta del archivo ingerido
        chunks_count: Número de fragmentos generados
        timestamp: Fecha y hora de la ingestión

    Example:
        {
            "status": "success",
            "message": "Documento ingerido correctamente",
            "file_path": "./docs_to_ingest/matematicas.pdf",
            "chunks_count": 125,
            "timestamp": "2026-03-25T10:30:45.123456"
        }
    """

    status: str = Field(..., description="Estado de la operación")
    message: str = Field(..., description="Mensaje descriptivo")
    file_path: str | None = Field(default=None, description="Ruta del archivo")
    dir_path: str | None = Field(default=None, description="Ruta del directorio")
    chunks_count: int = Field(default=0, description="Número de fragmentos")
    timestamp: datetime = Field(default_factory=datetime.now, description="Fecha y hora")


class HealthResponse(BaseModel):
    """
    Response de health check.

    Attributes:
        status: Estado del sistema ("healthy", "degraded", "unhealthy")
        version: Versión de la aplicación
        model: Modelo LLM cargado
        documents_count: Número de documentos en el índice
        timestamp: Fecha y hora del check

    Example:
        {
            "status": "healthy",
            "version": "1.0.0",
            "model": "mistral-7b-instruct-v0.3.Q4_K_M.gguf",
            "documents_count": 4843,
            "timestamp": "2026-03-25T10:30:45.123456"
        }
    """

    status: str = Field(..., description="Estado del sistema")
    version: str = Field(default="1.0.0", description="Versión de la aplicación")
    model: str = Field(default="unknown", description="Modelo LLM cargado")
    embedding_model: str = Field(default="unknown", description="Modelo de embeddings")
    documents_count: int = Field(default=0, description="Documentos en el índice")
    chromadb_status: str = Field(default="unknown", description="Estado de ChromaDB (healthy/unhealthy)")
    redis_status: str = Field(default="unknown", description="Estado de Redis (healthy/unhealthy/none)")
    timestamp: datetime = Field(default_factory=datetime.now, description="Fecha y hora")


class MetricsResponse(BaseModel):
    """
    Response con métricas del sistema.

    Attributes:
        total_queries: Total de consultas realizadas
        total_documents: Total de documentos indexados
        avg_latency_ms: Latencia promedio en ms
        cache_hit_rate: Porcentaje de hits en caché (si aplica)
        uptime_seconds: Tiempo de actividad en segundos

    Example:
        {
            "total_queries": 150,
            "total_documents": 4843,
            "avg_latency_ms": 2345.67,
            "cache_hit_rate": 0.0,
            "uptime_seconds": 3600
        }
    """

    total_queries: int = Field(default=0, description="Total de consultas")
    total_documents: int = Field(default=0, description="Documentos indexados")
    avg_latency_ms: float = Field(default=0.0, description="Latencia promedio")
    cache_hit_rate: float = Field(default=0.0, description="Cache hit rate")
    uptime_seconds: float = Field(default=0.0, description="Tiempo de actividad")


class DeleteResponse(BaseModel):
    """
    Response de eliminación de documento.

    Attributes:
        status: Estado de la operación
        message: Mensaje descriptivo
        document_id: ID del documento eliminado

    Example:
        {
            "status": "success",
            "message": "Documento eliminado correctamente",
            "document_id": "chunk_001"
        }
    """

    status: str = Field(..., description="Estado de la operación")
    message: str = Field(..., description="Mensaje descriptivo")
    document_id: str = Field(..., description="ID del documento eliminado")


class ListDocumentsResponse(BaseModel):
    """
    Response de listado de documentos.

    Attributes:
        total: Número total de documentos
        documents: Lista de documentos (IDs y metadata básica)
        limit: Límite aplicado
        offset: Offset aplicado

    Example:
        {
            "total": 4843,
            "documents": [
                {"id": "chunk_001", "source": "matematicas.pdf", "page": 1},
                {"id": "chunk_002", "source": "matematicas.pdf", "page": 2}
            ],
            "limit": 20,
            "offset": 0
        }
    """

    total: int = Field(..., description="Total de documentos")
    documents: list[dict[str, Any]] = Field(
        default_factory=list, description="Lista de documentos"
    )
    limit: int = Field(default=20, description="Límite aplicado")
    offset: int = Field(default=0, description="Offset aplicado")
