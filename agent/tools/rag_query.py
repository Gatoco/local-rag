"""
rag_query tool - Búsqueda semántica sobre el código fuente indexado.

Usa chromadb directo con embeddings de langchain para buscar código
por significado, no solo palabras clave.
"""

import os
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).parent.parent.parent
CHROMA_DB_DIR = PROJECT_ROOT / "chroma_db"
CODE_COLLECTION = "codebase_index"
EMBEDDING_MODEL = os.environ.get("CODE_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

from mcp.types import Tool, TextContent


def _get_embedding_fn():
    """Computa embeddings con langchain."""
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True, "batch_size": 32},
    )


def _rag_query_impl(arguments: dict[str, Any]) -> dict[str, Any]:
    """Implementación de búsqueda semántica."""
    query = arguments.get("query", "").strip()
    top_k = arguments.get("top_k", 5)
    filter_lang = arguments.get("language")

    if not query:
        return {"error": "query is required"}

    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
        collection = client.get_collection(CODE_COLLECTION)

        embed_fn = _get_embedding_fn()
        query_embedding = embed_fn.embed_query(query)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        output = []
        for i in range(len(results["ids"][0])):
            meta = results["metadatas"][0][i] or {}
            lang = meta.get("language", "")
            if filter_lang and lang != filter_lang:
                continue
            output.append({
                "file": meta.get("file", ""),
                "language": lang,
                "type": meta.get("type", ""),
                "name": meta.get("name", ""),
                "line": meta.get("line", 0),
                "line_start": meta.get("line_start", 0),
                "chunk_type": meta.get("chunk_type", "text"),
                "score": float(results["distances"][0][i]),
                "content": results["documents"][0][i][:600],
            })

        return {
            "query": query,
            "total": len(output),
            "results": output,
        }

    except Exception as e:
        return {
            "error": f"RAG query failed: {e}",
            "hint": "Ejecuta 'python -m agent.code_indexer --reindex' para crear el índice",
        }


def get_rag_query_tool() -> list[Tool]:
    return [
        Tool(
            name="rag_query",
            description="""Búsqueda semántica sobre el código fuente del proyecto.

Usa embeddings para encontrar código relevante por SIGNIFICADO,
no solo palabras exactas.

Útil para:
- "encontrar dónde se valida el token JWT" → encuentra auth.py
- "dónde está la clase que maneja ChromaDB" → encuentra adapters
- "dónde se hace el rate limiting" → encuentra rate_limiter.py
- "cómo funciona la indexación de documentos" → encuentra loaders

Ejemplo:
  query: "dónde se validan las dependencias del sistema"
  top_k: 5""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Pregunta en lenguaje natural sobre el código",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Número de resultados a devolver. Default: 5",
                        "default": 5,
                    },
                    "language": {
                        "type": "string",
                        "description": "Filtrar por lenguaje (ej: python, javascript). Opcional.",
                    },
                },
                "required": ["query"],
            },
        ),
    ]


async def handle_rag_query(arguments: dict[str, Any]) -> list[TextContent]:
    result = _rag_query_impl(arguments)

    if "error" in result:
        hint = f"\n💡 {result.get('hint', '')}" if result.get("hint") else ""
        return [TextContent(type="text", text=f"Error: {result['error']}{hint}")]

    r = result
    if not r["results"]:
        return [TextContent(
            type="text",
            text=f"🔍 Sin resultados semánticos para: '{r['query']}'. "
                 "El índice puede estar vacío. "
                 "Ejecuta: python -m agent.code_indexer --reindex"
        )]

    lines = [
        f"🧠 **RAG: {r['query']}** ({r['total']} resultados)",
        "",
    ]

    for i, res in enumerate(r["results"], 1):
        score_bar = "█" * int((1 - res["score"]) * 10) + "░" * int(res["score"] * 10)
        type_info = f"[{res['chunk_type']}"
        if res.get("type"):
            type_info += f" {res['type']}"
        if res.get("name"):
            type_info += f" {res['name']}"
        type_info += "]"

        lines.append(f"--- Resultado {i}/{r['total']} {score_bar} {type_info} ---")
        lines.append(f"📄 {res['file']}" +
                     (f":{res['line']}" if res.get("line") else
                      f":L{res['line_start']}" if res.get("line_start") else ""))
        lines.append("```")
        lines.append(res["content"][:400])
        lines.append("```")
        lines.append("")

    return [TextContent(type="text", text="\n".join(lines))]
