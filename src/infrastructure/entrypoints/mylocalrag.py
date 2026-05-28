#!/usr/bin/env python3
"""
MyLocalRAG - RAG-powered CLI for cloud LLM chat.

Usage:
    python3 -m src.infrastructure.entrypoints.mylocalrag

Commands:
    /help, /?      Show help
    /exit, /quit   Exit
    /providers     List providers
    /provider <n>  Switch provider
    /models        List models
    /model <name>  Switch model
    /rag [on|off]  Toggle RAG mode
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.infrastructure.entrypoints.repl.repl import run_repl

if __name__ == "__main__":
    run_repl()
