"""
Tests para ChromaDBAdapter.

Nota: Estos son tests unitarios que usan mocks.
Para tests de integracion, ver tests/integration/test_chromadb_integration.py
"""

import pytest
from unittest.mock import Mock, MagicMock, patch


class TestChromaDBAdapterInit:
    """Tests para inicializacion del adapter."""

    def test_init_with_valid_params(self):
        """Test: Inicializacion con parametros validos."""
        from src.infrastructure.adapters.chromadb_adapter import ChromaDBAdapter

        mock_embedding_port = Mock()
        mock_embedding_port.get_embeddings_model.return_value = Mock()

        adapter = ChromaDBAdapter(
            embedding_port=mock_embedding_port,
            persist_directory="./test_chroma",
            collection_name="test_collection",
        )

        assert adapter.persist_directory == "./test_chroma"
        assert adapter.collection_name == "test_collection"

    def test_init_stores_embedding_model(self):
        """Test: El modelo de embeddings se guarda correctamente."""
        from src.infrastructure.adapters.chromadb_adapter import ChromaDBAdapter

        mock_embedding_port = Mock()
        mock_model = Mock()
        mock_embedding_port.get_embeddings_model.return_value = mock_model

        adapter = ChromaDBAdapter(embedding_port=mock_embedding_port)

        assert adapter.embedding_model == mock_model


class TestChromaDBAdapterCount:
    """Tests para el metodo count()."""

    def test_count_returns_int(self):
        """Test: count() retorna un entero."""
        from src.infrastructure.adapters.chromadb_adapter import ChromaDBAdapter

        mock_embedding_port = Mock()
        mock_embedding_port.get_embeddings_model.return_value = Mock()

        with patch("src.infrastructure.adapters.chromadb_adapter.Chroma"):
            adapter = ChromaDBAdapter(embedding_port=mock_embedding_port)
            adapter._vector_store._collection.count.return_value = 42

            result = adapter.count()

            assert result == 42
            assert isinstance(result, int)

    def test_count_calls_collection_count(self):
        """Test: count() llama al metodo interno de ChromaDB."""
        from src.infrastructure.adapters.chromadb_adapter import ChromaDBAdapter

        mock_embedding_port = Mock()
        mock_embedding_port.get_embeddings_model.return_value = Mock()

        with patch("src.infrastructure.adapters.chromadb_adapter.Chroma"):
            adapter = ChromaDBAdapter(embedding_port=mock_embedding_port)
            adapter._vector_store._collection.count.return_value = 10

            adapter.count()

            adapter._vector_store._collection.count.assert_called_once()

    def test_count_exception_raises_chromadb_error(self):
        """Test: Excepcion en count() raise ChromaDBError."""
        from src.infrastructure.adapters.chromadb_adapter import ChromaDBAdapter, ChromaDBError

        mock_embedding_port = Mock()
        mock_embedding_port.get_embeddings_model.return_value = Mock()

        with patch("src.infrastructure.adapters.chromadb_adapter.Chroma"):
            adapter = ChromaDBAdapter(embedding_port=mock_embedding_port)
            adapter._vector_store._collection.count.side_effect = Exception("DB error")

            with pytest.raises(ChromaDBError):
                adapter.count()


class TestChromaDBAdapterAddDocuments:
    """Tests para add_documents()."""

    def test_add_documents_single_batch(self):
        """Test: add_documents con batch menor a batch_size."""
        from src.infrastructure.adapters.chromadb_adapter import ChromaDBAdapter

        mock_embedding_port = Mock()
        mock_embedding_port.get_embeddings_model.return_value = Mock()

        with patch("src.infrastructure.adapters.chromadb_adapter.Chroma"):
            adapter = ChromaDBAdapter(embedding_port=mock_embedding_port)

            docs = [Mock(), Mock()]
            adapter.add_documents(docs)

            adapter._vector_store.add_documents.assert_called_once()

    def test_add_documents_multiple_batches(self):
        """Test: add_documents divide en batches correctamente."""
        from src.infrastructure.adapters.chromadb_adapter import ChromaDBAdapter

        mock_embedding_port = Mock()
        mock_embedding_port.get_embeddings_model.return_value = Mock()

        with patch("src.infrastructure.adapters.chromadb_adapter.Chroma"):
            adapter = ChromaDBAdapter(embedding_port=mock_embedding_port)
            adapter._vector_store.add_documents = Mock()

            docs = [Mock()] * 15
            adapter.add_documents(docs, batch_size=5)

            assert adapter._vector_store.add_documents.call_count == 3

    def test_add_documents_with_ids(self):
        """Test: add_documents pasa ids al vector store."""
        from src.infrastructure.adapters.chromadb_adapter import ChromaDBAdapter

        mock_embedding_port = Mock()
        mock_embedding_port.get_embeddings_model.return_value = Mock()

        with patch("src.infrastructure.adapters.chromadb_adapter.Chroma"):
            adapter = ChromaDBAdapter(embedding_port=mock_embedding_port)
            adapter._vector_store.add_documents = Mock()

            docs = [Mock(), Mock()]
            ids = ["id1", "id2"]
            adapter.add_documents(docs, ids=ids)

            call_args = adapter._vector_store.add_documents.call_args
            assert call_args.kwargs.get("ids") == ids


