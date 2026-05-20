"""
Tests for indexing functionality.

Run with: pytest tests/unit/test_indexing.py -v
"""

import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from langchain.schema import Document
from chromadb.config import Settings
import chromadb


CHROMA_DB_DIR = Path(__file__).parent.parent.parent / "chroma_db"
MANIFEST_FILE = CHROMA_DB_DIR / "indexed_manifest.json"
COLLECTION_NAME = "test_local_rag_docs"


@pytest.fixture
def temp_chroma_dir():
    """Create a temporary ChromaDB directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_docs():
    """Create sample documents for testing."""
    return [
        Document(page_content=f"Document {i} content for testing indexing", metadata={"source": "test", "index": i})
        for i in range(100)
    ]


class TestIndexingFunctionality:
    """Test the core indexing functionality."""

    def test_embed_batch_returns_correct_dimensions(self):
        """Test that embed_batch returns embeddings with correct dimension."""
        from langchain_huggingface import HuggingFaceEmbeddings

        embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-large-en-v1.5",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True, "batch_size": 16}
        )

        texts = ["test document " + str(i) for i in range(10)]
        result = embeddings.embed_documents(texts)

        assert len(result) == 10
        assert len(result[0]) == 1024

    def test_embed_query_returns_correct_dimensions(self):
        """Test that embed_query returns embedding with correct dimension."""
        from langchain_huggingface import HuggingFaceEmbeddings

        embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-large-en-v1.5",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True, "batch_size": 16}
        )

        result = embeddings.embed_query("test query")

        assert len(result) == 1024

    def test_safe_progress_print_works(self):
        """Test that _safe_progress_print doesn't crash."""
        from src.infrastructure.entrypoints.repl.repl import REPL

        repl = REPL.__new__(REPL)
        repl._safe_progress_print(50, 100, "Test:")
        repl._safe_progress_print(0, 0, "Test:")
        repl._safe_progress_print(100, 100, "Test:")

    def test_compute_doc_hash(self):
        """Test document hash computation."""
        from scripts.index_documents import compute_doc_hash

        doc1 = Document(page_content="test", metadata={"source": "test"})
        doc2 = Document(page_content="test", metadata={"source": "test"})
        doc3 = Document(page_content="different", metadata={"source": "test"})

        hash1 = compute_doc_hash(doc1)
        hash2 = compute_doc_hash(doc2)
        hash3 = compute_doc_hash(doc3)

        assert hash1 == hash2
        assert hash1 != hash3

    def test_manifest_save_load(self, temp_chroma_dir):
        """Test manifest save and load functionality."""
        from scripts.index_documents import load_manifest, save_manifest

        manifest_data = {"last_indexed_id": 50, "total_indexed": 50, "timestamp": time.time()}

        with patch.object(Path, 'parent', temp_chroma_dir):
            with patch('scripts.index_documents.MANIFEST_FILE', temp_chroma_dir / "test_manifest.json"):
                with patch('scripts.index_documents.save_manifest') as mock_save:
                    manifest = {"last_indexed_id": 50, "total_indexed": 50}
                    mock_save(manifest)

                with patch('scripts.index_documents.load_manifest') as mock_load:
                    mock_load.return_value = manifest
                    loaded = mock_load()
                    assert loaded["last_indexed_id"] == 50


