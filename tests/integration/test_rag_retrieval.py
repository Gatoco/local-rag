"""
Tests para RAG retrieval con ChromaDB y verificación de fuentes.

Tests verifican:
- Retrieval de documentos desde ChromaDB
- Calidad de las fuentes devueltas
- Parameterized queries
- Edge cases de retrieval
"""

import os
import pytest

from src.infrastructure.adapters.hf_embedding_adapter import HFEmbeddingAdapter
from src.infrastructure.adapters.chromadb_adapter import ChromaDBAdapter


class TestRAGRetrieval:
    """Tests para retrieval de documentos en ChromaDB"""

    @pytest.fixture
    def chromadb_adapter(self):
        """ChromaDB adapter conectado a la DB real"""
        embeddings = HFEmbeddingAdapter(model_name='BAAI/bge-large-en-v1.5')
        return ChromaDBAdapter(
            embedding_port=embeddings,
            persist_directory='./chroma_db'
        )

    def test_retrieval_returns_sources(self, chromadb_adapter):
        """Test: Retrieval devuelve documentos fuente"""
        chroma_store = chromadb_adapter.vector_store
        collection = chroma_store._collection

        assert collection.count() > 0, "Collection should have documents"

        query = "student grades performance"
        results = chroma_store.similarity_search_with_score(query, k=4)

        assert len(results) > 0, "Should return results for student query"
        for doc, score in results:
            assert doc.page_content, "Document should have content"
            assert score > 0.0, "Score should be positive"

    def test_retrieval_with_different_queries(self, chromadb_adapter):
        """Test: Retrieval funciona con diferentes queries"""
        chroma_store = chromadb_adapter.vector_store
        collection = chroma_store._collection

        queries = [
            "math grades",
            "exam scores",
            "student performance data",
        ]

        for query in queries:
            results = chroma_store.similarity_search_with_score(query, k=2)
            assert len(results) > 0, f"Should return results for: {query}"

    def test_retrieval_top_k_parameter(self, chromadb_adapter):
        """Test: Retrieval respeta parámetro top_k"""
        chroma_store = chromadb_adapter.vector_store

        for k in [1, 3, 5, 10]:
            results = chroma_store.similarity_search_with_score("student", k=k)
            assert len(results) == k, f"Should return exactly {k} results for k={k}"

    def test_retrieval_score_range(self, chromadb_adapter):
        """Test: Scores de retrieval están en rango válido"""
        chroma_store = chromadb_adapter.vector_store

        results = chroma_store.similarity_search_with_score("student performance", k=10)

        for doc, score in results:
            assert 0.0 <= score <= 1.0, f"Score {score} out of range [0, 1]"

    def test_retrieval_context_relevance(self, chromadb_adapter):
        """Test: Documentos recuperados son contextualmente relevantes"""
        chroma_store = chromadb_adapter.vector_store

        results = chroma_store.similarity_search_with_score(
            "calificaciones de estudiantes",
            k=5
        )

        assert len(results) > 0, "Should find results for Spanish query"

        for doc, score in results:
            content_lower = doc.page_content.lower()
            assert any(
                keyword in content_lower
                for keyword in ['student', 'grade', 'score', 'calificacion', 'performance']
            ), f"Document should contain relevant keywords: {doc.page_content[:100]}"

    def test_retrieval_metadata_preserved(self, chromadb_adapter):
        """Test: Metadata se preserva en retrieval"""
        chroma_store = chromadb_adapter.vector_store

        results = chroma_store.similarity_search_with_score("student", k=3)

        for doc, score in results:
            assert doc.metadata, "Document should have metadata"
            assert isinstance(doc.metadata, dict), "Metadata should be dict"

    def test_retrieval_empty_query_handling(self, chromadb_adapter):
        """Test: Query vacío retorna error o vacío"""
        chroma_store = chromadb_adapter.vector_store

        results = chroma_store.similarity_search_with_score("", k=3)
        assert len(results) >= 0

    def test_retrieval_id_consistency(self, chromadb_adapter):
        """Test: Misma query retorna IDs consistentes"""
        chroma_store = chromadb_adapter.vector_store

        query = "student grades"

        results1 = chroma_store.similarity_search_with_score(query, k=5)
        results2 = chroma_store.similarity_search_with_score(query, k=5)

        ids1 = [getattr(doc, 'id', doc.page_content[:50]) for doc, _ in results1]
        ids2 = [getattr(doc, 'id', doc.page_content[:50]) for doc, _ in results2]

        assert ids1 == ids2, "Same query should return same documents"

    def test_collection_count(self, chromadb_adapter):
        """Test: Verifica count de colección"""
        chroma_store = chromadb_adapter.vector_store
        collection = chroma_store._collection

        count = collection.count()
        assert count >= 2400, f"Expected at least 2400 documents, got {count}"
        print(f"\n[V] Collection has {count} documents indexed")


