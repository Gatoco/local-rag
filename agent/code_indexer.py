"""
Code Indexer - Indexa el código fuente en ChromaDB para búsqueda semántica.

Usa chromadb directo (no langchain) para garantizar persistencia correcta.

Uso:
    python -m agent.code_indexer --reindex --limit 20
    python -m agent.code_indexer --status
"""

import argparse
import ast
import os
from pathlib import Path
from typing import Any

from langchain_core.documents import Document

PROJECT_ROOT = Path(__file__).parent.parent
CHROMA_DB_DIR = PROJECT_ROOT / "chroma_db"
CODE_COLLECTION = "codebase_index"
EMBEDDING_MODEL = os.environ.get("CODE_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")


class CodeChunker:
    """Extrae y chunkea código fuente Python intelligently."""

    LANGUAGE_EXTENSIONS = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".cs": "csharp",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".md": "markdown",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".json": "json",
        ".toml": "toml",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "bash",
        ".sql": "sql",
        ".html": "html",
        ".css": "css",
        ".scss": "scss",
    }

    def __init__(self, chunk_size: int = 80, chunk_overlap: int = 20):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def should_index(self, path: Path) -> bool:
        """Decide si un archivo debe ser indexado."""
        path_str = str(path)
        skip_dirs = {
            "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache",
            ".git", ".venv", "node_modules", "dist", "build", ".eggs",
            "egg-info", ".tox", ".nox", "venv", "env",
        }
        skip_patterns = {
            "test_", "_test.", ".min.js", ".bundle.js",
            "package-lock.json", "yarn.lock", "poetry.lock",
        }
        parts = path.parts
        if any(d in skip_dirs for d in parts):
            return False
        if any(p in path_str for p in skip_patterns):
            return False
        if path.stat().st_size > 2_000_000:
            return False
        return True

    def extract_python_defs(self, content: str, file_path: str) -> list[dict[str, Any]]:
        """Extrae definiciones de clases y funciones de Python."""
        items = []
        try:
            tree = ast.parse(content, filename=file_path)
            for node in ast.walk(tree):
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    line = node.lineno
                    name = node.name
                    type_ = type(node).__name__
                    lines = content.split("\n")
                    start = max(0, line - 1)
                    end = min(len(lines), start + 50)
                    snippet = "\n".join(lines[start:end])
                    items.append({
                        "type": type_,
                        "name": name,
                        "line": line,
                        "snippet": snippet,
                        "file": file_path,
                    })
        except SyntaxError:
            pass
        return items

    def chunk_file(self, path: Path) -> list[Document]:
        """Chunkea un archivo en documentos para ChromaDB."""
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return []

        lang = self.LANGUAGE_EXTENSIONS.get(path.suffix.lower(), "text")
        file_path = str(path)
        documents = []

        if path.suffix == ".py":
            defs = self.extract_python_defs(content, file_path)
            for def_ in defs:
                doc_id = f"{file_path}:{def_['name']}:{def_['type']}"
                metadata = {
                    "file": file_path,
                    "language": lang,
                    "type": def_["type"],
                    "name": def_["name"],
                    "line": def_["line"],
                    "chunk_type": "definition",
                }
                documents.append(Document(
                    page_content=f"// {def_['type']} {def_['name']}\n{def_['snippet']}",
                    metadata=metadata,
                    id=doc_id,
                ))

        if not documents:
            lines = content.split("\n")
            for i in range(0, len(lines), self.chunk_overlap):
                chunk_lines = lines[i:i + self.chunk_size]
                if not chunk_lines:
                    continue
                chunk_text = "\n".join(chunk_lines)
                doc_id = f"{file_path}:L{i + 1}"
                metadata = {
                    "file": file_path,
                    "language": lang,
                    "line_start": i + 1,
                    "line_end": min(i + self.chunk_size, len(lines)),
                    "chunk_type": "text",
                }
                documents.append(Document(
                    page_content=chunk_text,
                    metadata=metadata,
                    id=doc_id,
                ))

        return documents

    def walk_and_chunk(self, root: Path, max_files: int = 0) -> list[Document]:
        """Itera sobre todos los archivos fuente y los chunkea."""
        all_docs = []
        files_seen = 0
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if not self.should_index(path):
                continue
            docs = self.chunk_file(path)
            all_docs.extend(docs)
            files_seen += 1
            if max_files > 0 and files_seen >= max_files:
                break
        return all_docs


