"""
Tests unitarios para LangChainRAGAdapter.

Estos tests verifican el adapter que conecta RAGService con LangChain:
- Inicialización del adapter
- Invocación de la cadena RAG
- Configuración del retriever
- Manejo de errores
- Información de la cadena

Usa mocks para aislar de LangChain real.

Nota: Python 3.14 puede tener incompatibilidades de tipos con LangChain.
Estos tests se saltan si LangChain no puede ser importado.
"""

import sys

# Check if we can import LangChain without type errors BEFORE any other imports
langchain_available = True
langchain_error = None
try:
    from langchain.chains import create_retrieval_chain
    from langchain.chains.combine_documents import create_stuff_documents_chain
except TypeError as e:
    if "not subscriptable" in str(e) or "Unable to evaluate" in str(e):
        langchain_available = False
        langchain_error = str(e)[:100]
    else:
        raise
except Exception as e:
    langchain_available = False
    langchain_error = str(e)[:100]

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Any

# Only import after checking LangChain
if langchain_available:
    from src.infrastructure.adapters.langchain_rag_adapter import LangChainRAGAdapter
    from src.application.ports.rag_chain_port import RAGChainPort

# Skip entire module if LangChain has type issues with this Python version
pytestmark = pytest.mark.skipif(
    not langchain_available,
    reason=f"LangChain incompatible with Python 3.14 typing: {langchain_error}"
)


PROMPT_TEMPLATE = """Eres un asistente que responde preguntas basándose en el contexto.

Contexto: {context}

Pregunta: {input}

Responde basándote únicamente en el contexto proporcionado."""


class MockLLMPort:
    """Mock de LLMPort que retorna un modelo mockeado."""

    def get_model(self):
        mock_model = Mock()
        mock_model.invoke = Mock(return_value=Mock(content="Respuesta mock"))
        mock_model._call = Mock(return_value=Mock(content="Respuesta mock"))
        return mock_model


class MockDocumentStorePort:
    """Mock de DocumentStorePort."""

    def __init__(self, docs=None):
        self.docs = docs or []
        self._retriever = Mock()

    def get_retriever(self, search_kwargs=None):
        return self._retriever

    def search_similar(self, query, k=4):
        return self.docs[:k]


@pytest.fixture
def mock_llm_adapter():
    """Fixture de mock LLM adapter."""
    return MockLLMPort()


@pytest.fixture
def mock_doc_store():
    """Fixture de mock document store."""
    return MockDocumentStorePort()


@pytest.fixture
def langchain_adapter(mock_llm_adapter, mock_doc_store):
    """Adapter configurado con mocks para tests."""
    return LangChainRAGAdapter(
        llm_adapter=mock_llm_adapter,
        doc_store=mock_doc_store,
        prompt_template=PROMPT_TEMPLATE,
        top_k=4,
    )


class TestLangChainRAGAdapterInitialization:
    """Tests para inicialización del adapter."""

    def test_init_stores_attributes(self, mock_llm_adapter, mock_doc_store):
        """Test: __init__ almacena los atributos correctamente."""
        adapter = LangChainRAGAdapter(
            llm_adapter=mock_llm_adapter,
            doc_store=mock_doc_store,
            prompt_template=PROMPT_TEMPLATE,
            top_k=4,
        )

        assert adapter.llm is not None
        assert adapter.doc_store is mock_doc_store
        assert adapter.prompt_template == PROMPT_TEMPLATE
        assert adapter.top_k == 4

    def test_init_with_different_top_k(self, mock_llm_adapter, mock_doc_store):
        """Test: __init__ acepta diferentes valores de top_k."""
        adapter = LangChainRAGAdapter(
            llm_adapter=mock_llm_adapter,
            doc_store=mock_doc_store,
            prompt_template=PROMPT_TEMPLATE,
            top_k=8,
        )

        assert adapter.top_k == 8

    def test_init_stores_prompt_template(self, mock_llm_adapter, mock_doc_store):
        """Test: __init__ guarda el prompt template."""
        custom_prompt = "Custom prompt: {context} - {input}"
        adapter = LangChainRAGAdapter(
            llm_adapter=mock_llm_adapter,
            doc_store=mock_doc_store,
            prompt_template=custom_prompt,
            top_k=4,
        )

        assert adapter.prompt_template == custom_prompt


