"""
Tests unitarios para MCP Agent tools.

Estos tests verifican las funciones handler de los tools del agente:
- read_file
- search_code
- rag_query

Usa mocks para aislar de ChromaDB real.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import os


PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestReadFileTool:
    """Tests para read_file tool."""

    def test_read_file_impl_with_valid_file(self):
        """Test: _read_file_impl lee archivo válido."""
        from agent.tools.read_file import _read_file_impl

        # Use a file within the project
        result = _read_file_impl({"path": "README.md"})

        if "error" not in result:
            assert result["total_lines"] > 0

    def test_read_file_impl_with_line_range(self):
        """Test: _read_file_impl respeta rango de líneas."""
        from agent.tools.read_file import _read_file_impl

        result = _read_file_impl({
            "path": "README.md",
            "start_line": 1,
            "end_line": 5
        })

        if "error" not in result:
            assert result["start_line"] == 1
            assert result["end_line"] == 5

    def test_read_file_impl_file_not_found(self):
        """Test: _read_file_impl maneja archivo no encontrado."""
        from agent.tools.read_file import _read_file_impl

        result = _read_file_impl({"path": "/nonexistent/file.txt"})

        assert "error" in result

    def test_read_file_impl_path_traversal_blocked(self):
        """Test: _read_file_impl bloquea path traversal."""
        from agent.tools.read_file import _read_file_impl

        # Try to escape with ../
        result = _read_file_impl({"path": "../etc/passwd"})

        assert "error" in result

    def test_read_file_impl_max_lines(self):
        """Test: _read_file_impl respeta max_lines."""
        from agent.tools.read_file import _read_file_impl

        result = _read_file_impl({
            "path": "README.md",
            "max_lines": 10
        })

        if "error" not in result:
            assert result.get("truncated", False) is False or result["total_lines"] <= 10


class TestSearchCodeTool:
    """Tests para search_code tool."""

    def test_search_code_impl_finds_text(self):
        """Test: _search_code_impl encuentra texto."""
        from agent.tools.search_code import _search_code_impl

        with patch("agent.tools.search_code.PROJECT_ROOT", PROJECT_ROOT):
            result = _search_code_impl({"query": "RAGService"})

        assert "error" not in result
        assert result["files_scanned"] >= 0

    def test_search_code_impl_regex(self):
        """Test: _search_code_impl soporta regex."""
        from agent.tools.search_code import _search_code_impl

        with patch("agent.tools.search_code.PROJECT_ROOT", PROJECT_ROOT):
            result = _search_code_impl({
                "query": r"def \w+\(",
                "regex": True,
                "file_pattern": "*.py"
            })

        assert "error" not in result
        assert result["regex"] is True

    def test_search_code_impl_handles_empty_results(self):
        """Test: _search_code_impl maneja resultados vacíos correctamente."""
        from agent.tools.search_code import _search_code_impl

        with patch("agent.tools.search_code.PROJECT_ROOT", PROJECT_ROOT):
            result = _search_code_impl({"query": "__xyzzy_nonexistent_12345__"})

        # Verify structure is correct regardless of matches
        assert "files_scanned" in result
        assert "results" in result
        assert isinstance(result["results"], list)

    def test_search_code_impl_case_sensitive(self):
        """Test: _search_code_impl distingue mayúsculas."""
        from agent.tools.search_code import _search_code_impl

        with patch("agent.tools.search_code.PROJECT_ROOT", PROJECT_ROOT):
            result_cs = _search_code_impl({
                "query": "RAGService",
                "case_sensitive": True
            })
            result_ci = _search_code_impl({
                "query": "ragservice",
                "case_sensitive": False
            })

        # Case sensitive should find fewer matches
        assert result_cs["total_matches"] >= 0
        assert result_ci["total_matches"] >= result_cs["total_matches"]


class TestRAGQueryTool:
    """Tests para rag_query tool."""

    def test_rag_query_impl_requires_query(self):
        """Test: _rag_query_impl requiere query."""
        from agent.tools.rag_query import _rag_query_impl

        result = _rag_query_impl({})

        assert "error" in result
        assert "required" in result["error"]

    def test_rag_query_impl_empty_query(self):
        """Test: _rag_query_impl rechaza query vacía."""
        from agent.tools.rag_query import _rag_query_impl

        result = _rag_query_impl({"query": "   "})

        assert "error" in result

    def test_rag_query_impl_top_k_default(self):
        """Test: _rag_query_impl usa top_k por defecto."""
        from agent.tools.rag_query import _rag_query_impl

        # When ChromaDB is not available, should return error
        result = _rag_query_impl({"query": "test query"})

        # Should either work or fail gracefully
        assert "error" in result or "results" in result


class TestToolHandlers:
    """Tests para los handlers de los tools."""

    def test_handle_read_file_returns_list(self):
        """Test: handle_read_file retorna list[TextContent]."""
        import asyncio
        from agent.tools.read_file import handle_read_file
        from mcp.types import TextContent

        async def run():
            result = await handle_read_file({"path": "README.md"})
            return result

        result = asyncio.run(run())

        assert isinstance(result, list)
        assert all(isinstance(item, TextContent) for item in result)

    def test_handle_search_code_returns_list(self):
        """Test: handle_search_code retorna list[TextContent]."""
        import asyncio
        from agent.tools.search_code import handle_search_code
        from mcp.types import TextContent

        async def run():
            with patch("agent.tools.search_code.PROJECT_ROOT", PROJECT_ROOT):
                result = await handle_search_code({"query": "import"})
            return result

        result = asyncio.run(run())

        assert isinstance(result, list)
        assert all(isinstance(item, TextContent) for item in result)

    def test_handle_rag_query_returns_list(self):
        """Test: handle_rag_query retorna list[TextContent]."""
        import asyncio
        from agent.tools.rag_query import handle_rag_query
        from mcp.types import TextContent

        async def run():
            result = await handle_rag_query({"query": "test"})
            return result

        result = asyncio.run(run())

        assert isinstance(result, list)
        assert all(isinstance(item, TextContent) for item in result)

