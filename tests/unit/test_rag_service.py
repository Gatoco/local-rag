"""
Tests unitarios para RAGService.

Estos tests verifican la lógica de negocio del servicio RAG:
- Validación de inputs
- Ingesta de documentos
- Consultas RAG
- Manejo de errores
- Actualización de top_k

Nota: Usamos mocks para aislar RAGService de dependencias externas.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pydantic import ValidationError

from src.application.services.rag_service import (
    RAGService,
    RAGServiceError,
    RAGServiceIngestionError,
    RAGServiceQueryError,
)
from src.application.ports.rag_chain_port import RAGChainPort
from src.domain.models import Document, Query, Answer


# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_chain():
    """Mock de RAGChainPort para tests."""
    chain = Mock(spec=RAGChainPort)
    chain.invoke.return_value = {
        "answer": "Esta es una respuesta de prueba generada por el LLM.",
        "context": [
            Document(page_content="Documento de prueba 1", metadata={"source": "test1.pdf"}),
            Document(page_content="Documento de prueba 2", metadata={"source": "test2.pdf"}),
        ]
    }
    chain.get_retriever.return_value = Mock()
    chain.update_retriever_config = Mock()
    return chain


@pytest.fixture
def mock_doc_store():
    """Mock de DocumentStorePort."""
    store = Mock()
    store.add_documents = Mock()
    store.search_similar = Mock(return_value=[])
    store.get_retriever = Mock(return_value=Mock())
    store.count = Mock(return_value=100)
    return store


@pytest.fixture
def mock_loader():
    """Mock de DocumentLoaderPort."""
    loader = Mock()
    loader.load_and_split = Mock(return_value=[
        Mock(page_content="Chunk 1", metadata={}),
        Mock(page_content="Chunk 2", metadata={}),
    ])
    loader.load_directory = Mock(return_value=[
        Mock(page_content="Chunk dir 1", metadata={}),
    ])
    return loader


@pytest.fixture
def rag_service(mock_chain, mock_doc_store, mock_loader):
    """RAGService configurado con mocks."""
    return RAGService(
        chain=mock_chain,
        doc_store_adapter=mock_doc_store,
        loader_adapter=mock_loader,
        top_k=4
    )


# ═══════════════════════════════════════════════════════════════════════════
# TESTS DE INICIALIZACIÓN
# ═══════════════════════════════════════════════════════════════════════════

class TestRAGServiceInitialization:
    """Tests para inicialización de RAGService"""

    def test_init_with_valid_params(self, mock_chain, mock_doc_store, mock_loader):
        """Test: Inicializar con parámetros válidos"""
        service = RAGService(
            chain=mock_chain,
            doc_store_adapter=mock_doc_store,
            loader_adapter=mock_loader,
            top_k=4
        )
        
        assert service.top_k == 4
        assert service.chain == mock_chain
        assert service.doc_store == mock_doc_store
        assert service.loader == mock_loader

    def test_init_with_default_top_k(self, mock_chain, mock_doc_store, mock_loader):
        """Test: Inicializar con top_k por defecto"""
        service = RAGService(
            chain=mock_chain,
            doc_store_adapter=mock_doc_store,
            loader_adapter=mock_loader
        )
        
        assert service.top_k == 4

    def test_init_with_invalid_top_k_zero(self, mock_chain, mock_doc_store, mock_loader):
        """Test: Inicializar con top_k=0 debe fallar"""
        with pytest.raises(ValueError, match="top_k debe ser un entero positivo"):
            RAGService(
                chain=mock_chain,
                doc_store_adapter=mock_doc_store,
                loader_adapter=mock_loader,
                top_k=0
            )

    def test_init_with_invalid_top_k_negative(self, mock_chain, mock_doc_store, mock_loader):
        """Test: Inicializar con top_k negativo debe fallar"""
        with pytest.raises(ValueError):
            RAGService(
                chain=mock_chain,
                doc_store_adapter=mock_doc_store,
                loader_adapter=mock_loader,
                top_k=-1
            )

    def test_init_with_high_top_k_warning(self, mock_chain, mock_doc_store, mock_loader, caplog):
        """Test: Inicializar con top_k alto genera warning"""
        import logging
        with caplog.at_level(logging.WARNING):
            service = RAGService(
                chain=mock_chain,
                doc_store_adapter=mock_doc_store,
                loader_adapter=mock_loader,
                top_k=25
            )
        
        assert "top_k=25 es alto" in caplog.text


# ═══════════════════════════════════════════════════════════════════════════
# TESTS DE CONSULTAS (QUERY)
# ═══════════════════════════════════════════════════════════════════════════

class TestRAGServiceQuery:
    """Tests para método ask() de RAGService"""

    def test_ask_valid_question(self, rag_service, mock_chain):
        """Test: Consulta válida retorna respuesta"""
        result = rag_service.ask("¿Qué es Python?")
        
        assert "answer" in result
        assert "source_documents" in result
        assert result["answer"] == "Esta es una respuesta de prueba generada por el LLM."
        assert len(result["source_documents"]) == 2
        
        # Verificar que se invocó la chain
        mock_chain.invoke.assert_called_once_with("¿Qué es Python?")

    def test_ask_question_with_whitespace(self, rag_service, mock_chain):
        """Test: Pregunta con whitespace se limpia"""
        result = rag_service.ask("  ¿Qué es Python?  ")
        
        assert result["answer"] is not None
        # Pydantic strip whitespace
        mock_chain.invoke.assert_called_once()

    def test_ask_empty_question_fails(self, rag_service):
        """Test: Pregunta vacía debe fallar"""
        with pytest.raises(ValueError, match="Consulta inválida"):
            rag_service.ask("")

    def test_ask_whitespace_only_question_fails(self, rag_service):
        """Test: Pregunta con solo whitespace debe fallar"""
        with pytest.raises(ValueError):
            rag_service.ask("   ")

    def test_ask_chain_returns_empty_answer(self, rag_service, mock_chain):
        """Test: Chain retorna respuesta vacía debe fallar"""
        mock_chain.invoke.return_value = {"answer": "", "context": []}
        
        with pytest.raises(RAGServiceQueryError, match="LLM generated empty answer"):
            rag_service.ask("¿Qué es Python?")

    def test_ask_chain_returns_none_answer(self, rag_service, mock_chain):
        """Test: Chain retorna None debe fallar"""
        mock_chain.invoke.return_value = {"answer": None, "context": []}
        
        with pytest.raises(RAGServiceQueryError):
            rag_service.ask("¿Qué es Python?")

    def test_ask_chain_exception(self, rag_service, mock_chain):
        """Test: Excepción en chain se maneja"""
        mock_chain.invoke.side_effect = Exception("Error en LLM")
        
        with pytest.raises(RAGServiceQueryError):
            rag_service.ask("¿Qué es Python?")

    def test_ask_convert_context_with_langchain_docs(self, rag_service, mock_chain):
        """Test: Convertir contexto de LangChain a Document"""
        # Mock con objetos tipo LangChain
        mock_doc = MagicMock()
        mock_doc.page_content = "Content from LangChain doc"
        mock_doc.metadata = {"source": "langchain.pdf", "page": 1}
        mock_doc.id = "doc_123"
        
        mock_chain.invoke.return_value = {
            "answer": "Answer",
            "context": [mock_doc]
        }
        
        result = rag_service.ask("Question")
        
        assert len(result["source_documents"]) == 1
        assert result["source_documents"][0].page_content == "Content from LangChain doc"
        assert result["source_documents"][0].metadata["source"] == "langchain.pdf"

    def test_ask_convert_context_with_dict(self, rag_service, mock_chain):
        """Test: Convertir contexto de dict a Document"""
        mock_chain.invoke.return_value = {
            "answer": "Answer",
            "context": [
                {"page_content": "Dict content", "metadata": {"source": "dict.pdf"}}
            ]
        }
        
        result = rag_service.ask("Question")
        
        assert len(result["source_documents"]) == 1
        assert result["source_documents"][0].page_content == "Dict content"

    def test_ask_convert_context_with_invalid_doc(self, rag_service, mock_chain, caplog):
        """Test: Documento inválido se saltea con warning"""
        mock_chain.invoke.return_value = {
            "answer": "Answer",
            "context": [None, "invalid", 123]  # Documentos inválidos
        }
        
        import logging
        with caplog.at_level(logging.WARNING):
            result = rag_service.ask("Question")
        
        # Debería crear documentos fallback
        assert len(result["source_documents"]) > 0


# ═══════════════════════════════════════════════════════════════════════════
# TESTS DE INGESTIÓN
# ═══════════════════════════════════════════════════════════════════════════

class TestRAGServiceIngestion:
    """Tests para métodos de ingesta de RAGService"""

    def test_ingest_document_valid_file(self, rag_service, mock_loader, mock_doc_store):
        """Test: Ingestar archivo válido"""
        rag_service.ingest_document("./test/file.pdf")
        
        mock_loader.load_and_split.assert_called_once_with("./test/file.pdf")
        mock_doc_store.add_documents.assert_called_once()

    def test_ingest_document_no_chunks(self, rag_service, mock_loader):
        """Test: Ingestar archivo sin chunks debe fallar"""
        mock_loader.load_and_split.return_value = []
        
        with pytest.raises(RAGServiceIngestionError, match="No se generaron fragmentos"):
            rag_service.ingest_document("./test/empty.pdf")

    def test_ingest_document_file_not_found(self, rag_service, mock_loader):
        """Test: Archivo no encontrado debe fallar"""
        mock_loader.load_and_split.side_effect = FileNotFoundError("File not found")
        
        with pytest.raises(FileNotFoundError):
            rag_service.ingest_document("./nonexistent.pdf")

    def test_ingest_document_exception(self, rag_service, mock_loader):
        """Test: Excepción en ingesta se maneja"""
        mock_loader.load_and_split.side_effect = Exception("Error loading")
        
        with pytest.raises(RAGServiceIngestionError):
            rag_service.ingest_document("./test/error.pdf")

    def test_ingest_directory_valid(self, rag_service, mock_loader, mock_doc_store):
        """Test: Ingestar directorio válido"""
        rag_service.ingest_directory("./test/docs")
        
        mock_loader.load_directory.assert_called_once_with("./test/docs")
        mock_doc_store.add_documents.assert_called_once()

    def test_ingest_directory_no_documents(self, rag_service, mock_loader):
        """Test: Directorio sin documentos debe fallar"""
        mock_loader.load_directory.return_value = []
        
        with pytest.raises(RAGServiceIngestionError, match="No se encontraron documentos"):
            rag_service.ingest_directory("./empty/dir")

    def test_ingest_directory_not_found(self, rag_service, mock_loader):
        """Test: Directorio no encontrado debe fallar"""
        mock_loader.load_directory.side_effect = FileNotFoundError("Dir not found")
        
        with pytest.raises(FileNotFoundError):
            rag_service.ingest_directory("./nonexistent/dir")


# ═══════════════════════════════════════════════════════════════════════════
# TESTS DE MÉTODOS AUXILIARES
# ═══════════════════════════════════════════════════════════════════════════

class TestRAGServiceAuxiliary:
    """Tests para métodos auxiliares de RAGService"""

    def test_get_document_count(self, rag_service, mock_doc_store):
        """Test: Obtener conteo de documentos"""
        count = rag_service.get_document_count()

        assert count == 100
        mock_doc_store.count.assert_called_once()

    def test_get_document_count_exception(self, rag_service, mock_doc_store):
        """Test: Excepcion en conteo lanza RAGServiceError"""
        from src.application.services.rag_service import RAGServiceError

        mock_doc_store.count.side_effect = Exception("Error")

        with pytest.raises(RAGServiceError):
            rag_service.get_document_count()

    def test_update_top_k_valid(self, rag_service, mock_chain):
        """Test: Actualizar top_k válido"""
        rag_service.update_top_k(8)
        
        assert rag_service.top_k == 8
        mock_chain.update_retriever_config.assert_called_once_with({"k": 8})

    def test_update_top_k_invalid_zero(self, rag_service):
        """Test: Actualizar top_k=0 debe fallar"""
        with pytest.raises(ValueError):
            rag_service.update_top_k(0)

    def test_update_top_k_invalid_negative(self, rag_service):
        """Test: Actualizar top_k negativo debe fallar"""
        with pytest.raises(ValueError):
            rag_service.update_top_k(-5)

    def test_get_chain_info_with_method(self, mock_doc_store, mock_loader):
        """Test: Obtener información de chain con método"""
        mock_chain = Mock(spec=RAGChainPort)
        mock_chain.get_chain_info = Mock(return_value={
            "type": "langchain",
            "top_k": 4,
            "prompt_template": "Eres un asistente..."
        })
        
        service = RAGService(
            chain=mock_chain,
            doc_store_adapter=mock_doc_store,
            loader_adapter=mock_loader
        )
        
        info = service.get_chain_info()
        
        assert info["type"] == "langchain"
        assert info["top_k"] == 4

    def test_get_chain_info_without_method(self, mock_doc_store, mock_loader):
        """Test: Obtener información de chain sin método"""
        mock_chain = Mock(spec=RAGChainPort)
        # No tiene get_chain_info
        
        service = RAGService(
            chain=mock_chain,
            doc_store_adapter=mock_doc_store,
            loader_adapter=mock_loader
        )
        
        info = service.get_chain_info()
        
        assert "type" in info
        assert "top_k" in info


# ═══════════════════════════════════════════════════════════════════════════
# TESTS DE INTEGRACIÓN ENTRE COMPONENTES
# ═══════════════════════════════════════════════════════════════════════════

class TestRAGServiceIntegration:
    """Tests de integración entre componentes de RAGService"""

    def test_full_query_flow(self, rag_service, mock_chain):
        """Test: Flujo completo de consulta"""
        # Configurar mock para simular flujo real
        mock_chain.invoke.return_value = {
            "answer": "Python es un lenguaje de programación interpretado.",
            "context": [
                Document(
                    page_content="Python es un lenguaje de alto nivel...",
                    metadata={"source": "python_intro.pdf", "page": 1},
                    id="chunk_001"
                )
            ]
        }
        
        result = rag_service.ask("¿Qué es Python?")
        
        # Verificar respuesta
        assert "answer" in result
        assert "source_documents" in result
        assert len(result["source_documents"]) == 1
        
        # Verificar que los metadatos se preservan
        doc = result["source_documents"][0]
        assert doc.metadata["source"] == "python_intro.pdf"
        assert doc.id == "chunk_001"

    def test_query_with_multiple_sources(self, rag_service, mock_chain):
        """Test: Consulta con múltiples fuentes"""
        mock_chain.invoke.return_value = {
            "answer": "Respuesta basada en múltiples fuentes",
            "context": [
                Document(page_content="Source 1", metadata={"source": "doc1.pdf"}),
                Document(page_content="Source 2", metadata={"source": "doc2.pdf"}),
                Document(page_content="Source 3", metadata={"source": "doc3.pdf"}),
            ]
        }
        
        result = rag_service.ask("Pregunta compleja")
        
        assert len(result["source_documents"]) == 3
        sources = set(doc.metadata["source"] for doc in result["source_documents"])
        assert len(sources) == 3

    def test_ingest_then_query(self, rag_service, mock_chain, mock_loader, mock_doc_store):
        """Test: Ingestar y luego consultar"""
        # 1. Ingestar
        rag_service.ingest_document("./test/doc.pdf")
        assert mock_doc_store.add_documents.called
        
        # 2. Consultar
        rag_service.ask("¿Qué se ingirió?")
        assert mock_chain.invoke.called
        
        # Verificar que ambas operaciones se ejecutaron
        assert mock_loader.load_and_split.called
        assert mock_chain.invoke.called
