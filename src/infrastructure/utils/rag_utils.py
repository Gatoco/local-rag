"""
RAG utilities - Lógica compartida para ChromaDB y búsqueda semántica.

Evita duplicación entre REPL, CloudChat y MCP tools.
"""

import os
from pathlib import Path
from typing import Any

from langchain_huggingface import HuggingFaceEmbeddings


def get_chroma_db_path(project_root: Path | None = None) -> Path:
    """Obtiene la ruta de chroma_db."""
    if project_root is None:
        project_root = Path(__file__).parent.parent.parent.parent
    return project_root / "chroma_db"


def get_embedding_model():
    """Obtiene el modelo de embeddings (BGE-Large para producción)."""
    return HuggingFaceEmbeddings(
        model_name="BAAI/bge-large-en-v1.5",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True, "batch_size": 32},
    )


def get_code_embedding_model():
    """Obtiene el modelo de embeddings para código (MiniLM para el codebase index)."""
    return HuggingFaceEmbeddings(
        model_name=os.environ.get(
            "CODE_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        ),
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True, "batch_size": 16},
    )


def search_chroma(
    chroma_collection,
    query: str,
    embedding_model: HuggingFaceEmbeddings,
    k: int = 4,
    include_metadata: bool = True,
) -> list[dict[str, Any]]:
    """
    Busca documentos similares en ChromaDB.

    Args:
        chroma_collection: Colección de ChromaDB
        query: Query text
        embedding_model: Modelo de embeddings a usar
        k: Número de resultados
        include_metadata: Incluir metadatos

    Returns:
        Lista de dicts con 'content' y 'metadata'
    """
    try:
        query_embedding = embedding_model.embed_query(query)
        results = chroma_collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas"] if include_metadata else ["documents"],
        )
        docs = []
        if results and results.get("documents"):
            for i, doc in enumerate(results["documents"][0]):
                metadata = (
                    results.get("metadatas", [[{}]])[0][i] if results.get("metadatas") else {}
                )
                docs.append({"content": doc, "metadata": metadata})
        return docs
    except Exception as e:
        return []


def build_rag_prompt(question: str, context_docs: list[dict[str, Any]], max_chars: int = 1500) -> str:
    """
    Construye un prompt RAG con el contexto.

    Args:
        question: Pregunta del usuario
        context_docs: Documentos retrieved
        max_chars: Máximo de caracteres por documento

    Returns:
        Prompt formateado
    """
    if not context_docs:
        return f"Pregunta: {question}\n\nResponde basándote únicamente en tu conocimiento."

    context_parts = []
    sources = []
    for doc in context_docs:
        content = doc["content"][:max_chars]
        context_parts.append(content)
        source = doc["metadata"].get("source", "unknown")
        if source not in sources:
            sources.append(source)

    context = "\n\n".join(context_parts)

    prompt = f"""Contexto de documentos:
{context}

Pregunta: {question}

Responde de forma directa, sin bloques de pensamiento. Usa SOLO la información del contexto. Si no hay suficiente información, indica que no tienes esa información en los documentos."""
    return prompt, sources
