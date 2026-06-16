#!/usr/bin/env python3
"""
MyLocalRAG - REPL Entry Point

Usage:
    python3 mylocalrag.py          # Run REPL
"""

from dotenv import load_dotenv
load_dotenv()

from src.infrastructure.entrypoints.repl.repl import run_repl

if __name__ == "__main__":
    run_repl()