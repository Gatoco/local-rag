#!/usr/bin/env python3
"""
Re-index all documents with new embedding model (BAAI/bge-large-en-v1.5).
Usage: python reindex.py [docs_dir]
"""

import os
import sys

from src.infrastructure.adapters.hf_embedding_adapter import HFEmbeddingAdapter
from src.infrastructure.adapters.chromadb_adapter import ChromaDBAdapter
from src.infrastructure.adapters.langchain_loader_adapter import LangChainLoaderAdapter


def reindex_directory(docs_dir: str = "./docs_to_ingest", collection_name: str = "local_rag_docs"):
    """Re-index all documents with new embeddings."""

    print("=" * 60)
    print("Re-Indexing con BAAI/bge-large-en-v1.5 (1024 dims)")
    print("=" * 60)

    print("\n[1/3] Loading embedding model...")
    embedding_adapter = HFEmbeddingAdapter(model_name="BAAI/bge-large-en-v1.5")
    print(f"  Model: {embedding_adapter.model_name}")

    print("\n[2/3] Initializing ChromaDB...")
    chroma_adapter = ChromaDBAdapter(
        embedding_port=embedding_adapter,
        persist_directory="./chroma_db",
        collection_name=collection_name
    )
    print(f"  Collection: {collection_name}")

    print("\n[3/3] Loading documents...")
    loader = LangChainLoaderAdapter(chunk_size=800, chunk_overlap=150)

    if not os.path.isdir(docs_dir):
        print(f"ERROR: Directory not found: {docs_dir}")
        return

    all_docs = loader.load_directory(docs_dir)
    print(f"  Loaded {len(all_docs)} chunks")

    if not all_docs:
        print("WARNING: No documents found to index")
        return

    print("\n[Indexing] Adding documents to ChromaDB...")
    chroma_adapter.add_documents(all_docs)

    count = chroma_adapter.vector_store._collection.count()
    print(f"\n[DONE] Indexed {count} documents")
    print("=" * 60)


if __name__ == "__main__":
    docs_dir = sys.argv[1] if len(sys.argv) > 1 else "./docs_to_ingest"
    reindex_directory(docs_dir)