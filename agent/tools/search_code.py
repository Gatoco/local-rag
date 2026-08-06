"""
search_code tool - Búsqueda por patrón (grep-like) en el código fuente.
"""

import re
from pathlib import Path
from typing import Any

from mcp.types import Tool, TextContent


PROJECT_ROOT = Path(__file__).parent.parent.parent


EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java", ".c", ".cpp",
              ".h", ".cs", ".rb", ".php", ".swift", ".kt", ".md", ".yaml", ".yml",
              ".sh", ".bash", ".sql", ".html", ".css"}


def _search_code_impl(arguments: dict[str, Any]) -> list[dict[str, Any]]:
    """Implementación de búsqueda por patrón."""
    query = arguments.get("query", "").strip()
    case_sensitive = arguments.get("case_sensitive", False)
    regex = arguments.get("regex", False)
    file_pattern = arguments.get("file_pattern", "*.py")
    max_results = arguments.get("max_results", 50)

    if not query:
        return [{"error": "query is required"}]

    try:
        flags = 0 if case_sensitive else re.IGNORECASE
        if regex:
            pattern = re.compile(query, flags)
        else:
            pattern = re.compile(re.escape(query), flags)
    except re.error as e:
        return [{"error": f"Invalid regex: {e}"}]

    # Resolver file pattern a extensiones
    glob_pattern = file_pattern.replace(".", "\\.").replace("*", ".*")
    try:
        file_regex = re.compile(glob_pattern, re.IGNORECASE)
    except re.error:
        file_regex = re.compile(".*\\.py", re.IGNORECASE)

    results = []
    files_scanned = 0

    skip_dirs = {"__pycache__", ".pytest_cache", ".ruff_cache", ".git", ".venv",
                 "node_modules", "dist", "build", ".eggs", "egg-info"}

    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file():
            continue

        # Filtrar por directorio
        if any(d in path.parts for d in skip_dirs):
            continue

        # Filtrar por extensión/patrón de archivo
        if not file_regex.search(path.suffix) and not file_regex.search(path.name):
            continue

        # Skip large files
        if path.stat().st_size > 5_000_000:
            continue

        files_scanned += 1

        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").split("\n")
        except Exception:
            continue

        for i, line in enumerate(lines, 1):
            if pattern.search(line):
                rel_path = str(path.relative_to(PROJECT_ROOT))
                results.append({
                    "file": rel_path,
                    "line": i,
                    "content": line.rstrip(),
                    "column": -1,
                })
                if len(results) >= max_results:
                    break

        if len(results) >= max_results:
            break

    return {
        "query": query,
        "regex": regex,
        "files_scanned": files_scanned,
        "total_matches": len(results),
        "results": results,
    }


def get_search_code_tool() -> list[Tool]:
    return [
        Tool(
            name="search_code",
            description="""Busca patrones de texto o regex en el código fuente.

Útil para:
- Encontrar dónde se usa una función o variable
- Buscar imports específicos
- Encontrar todos los archivos que usan cierta API
- Rastrear TODOs o FIXMEs

Ejemplos:
- query: "RAGService" (busca texto exacto)
- query: "def.*rag" regex:true (busca regex)
- query: "TODO" file_pattern: "*.py" (busca TODOs en Python)""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Texto o patrón regex a buscar",
                    },
                    "case_sensitive": {
                        "type": "boolean",
                        "description": "Si True, la búsqueda distingue mayúsculas. Default: False",
                        "default": False,
                    },
                    "regex": {
                        "type": "boolean",
                        "description": "Si True, trata query como expresión regular. Default: False",
                        "default": False,
                    },
                    "file_pattern": {
                        "type": "string",
                        "description": "Patrón glob para filtrar archivos (ej: *.py, *.js). Default: *.py",
                        "default": "*.py",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Máximo de resultados a devolver. Default: 50",
                        "default": 50,
                    },
                },
                "required": ["query"],
            },
        ),
    ]


async def handle_search_code(arguments: dict[str, Any]) -> list[TextContent]:
    result = _search_code_impl(arguments)

    if isinstance(result, list) and "error" in result[0]:
        return [TextContent(type="text", text=f"Error: {result[0]['error']}")]

    r = result
    if not r["results"]:
        return [TextContent(
            type="text",
            text=f"🔍 Sin resultados para '{r['query']}' "
                 f"(regex={r['regex']}, archivos escaneados: {r['files_scanned']})"
        )]

    lines = [
        f"🔍 **{r['query']}** ({r['total_matches']} matches en {r['files_scanned']} archivos)"
        f"{' (regex)' if r['regex'] else ''}",
        "",
    ]

    for match in r["results"][:20]:
        lines.append(f"  📄 {match['file']}:{match['line']}")
        lines.append(f"     {match['content'][:120]}")
        lines.append("")

    if r["total_matches"] > 20:
        lines.append(f"... y {r['total_matches'] - 20} más")

    return [TextContent(type="text", text="\n".join(lines))]
