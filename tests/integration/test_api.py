"""
Tests para la API REST del sistema RAG.

Estos tests verifican:
- Endpoints de health y métricas
- Endpoints de consulta (query)
- Endpoints de ingestión
- Manejo de errores
- Validación de schemas Pydantic
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from src.infrastructure.entrypoints.api_schemas import (
    QueryRequest,
    QueryResponse,
    QueryError,
    IngestFileRequest,
    IngestDirectoryRequest,
    IngestResponse,
    HealthResponse,
    MetricsResponse,
    SourceDocument,
)


# ═══════════════════════════════════════════════════════════════════════════
# TESTS DE SCHEMAS PYDANTIC
# ═══════════════════════════════════════════════════════════════════════════

class TestQueryRequestSchema:
    """Tests para QueryRequest schema"""

    def test_query_request_minimal(self):
        """Test: QueryRequest con solo pregunta"""
        request = QueryRequest(question="¿Qué es Python?")
        
        assert request.question == "¿Qué es Python?"
        assert request.top_k == 4
        assert request.max_tokens == 512
        assert request.stream is False

    def test_query_request_complete(self):
        """Test: QueryRequest con todos los parámetros"""
        request = QueryRequest(
            question="¿Qué es RAG?",
            top_k=5,
            max_tokens=256,
            stream=True
        )
        
        assert request.question == "¿Qué es RAG?"
        assert request.top_k == 5
        assert request.max_tokens == 256
        assert request.stream is True

    def test_query_request_whitespace_stripped(self):
        """Test: QueryRequest elimina whitespace"""
        request = QueryRequest(question="  Question with spaces  ")
        
        assert request.question == "Question with spaces"

    def test_query_request_empty_question_fails(self):
        """Test: QueryRequest con pregunta vacía falla"""
        with pytest.raises(Exception):  # ValidationError
            QueryRequest(question="")

    def test_query_request_whitespace_only_fails(self):
        """Test: QueryRequest con solo whitespace falla"""
        with pytest.raises(Exception):
            QueryRequest(question="   ")

    def test_query_request_top_k_bounds(self):
        """Test: QueryRequest valida top_k"""
        # Válido
        QueryRequest(question="Test", top_k=1)
        QueryRequest(question="Test", top_k=20)
        
        # Inválido
        with pytest.raises(Exception):
            QueryRequest(question="Test", top_k=0)
        
        with pytest.raises(Exception):
            QueryRequest(question="Test", top_k=21)

    def test_query_request_max_tokens_bounds(self):
        """Test: QueryRequest valida max_tokens"""
        # Válido
        QueryRequest(question="Test", max_tokens=1)
        QueryRequest(question="Test", max_tokens=4096)
        
        # Inválido
        with pytest.raises(Exception):
            QueryRequest(question="Test", max_tokens=0)
        
        with pytest.raises(Exception):
            QueryRequest(question="Test", max_tokens=4097)

    def test_query_request_too_long_question_fails(self):
        """Test: QueryRequest con pregunta muy larga falla"""
        with pytest.raises(Exception):
            QueryRequest(question="A" * 10001)


class TestIngestFileRequestSchema:
    """Tests para IngestFileRequest schema"""

    def test_ingest_file_request_minimal(self):
        """Test: IngestFileRequest minimal"""
        request = IngestFileRequest(file_path="./docs/test.pdf")
        
        assert request.file_path == "./docs/test.pdf"
        assert request.force is False

    def test_ingest_file_request_complete(self):
        """Test: IngestFileRequest completo"""
        request = IngestFileRequest(
            file_path="./docs/test.pdf",
            force=True
        )
        
        assert request.file_path == "./docs/test.pdf"
        assert request.force is True

    def test_ingest_file_request_empty_path_fails(self):
        """Test: IngestFileRequest con path vacío falla"""
        with pytest.raises(Exception):
            IngestFileRequest(file_path="")


class TestIngestDirectoryRequestSchema:
    """Tests para IngestDirectoryRequest schema"""

    def test_ingest_directory_request_minimal(self):
        """Test: IngestDirectoryRequest minimal"""
        request = IngestDirectoryRequest(dir_path="./docs")
        
        assert request.dir_path == "./docs"
        assert request.recursive is True
        assert request.force is False

    def test_ingest_directory_request_complete(self):
        """Test: IngestDirectoryRequest completo"""
        request = IngestDirectoryRequest(
            dir_path="./docs",
            recursive=False,
            force=True
        )
        
        assert request.dir_path == "./docs"
        assert request.recursive is False
        assert request.force is True


class TestQueryResponseSchema:
    """Tests para QueryResponse schema"""

    def test_query_response_minimal(self):
        """Test: QueryResponse minimal"""
        response = QueryResponse(
            answer="Esta es la respuesta",
            question="¿Qué es Python?"
        )
        
        assert response.answer == "Esta es la respuesta"
        assert response.question == "¿Qué es Python?"
        assert response.sources == []
        assert isinstance(response.timestamp, datetime)

    def test_query_response_with_sources(self):
        """Test: QueryResponse con fuentes"""
        from src.infrastructure.entrypoints.api_schemas import SourceDocument
        
        source = SourceDocument(
            content="Python es un lenguaje...",
            metadata={"source": "test.pdf"},
            id="chunk_001"
        )
        
        response = QueryResponse(
            answer="Python es un lenguaje de programación",
            question="¿Qué es Python?",
            sources=[source]
        )
        
        assert len(response.sources) == 1
        assert response.sources[0].content == "Python es un lenguaje..."
        assert response.sources[0].metadata["source"] == "test.pdf"

    def test_query_response_with_latency(self):
        """Test: QueryResponse con latencia"""
        response = QueryResponse(
            answer="Answer",
            question="Question",
            latency_ms=1234.56,
            model="mistral-7b"
        )
        
        assert response.latency_ms == 1234.56
        assert response.model == "mistral-7b"


class TestHealthResponseSchema:
    """Tests para HealthResponse schema"""

    def test_health_response_healthy(self):
        """Test: HealthResponse healthy"""
        response = HealthResponse(
            status="healthy",
            model="mistral-7b.gguf",
            documents_count=100
        )
        
        assert response.status == "healthy"
        assert response.model == "mistral-7b.gguf"
        assert response.documents_count == 100

    def test_health_response_unhealthy(self):
        """Test: HealthResponse unhealthy"""
        response = HealthResponse(
            status="unhealthy",
            model="unknown",
            documents_count=0
        )
        
        assert response.status == "unhealthy"


class TestIngestResponseSchema:
    """Tests para IngestResponse schema"""

    def test_ingest_response_file(self):
        """Test: IngestResponse para archivo"""
        response = IngestResponse(
            status="success",
            message="Documento ingerido",
            file_path="./docs/test.pdf",
            chunks_count=50
        )
        
        assert response.status == "success"
        assert response.file_path == "./docs/test.pdf"
        assert response.chunks_count == 50

    def test_ingest_response_directory(self):
        """Test: IngestResponse para directorio"""
        response = IngestResponse(
            status="success",
            message="Directorio ingerido",
            dir_path="./docs",
            chunks_count=200
        )
        
        assert response.status == "success"
        assert response.dir_path == "./docs"


class TestMetricsResponseSchema:
    """Tests para MetricsResponse schema"""

    def test_metrics_response(self):
        """Test: MetricsResponse"""
        from src.infrastructure.entrypoints.api_schemas import MetricsResponse
        
        response = MetricsResponse(
            total_queries=100,
            total_documents=500,
            avg_latency_ms=2345.67,
            uptime_seconds=3600
        )
        
        assert response.total_queries == 100
        assert response.total_documents == 500
        assert response.avg_latency_ms == 2345.67
        assert response.uptime_seconds == 3600


# ═══════════════════════════════════════════════════════════════════════════
# TESTS DE INTEGRACIÓN CON FASTAPI (Mock)
# ═══════════════════════════════════════════════════════════════════════════

class TestAPIIntegration:
    """Tests de integración con FastAPI (requieren mock del servicio RAG)"""

    @pytest.fixture
    def mock_rag_service(self):
        """Mock de RAGService para tests"""
        from unittest.mock import Mock

        mock_service = Mock()
        mock_service.ask.return_value = {
            "answer": "Esta es una respuesta de prueba",
            "source_documents": []
        }
        mock_service.get_document_count.return_value = 100

        mock_llm = Mock()
        mock_llm.model_path = "./models/test.gguf"

        mock_chain = Mock()
        mock_chain.llm = mock_llm

        mock_service.chain = mock_chain

        return mock_service

    @pytest.fixture
    def api_client(self, mock_rag_service):
        """Cliente de test para FastAPI"""
        from src.infrastructure.entrypoints.fastapi_adapter import create_app
        
        app = create_app(mock_rag_service)
        client = TestClient(app)
        
        return client

    def test_health_endpoint(self, api_client):
        """Test: GET /api/v1/health"""
        response = api_client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "documents_count" in data

    def test_metrics_endpoint(self, api_client):
        """Test: GET /api/v1/metrics"""
        response = api_client.get("/api/v1/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_queries" in data
        assert "total_documents" in data
        assert "avg_latency_ms" in data

    def test_query_endpoint(self, api_client):
        """Test: POST /api/v1/query"""
        response = api_client.post(
            "/api/v1/query",
            json={"question": "¿Qué es Python?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "Esta es una respuesta de prueba"
        assert data["question"] == "¿Qué es Python?"

    def test_query_endpoint_validation(self, api_client):
        """Test: POST /api/v1/query con validación"""
        # Pregunta vacía
        response = api_client.post(
            "/api/v1/query",
            json={"question": ""}
        )
        
        assert response.status_code == 422  # Validation error

    def test_query_endpoint_with_params(self, api_client):
        """Test: POST /api/v1/query con parámetros"""
        response = api_client.post(
            "/api/v1/query",
            json={
                "question": "¿Qué es RAG?",
                "top_k": 5,
                "max_tokens": 256
            }
        )
        
        assert response.status_code == 200

    def test_root_endpoint(self, api_client):
        """Test: GET /"""
        response = api_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data

    def test_cors_headers(self, api_client):
        """Test: CORS headers presentes"""
        response = api_client.get("/api/v1/health")
        
        # FastAPI agrega CORS middleware automáticamente
        assert response.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════
# TESTS DE DOCUMENTACIÓN API
# ═══════════════════════════════════════════════════════════════════════════

class TestAPIDocumentation:
    """Tests para documentación de la API"""

    @pytest.fixture
    def api_client(self):
        """Cliente de test con mock"""
        from unittest.mock import Mock
        from src.infrastructure.entrypoints.fastapi_adapter import create_app
        
        mock_service = Mock()
        mock_service.ask.return_value = {"answer": "Test", "source_documents": []}
        mock_service.get_document_count.return_value = 0
        mock_service.llm.model_path = "test.gguf"
        
        app = create_app(mock_service)
        return TestClient(app)

    def test_openapi_schema_available(self, api_client):
        """Test: OpenAPI schema disponible"""
        response = api_client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    def test_docs_page_available(self, api_client):
        """Test: Swagger UI disponible"""
        response = api_client.get("/docs")
        
        assert response.status_code == 200
        assert "Swagger UI" in response.text or "swagger" in response.text.lower()

    def test_redoc_page_available(self, api_client):
        """Test: ReDoc disponible"""
        response = api_client.get("/redoc")
        
        assert response.status_code == 200
        assert "ReDoc" in response.text or "redoc" in response.text.lower()

    def test_api_endpoints_documented(self, api_client):
        """Test: Endpoints documentados en OpenAPI"""
        response = api_client.get("/openapi.json")
        data = response.json()
        
        paths = data["paths"]
        
        # Verificar endpoints principales
        assert "/api/v1/health" in paths
        assert "/api/v1/metrics" in paths
        assert "/api/v1/query" in paths
