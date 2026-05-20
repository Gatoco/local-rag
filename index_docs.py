#!/usr/bin/env python3
"""
Index documents to ChromaDB with BGE-Large embeddings.
Usage: python index_docs.py [docs_dir]

Example: python index_docs.py ./docs_to_ingest
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.infrastructure.adapters.hf_embedding_adapter import HFEmbeddingAdapter
from src.infrastructure.adapters.chromadb_adapter import ChromaDBAdapter
from src.infrastructure.adapters.langchain_loader_adapter import LangChainLoaderAdapter


def main():
    docs_dir = sys.argv[1] if len(sys.argv) > 1 else "./docs_to_ingest"
    
    print("=" * 60)
    print("INDEXING DOCUMENTS")
    print("=" * 60)
    print(f"Directory: {docs_dir}")
    print(f"Model: BAAI/bge-large-en-v1.5 (1024 dims)")
    print("=" * 60)
    
    if not os.path.isdir(docs_dir):
        print(f"ERROR: Directory not found: {docs_dir}")
        return
    
    print("\n[1/3] Loading embedding model...")
    emb = HFEmbeddingAdapter()
    print(f"      Model: {emb.model_name}")
    
    print("\n[2/3] Loading documents...")
    loader = LangChainLoaderAdapter(chunk_size=800, chunk_overlap=150)
    docs = loader.load_directory(docs_dir)
    print(f"      Loaded {len(docs)} chunks")
    
    if not docs:
        print("WARNING: No documents found!")
        return
    
    print("\n[3/3] Indexing to ChromaDB...")
    chroma = ChromaDBAdapter(
        embedding_port=emb,
        persist_directory="./chroma_db",
        collection_name="local_rag_docs"
    )
    chroma.add_documents(docs)
    count = chroma.vector_store._collection.count()
    
    print("\n" + "=" * 60)
    print(f"DONE! Indexed {count} documents")
    print(f"DB location: ./chroma_db")
    print("=" * 60)


if __name__ == "__main__":
    main()