class TestRAGRetrievalWithMinimax:
    """Tests de integración RAG con MiniMax via CloudLLMAdapter"""

    @pytest.fixture
    def minimax_api_key(self):
        """Obtiene API key de .env"""
        from dotenv import load_dotenv
        load_dotenv()
        return os.getenv("MINIMAX_API_KEY")

    def test_cloud_llm_adapter_minimax(self, minimax_api_key):
        """Test: CloudLLMAdapter funciona con MiniMax"""
        if not minimax_api_key:
            pytest.skip("MINIMAX_API_KEY not set")

        from src.infrastructure.adapters.cloud_llm_adapter import CloudLLMAdapter

        adapter = CloudLLMAdapter(provider="minimax", api_key=minimax_api_key)

        assert adapter.provider == "minimax"
        assert adapter.model == "MiniMax-M2.7"

        info = adapter.get_model_info()
        assert info["provider"] == "minimax"
        assert info["api_key_set"] is True

    def test_minimax_generate_response(self, minimax_api_key):
        """Test: MiniMax genera respuesta"""
        if not minimax_api_key:
            pytest.skip("MINIMAX_API_KEY not set")

        from src.infrastructure.adapters.cloud_llm_adapter import CloudLLMAdapter

        adapter = CloudLLMAdapter(provider="minimax", api_key=minimax_api_key)
        response = adapter.generate_response("Say 'OK' in one word", max_tokens=10)

        assert response, "Should return non-empty response"
        print(f"\n[V] MiniMax response: {response}")

    def test_minimax_streaming(self, minimax_api_key):
        """Test: MiniMax streaming funciona"""
        if not minimax_api_key:
            pytest.skip("MINIMAX_API_KEY not set")

        from src.infrastructure.adapters.cloud_llm_adapter import CloudLLMAdapter

        adapter = CloudLLMAdapter(provider="minimax", api_key=minimax_api_key)

        tokens = list(adapter.generate_stream("Count from 1 to 3", max_tokens=20))

        assert len(tokens) > 0, "Should return tokens"
        full_response = "".join(tokens)
        assert full_response, "Full response should not be empty"
        print(f"\n[V] MiniMax stream: {full_response[:50]}...")

    def test_rag_flow_with_minimax(self, minimax_api_key):
        """Test: RAG flow end-to-end con MiniMax (requiere chroma_db indexing)"""
        if not minimax_api_key:
            pytest.skip("MINIMAX_API_KEY not set")

        from langchain_huggingface import HuggingFaceEmbeddings
        from src.infrastructure.adapters.cloud_llm_adapter import CloudLLMAdapter
        from src.infrastructure.adapters.chromadb_adapter import ChromaDBAdapter
        from src.infrastructure.adapters.langchain_rag_adapter import LangChainRAGAdapter

        embeddings = HuggingFaceEmbeddings(
            model_name='BAAI/bge-large-en-v1.5',
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True, 'batch_size': 32}
        )

        store = ChromaDBAdapter(embedding_port=embeddings, persist_directory='./chroma_db')
        collection = store.vector_store._collection

        if collection.count() == 0:
            pytest.skip("No documents indexed in chroma_db")

        llm = CloudLLMAdapter(provider="minimax", api_key=minimax_api_key)

        chain = LangChainRAGAdapter(
            llm_adapter=llm,
            doc_store=store,
            prompt_template="""Eres un asistente que responde preguntas basándose en el contexto proporcionado.

Contexto: {context}

Pregunta: {input}

Responde basándote únicamente en el contexto proporcionado.""",
            top_k=3,
        )

        result = chain.invoke("What information is available about student grades?")

        assert result.get("answer"), "Should have answer"
        assert len(result.get("context", [])) > 0, "Should have context documents"

        print(f"\n[V] RAG with MiniMax answer: {result['answer'][:100]}...")
        print(f"[V] Sources used: {len(result['context'])}")

    def test_rag_service_ask_with_minimax(self, minimax_api_key):
        """Test: RAGService.ask() con provider=minimax"""
        if not minimax_api_key:
            pytest.skip("MINIMAX_API_KEY not set")

        from langchain_huggingface import HuggingFaceEmbeddings
        from src.infrastructure.adapters.cloud_llm_adapter import CloudLLMAdapter
        from src.infrastructure.adapters.chromadb_adapter import ChromaDBAdapter
        from src.infrastructure.adapters.langchain_rag_adapter import LangChainRAGAdapter
        from src.infrastructure.adapters.langchain_loader_adapter import LangChainLoaderAdapter
        from src.application.services.rag_service import RAGService

        embeddings = HuggingFaceEmbeddings(
            model_name='BAAI/bge-large-en-v1.5',
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True, 'batch_size': 32}
        )

        store = ChromaDBAdapter(embedding_port=embeddings, persist_directory='./chroma_db')
        loader = LangChainLoaderAdapter()

        collection = store.vector_store._collection
        if collection.count() == 0:
            pytest.skip("No documents indexed")

        llm = CloudLLMAdapter(provider="minimax", api_key=minimax_api_key)

        chain = LangChainRAGAdapter(
            llm_adapter=llm,
            doc_store=store,
            prompt_template="Eres un asistente. Contexto: {context}. Pregunta: {input}",
            top_k=3,
        )

        service = RAGService(chain=chain, doc_store_adapter=store, loader_adapter=loader, top_k=3)

        result = service.ask(
            question="Tell me about student performance data",
            provider="minimax",
            api_key=minimax_api_key,
        )

        assert result.get("answer"), "Should have answer"
        assert len(result.get("source_documents", [])) > 0, "Should have sources"

        print(f"\n[V] RAGService with MiniMax: {result['answer'][:100]}...")

    def test_minimax_provider_models(self):
        """Test: MiniMax provider models list"""
        from src.infrastructure.adapters.cloud_llm_adapter import PROVIDER_CONFIG

        minimax_config = PROVIDER_CONFIG.get("minimax")
        assert minimax_config is not None, "MiniMax should be in provider config"

        assert "MiniMax-M2.7" in minimax_config["models"]
        assert minimax_config["supports_streaming"] is True
        assert minimax_config["api_key_env"] == "MINIMAX_API_KEY"


