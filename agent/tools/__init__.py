"""
Agent Tools - MCP tools para el agente Navi-LocalRAG.
"""

from agent.tools.rag_query import get_rag_query_tool
from agent.tools.read_file import get_read_file_tool
from agent.tools.search_code import get_search_code_tool


def get_all_tools():
    """Retorna todas las tools del agente."""
    return [
        *get_read_file_tool(),
        *get_rag_query_tool(),
        *get_search_code_tool(),
    ]