def get_embedding_fn():
    """Computa embeddings usando langchain."""
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True, "batch_size": 32},
    )


def get_collection():
    """Obtiene o crea la colección de código."""
    client = __import__("chromadb").PersistentClient(path=str(CHROMA_DB_DIR))
    try:
        client.delete_collection(CODE_COLLECTION)
    except Exception:
        pass
    return client.create_collection(CODE_COLLECTION, get_or_create=True)


def index_codebase(reindex: bool = False, max_files: int = 0, verbose: bool = True):
    """Indexa el código fuente."""
    if verbose:
        print(f"Indexando: {PROJECT_ROOT}")
        print(f"Modelo: {EMBEDDING_MODEL}")
        if max_files > 0:
            print(f"Límite: {max_files} archivos")

    indexer = CodeChunker(chunk_size=80, chunk_overlap=20)
    documents = indexer.walk_and_chunk(PROJECT_ROOT, max_files=max_files)

    if not documents:
        if verbose:
            print("No se encontraron archivos.")
        return

    if verbose:
        print(f"Chunks: {len(documents)}")

    collection = get_collection()

    if verbose:
        print("Computando embeddings...")

    embed_fn = get_embedding_fn()
    texts = [doc.page_content for doc in documents]
    embeddings = embed_fn.embed_documents(texts)

    if verbose:
        print("Añadiendo a ChromaDB...")

    ids = [doc.id for doc in documents]
    metadatas = [doc.metadata for doc in documents]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    if verbose:
        print(f"✓ {collection.count()} chunks en '{CODE_COLLECTION}'")


def search_code(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Búsqueda por embedding similarity."""
    collection = __import__("chromadb").PersistentClient(
        path=str(CHROMA_DB_DIR)
    ).get_collection(CODE_COLLECTION)

    embed_fn = get_embedding_fn()
    query_embedding = embed_fn.embed_query(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    output = []
    for i in range(len(results["ids"][0])):
        meta = results["metadatas"][0][i] or {}
        output.append({
            "file": meta.get("file", ""),
            "language": meta.get("language", ""),
            "type": meta.get("type", ""),
            "name": meta.get("name", ""),
            "line": meta.get("line", 0),
            "line_start": meta.get("line_start", 0),
            "score": float(results["distances"][0][i]),
            "content": results["documents"][0][i][:500],
        })
    return output


def get_index_status() -> dict[str, Any]:
    """Estado del índice."""
    try:
        client = __import__("chromadb").PersistentClient(path=str(CHROMA_DB_DIR))
        collection = client.get_collection(CODE_COLLECTION)
        return {"indexed": True, "chunks": collection.count(), "collection": CODE_COLLECTION}
    except Exception as e:
        return {"indexed": False, "error": str(e), "chunks": 0}


def main():
    parser = argparse.ArgumentParser(description="Codebase Indexer")
    parser.add_argument("--reindex", action="store_true", help="Recrear índice")
    parser.add_argument("--status", action="store_true", help="Ver estado")
    parser.add_argument("--limit", type=int, default=0, help="Máx archivos (0=todos)")
    args = parser.parse_args()

    if args.status:
        s = get_index_status()
        print(f"Índice: {s.get('chunks')} chunks | {s.get('collection')}")
        if "error" in s:
            print(f"Error: {s['error']}")
        return

    index_codebase(reindex=args.reindex, max_files=args.limit)


if __name__ == "__main__":
    main()