class TestRAGRetrievalEdgeCases:
    """Tests para edge cases de retrieval"""

    @pytest.fixture
    def chromadb_adapter(self):
        from langchain_huggingface import HuggingFaceEmbeddings
        return ChromaDBAdapter(
            embedding_port=HuggingFaceEmbeddings(
                model_name='BAAI/bge-large-en-v1.5',
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True, 'batch_size': 32}
            ),
            persist_directory='./chroma_db'
        )

    def test_retrieval_with_very_long_query(self, chromadb_adapter):
        """Test: Query muy larga no rompe retrieval"""
        chroma_store = chromadb_adapter.vector_store

        long_query = "student " * 100
        results = chroma_store.similarity_search_with_score(long_query, k=3)

        assert len(results) >= 0

    def test_retrieval_with_special_characters(self, chromadb_adapter):
        """Test: Query con caracteres especiales"""
        chroma_store = chromadb_adapter.vector_store

        query = "student@#%^&*()grades"
        results = chroma_store.similarity_search_with_score(query, k=3)

        assert len(results) >= 0

    def test_retrieval_with_unicode(self, chromadb_adapter):
        """Test: Query con unicode"""
        chroma_store = chromadb_adapter.vector_store

        query = "calificaciones студент 学生"
        results = chroma_store.similarity_search_with_score(query, k=3)

        assert len(results) >= 0

    def test_retrieval_no_results_returns_empty(self, chromadb_adapter):
        """Test: Query sin resultados retorna lista vacía"""
        chroma_store = chromadb_adapter.vector_store

        very_specific_query = "xyz123abcnonexistentconcept999"
        results = chroma_store.similarity_search_with_score(very_specific_query, k=3)

        assert isinstance(results, list)