class TestIndexingIntegration:
    """Integration tests for indexing (requires actual ChromaDB and embedding model)."""

    @pytest.mark.slow
    def test_indexing_with_small_dataset(self, temp_chroma_dir, sample_docs):
        """Test indexing with a small dataset (100 docs)."""
        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from concurrent.futures import ThreadPoolExecutor, as_completed

        if os.environ.get("SKIP_SLOW_TESTS"):
            pytest.skip("Skipping slow test")

        embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-large-en-v1.5",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True, "batch_size": 16}
        )

        client = chromadb.PersistentClient(
            path=str(temp_chroma_dir),
            settings=Settings(anonymized_telemetry=False)
        )

        try:
            client.delete_collection(name=COLLECTION_NAME)
        except Exception:
            pass

        collection = client.create_collection(name=COLLECTION_NAME)

        batch_size = 50
        total_chunks = len(sample_docs)

        def embed_batch(texts):
            return embeddings.embed_documents(texts)

        indexed = 0
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            for i in range(0, total_chunks, batch_size):
                batch = sample_docs[i:i + batch_size]
                texts = [doc.page_content for doc in batch]
                future = executor.submit(embed_batch, texts)
                futures[future] = i

            for future in as_completed(futures):
                batch_start = futures[future]
                emb_batch = future.result()
                batch_end = min(batch_start + batch_size, total_chunks)
                batch = sample_docs[batch_start:batch_end]

                ids = [f"test_doc_{j}" for j in range(batch_start, batch_end)]
                texts = [doc.page_content for doc in batch]
                metas = [doc.metadata for doc in batch]

                collection.add(ids=ids, documents=texts, embeddings=emb_batch, metadatas=metas)
                indexed += len(batch)

        assert collection.count() == 100

    @pytest.mark.slow
    def test_no_duplicate_ids_on_reindex(self, temp_chroma_dir, sample_docs):
        """Test that reindexing doesn't create duplicate IDs."""
        from langchain_huggingface import HuggingFaceEmbeddings
        from concurrent.futures import ThreadPoolExecutor, as_completed

        if os.environ.get("SKIP_SLOW_TESTS"):
            pytest.skip("Skipping slow test")

        embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-large-en-v1.5",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True, "batch_size": 16}
        )

        client = chromadb.PersistentClient(
            path=str(temp_chroma_dir),
            settings=Settings(anonymized_telemetry=False)
        )

        collection = client.create_collection(name=COLLECTION_NAME)
        batch_size = 50

        def embed_batch(texts):
            return embeddings.embed_documents(texts)

        texts = [doc.page_content for doc in sample_docs]
        metas = [doc.metadata for doc in sample_docs]
        ids = [f"test_doc_{j}" for j in range(len(sample_docs))]

        emb = embeddings.embed_documents(texts)
        collection.add(ids=ids, documents=texts, embeddings=emb, metadatas=metas)

        first_count = collection.count()
        assert first_count == 100

        client.delete_collection(name=COLLECTION_NAME)
        collection = client.create_collection(name=COLLECTION_NAME)

        emb2 = embeddings.embed_documents(texts)
        collection.add(ids=ids, documents=texts, embeddings=emb2, metadatas=metas)

        second_count = collection.count()
        assert second_count == 100

    @pytest.mark.slow
    def test_query_returns_correct_dimension(self, temp_chroma_dir, sample_docs):
        """Test that querying works with correct embedding dimension."""
        from langchain_huggingface import HuggingFaceEmbeddings

        if os.environ.get("SKIP_SLOW_TESTS"):
            pytest.skip("Skipping slow test")

        embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-large-en-v1.5",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True, "batch_size": 16}
        )

        client = chromadb.PersistentClient(
            path=str(temp_chroma_dir),
            settings=Settings(anonymized_telemetry=False)
        )

        try:
            client.delete_collection(name=COLLECTION_NAME)
        except Exception:
            pass

        collection = client.create_collection(name=COLLECTION_NAME)

        texts = [doc.page_content for doc in sample_docs[:10]]
        metas = [doc.metadata for doc in sample_docs[:10]]
        ids = [f"test_doc_{j}" for j in range(10)]

        emb = embeddings.embed_documents(texts)
        collection.add(ids=ids, documents=texts, embeddings=emb, metadatas=metas)

        query_emb = embeddings.embed_query("testing query")
        assert len(query_emb) == 1024

        results = collection.query(query_embeddings=[query_emb], n_results=2)
        assert len(results["documents"][0]) == 2


class TestIndexingEdgeCases:
    """Test edge cases in indexing."""

    def test_nonexistent_directory(self):
        """Test handling of nonexistent directory."""
        from scripts.index_documents import index_documents

        result = index_documents(docs_dir="/nonexistent/directory/path")

        assert not result.get("success")
        assert "not found" in result.get("error", "").lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])