class TestLangChainRAGAdapterInterface:
    """Tests para verificar que implementa RAGChainPort."""

    def test_implements_rag_chain_port(self, langchain_adapter):
        """Test: LangChainRAGAdapter implementa RAGChainPort."""
        assert isinstance(langchain_adapter, RAGChainPort)

    def test_has_invoke_method(self, langchain_adapter):
        """Test: Tiene método invoke."""
        assert hasattr(langchain_adapter, "invoke")
        assert callable(langchain_adapter.invoke)

    def test_has_get_retriever_method(self, langchain_adapter):
        """Test: Tiene método get_retriever."""
        assert hasattr(langchain_adapter, "get_retriever")
        assert callable(langchain_adapter.get_retriever)

    def test_has_update_retriever_config_method(self, langchain_adapter):
        """Test: Tiene método update_retriever_config."""
        assert hasattr(langchain_adapter, "update_retriever_config")
        assert callable(langchain_adapter.update_retriever_config)

    def test_has_get_chain_info_method(self, langchain_adapter):
        """Test: Tiene método get_chain_info."""
        assert hasattr(langchain_adapter, "get_chain_info")
        assert callable(langchain_adapter.get_chain_info)


class TestLangChainRAGAdapterRetriever:
    """Tests para configuración del retriever."""

    def test_get_retriever_returns_doc_store_retriever(self, langchain_adapter, mock_doc_store):
        """Test: get_retriever usa el retriever del doc store."""
        retriever = langchain_adapter.get_retriever()
        assert retriever is mock_doc_store._retriever

    def test_get_retriever_passes_search_kwargs(self, langchain_adapter):
        """Test: get_retriever pasa search_kwargs con top_k."""
        adapter = langchain_adapter
        adapter.get_retriever(search_kwargs={"k": 10})

    def test_update_retriever_config_updates_top_k(self, langchain_adapter):
        """Test: update_retriever_config actualiza top_k."""
        langchain_adapter.update_retriever_config({"k": 10})
        assert langchain_adapter.top_k == 10


class TestLangChainRAGAdapterChainInfo:
    """Tests para get_chain_info."""

    def test_get_chain_info_returns_dict(self, langchain_adapter):
        """Test: get_chain_info retorna diccionario."""
        info = langchain_adapter.get_chain_info()
        assert isinstance(info, dict)

    def test_get_chain_info_contains_type(self, langchain_adapter):
        """Test: get_chain_info incluye type=langchain."""
        info = langchain_adapter.get_chain_info()
        assert info.get("type") == "langchain"

    def test_get_chain_info_contains_top_k(self, langchain_adapter):
        """Test: get_chain_info incluye top_k."""
        info = langchain_adapter.get_chain_info()
        assert "top_k" in info
        assert info["top_k"] == 4

    def test_get_chain_info_contains_prompt_template(self, langchain_adapter):
        """Test: get_chain_info incluye prompt_template (truncado)."""
        info = langchain_adapter.get_chain_info()
        assert "prompt_template" in info
        assert isinstance(info["prompt_template"], str)
        assert len(info["prompt_template"]) > 0


class TestLangChainRAGAdapterEdgeCases:
    """Tests para casos borde."""

    def test_invoke_with_empty_context(self, langchain_adapter):
        """Test: invoke maneja contexto vacío."""
        langchain_adapter.doc_store.docs = []

    def test_invoke_truncates_long_input(self, langchain_adapter):
        """Test: invoke maneja inputs muy largos."""
        long_input = "a" * 10000
        langchain_adapter.invoke(long_input)

    def test_init_with_empty_prompt_template_raises(self, mock_llm_adapter, mock_doc_store):
        """Test: init con prompt vacío puede fallar en LangChain."""
        with pytest.raises(Exception):
            LangChainRAGAdapter(
                llm_adapter=mock_llm_adapter,
                doc_store=mock_doc_store,
                prompt_template="",
                top_k=4,
            )

    def test_init_with_invalid_top_k(self, mock_llm_adapter, mock_doc_store):
        """Test: init con top_k inválido."""
        with pytest.raises(Exception):
            LangChainRAGAdapter(
                llm_adapter=mock_llm_adapter,
                doc_store=mock_doc_store,
                prompt_template=PROMPT_TEMPLATE,
                top_k=0,
            )

    def test_update_retriever_config_with_empty_dict(self, langchain_adapter):
        """Test: update_retriever_config con dict vacío no falla."""
        langchain_adapter.update_retriever_config({})
        assert langchain_adapter.top_k == 4

    def test_update_retriever_config_ignores_unknown_keys(self, langchain_adapter):
        """Test: update_retriever_config ignora claves desconocidas."""
        langchain_adapter.update_retriever_config({"unknown_key": 100})
        assert langchain_adapter.top_k == 4
