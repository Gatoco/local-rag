"""
read_file tool - Lee archivos del proyecto con soporte para rangos de líneas.
"""

from pathlib import Path
from typing import Any

from mcp.types import Tool, TextContent


PROJECT_ROOT = Path(__file__).parent.parent.parent


def _read_file_impl(arguments: dict[str, Any]) -> dict[str, Any]:
    """Implementación de read_file."""
    file_path = arguments.get("path", "")
    start_line = arguments.get("start_line", 1)
    end_line = arguments.get("end_line")
    max_lines = arguments.get("max_lines", 200)

    # Seguridad: solo permitir archivos dentro del proyecto
    try:
        full_path = (PROJECT_ROOT / file_path).resolve()
        if not str(full_path).startswith(str(PROJECT_ROOT.resolve())):
            return {"error": "Path outside project not allowed"}
    except Exception:
        return {"error": f"Invalid path: {file_path}"}

    if not full_path.exists():
        return {"error": f"File not found: {file_path}"}

    if not full_path.is_file():
        return {"error": f"Not a file: {file_path}"}

    try:
        lines = full_path.read_text(encoding="utf-8", errors="replace").split("\n")
    except Exception as e:
        return {"error": f"Cannot read file: {e}"}

    total_lines = len(lines)

    # Si no se especifica end_line, limitar a max_lines
    if end_line is None:
        end_line = min(start_line + max_lines - 1, total_lines)

    # Validar rango
    if start_line < 1:
        start_line = 1
    if end_line > total_lines:
        end_line = total_lines
    if start_line > end_line:
        return {"error": f"start_line ({start_line}) > end_line ({end_line})"}

    snippet = "\n".join(lines[start_line - 1:end_line])

    return {
        "path": str(full_path.relative_to(PROJECT_ROOT)),
        "total_lines": total_lines,
        "start_line": start_line,
        "end_line": end_line,
        "content": snippet,
        "truncated": end_line - start_line + 1 > max_lines,
    }


def get_read_file_tool() -> list[Tool]:
    return [
        Tool(
            name="read_file",
            description="""Lee el contenido de un archivo del proyecto.

Útil para:
- Ver el contenido de un archivo antes de editarlo
- Entender qué hace una función o clase
- Revisar un archivo de test

El path es relativo a la raíz del proyecto. Puedes especificar un rango de líneas
con start_line y end_line para leer solo una porción del archivo.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path al archivo relativo a la raíz del proyecto (ej: src/infrastructure/adapters/chromadb_adapter.py)",
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "Línea inicial (1-indexed). Default: 1",
                        "default": 1,
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "Línea final (inclusive). Si no se especifica, lee hasta start_line + max_lines.",
                    },
                    "max_lines": {
                        "type": "integer",
                        "description": "Máximo de líneas a leer si end_line no está especificado. Default: 200",
                        "default": 200,
                    },
                },
                "required": ["path"],
            },
        ),
    ]


async def handle_read_file(arguments: dict[str, Any]) -> list[TextContent]:
    result = _read_file_impl(arguments)
    if "error" in result:
        return [TextContent(type="text", text=f"Error: {result['error']}")]

    r = result
    output = [
        f"📄 {r['path']} ({r['total_lines']} líneas)",
        f"Mostrando líneas {r['start_line']}–{r['end_line']}" +
        (f" (truncado a {r['max_lines']} líneas)" if r.get("truncated") else ""),
        "",
        "```",
        r["content"],
        "```",
    ]
    return [TextContent(type="text", text="\n".join(output))]