class TestChromaDBAdapterSearchSimilar:
    """Tests para search_similar()."""

    def test_search_similar_returns_list(self):
        """Test: search_similar retorna una lista."""
        from src.infrastructure.adapters.chromadb_adapter import ChromaDBAdapter

        mock_embedding_port = Mock()
        mock_embedding_port.get_embeddings_model.return_value = Mock()

        with patch("src.infrastructure.adapters.chromadb_adapter.Chroma"):
            adapter = ChromaDBAdapter(embedding_port=mock_embedding_port)
            adapter._vector_store.similarity_search = Mock(return_value=[Mock(), Mock()])

            result = adapter.search_similar("test query", k=5)

            assert isinstance(result, list)
            assert len(result) == 2

    def test_search_similar_calls_similarity_search(self):
        """Test: search_similar llama a similarity_search con k correcto."""
        from src.infrastructure.adapters.chromadb_adapter import ChromaDBAdapter

        mock_embedding_port = Mock()
        mock_embedding_port.get_embeddings_model.return_value = Mock()

        with patch("src.infrastructure.adapters.chromadb_adapter.Chroma"):
            adapter = ChromaDBAdapter(embedding_port=mock_embedding_port)
            adapter._vector_store.similarity_search = Mock(return_value=[])

            adapter.search_similar("query", k=7)

            adapter._vector_store.similarity_search.assert_called_once_with("query", k=7)

    def test_search_similar_default_k(self):
        """Test: search_similar usa k=4 por defecto."""
        from src.infrastructure.adapters.chromadb_adapter import ChromaDBAdapter

        mock_embedding_port = Mock()
        mock_embedding_port.get_embeddings_model.return_value = Mock()

        with patch("src.infrastructure.adapters.chromadb_adapter.Chroma"):
            adapter = ChromaDBAdapter(embedding_port=mock_embedding_port)
            adapter._vector_store.similarity_search = Mock(return_value=[])

            adapter.search_similar("query")

            adapter._vector_store.similarity_search.assert_called_once_with("query", k=4)


class TestChromaDBAdapterListDocuments:
    """Tests para list_documents()."""

    def test_list_documents_returns_tuple(self):
        """Test: list_documents retorna (docs, total)."""
        from src.infrastructure.adapters.chromadb_adapter import ChromaDBAdapter

        mock_embedding_port = Mock()
        mock_embedding_port.get_embeddings_model.return_value = Mock()

        with patch("src.infrastructure.adapters.chromadb_adapter.Chroma"):
            adapter = ChromaDBAdapter(embedding_port=mock_embedding_port)
            adapter._vector_store._collection.count.return_value = 100
            adapter._vector_store._collection.get.return_value = {
                "ids": ["id1", "id2"],
                "metadatas": [{"source": "a"}, {"source": "b"}],
            }

            docs, total = adapter.list_documents(limit=10, offset=0)

            assert isinstance(docs, list)
            assert total == 100

    def test_list_documents_empty_when_offset_exceeds_total(self):
        """Test: list_documents retorna lista vacia si offset >= total."""
        from src.infrastructure.adapters.chromadb_adapter import ChromaDBAdapter

        mock_embedding_port = Mock()
        mock_embedding_port.get_embeddings_model.return_value = Mock()

        with patch("src.infrastructure.adapters.chromadb_adapter.Chroma"):
            adapter = ChromaDBAdapter(embedding_port=mock_embedding_port)
            adapter._vector_store._collection.count.return_value = 10

            docs, total = adapter.list_documents(limit=10, offset=15)

            assert docs == []
            assert total == 10


class TestChromaDBAdapterDeleteDocument:
    """Tests para delete_document()."""

    def test_delete_document_returns_true(self):
        """Test: delete_document retorna True al eliminar."""
        from src.infrastructure.adapters.chromadb_adapter import ChromaDBAdapter

        mock_embedding_port = Mock()
        mock_embedding_port.get_embeddings_model.return_value = Mock()

        with patch("src.infrastructure.adapters.chromadb_adapter.Chroma"):
            adapter = ChromaDBAdapter(embedding_port=mock_embedding_port)

            result = adapter.delete_document("doc_id")

            assert result is True
            adapter._vector_store._collection.delete.assert_called_once_with(ids=["doc_id"])

    def test_delete_document_exception_raises_chromadb_error(self):
        """Test: delete_document raise ChromaDBError si hay excepcion."""
        from src.infrastructure.adapters.chromadb_adapter import ChromaDBAdapter, ChromaDBError

        mock_embedding_port = Mock()
        mock_embedding_port.get_embeddings_model.return_value = Mock()

        with patch("src.infrastructure.adapters.chromadb_adapter.Chroma"):
            adapter = ChromaDBAdapter(embedding_port=mock_embedding_port)
            adapter._vector_store._collection.delete.side_effect = Exception("Not found")

            with pytest.raises(ChromaDBError):
                adapter.delete_document("nonexistent")
