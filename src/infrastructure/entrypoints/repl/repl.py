"""
Main REPL loop for local-rag.

Refactored to be minimal and opencode-like:
- Minimal prompt: "> "
- Status bar header
- Natural language command support
- Local/Cloud mode switching
"""

import readline
from pathlib import Path
from typing import Any

from .adapters.factory import get_default_local_model, get_llm_adapter
from .commands.help import ClearCommand, ExitCommand, HelpCommand
from .commands.mode import ModeCommand
from .commands.model import ModelCommand, ModelsCommand, ProviderCommand, ProvidersCommand
from .commands.rag import IndexCommand, RagCommand, StatsCommand
from .ui.console import Console
from .ui.statusbar import StatusBar


class REPL:
    """
    Refactored REPL with minimal opencode-like interface.

    Usage:
        repl = REPL()
        repl.run()
    """

    KNOWN_COMMANDS = ["mode", "provider", "model", "rag", "index", "help", "quit", "exit", "clear", "providers", "models", "stats", "h", "status"]

    def __init__(self) -> None:
        self.running = True
        self.console = Console()
        self.status_bar = StatusBar(self.console)

        self.mode = "cloud"
        self.provider = "minimax"
        self.model = "MiniMax-M2.7"
        self.rag_enabled = True
        self.rag_top_k = 5
        self.local_model = "none"
        self.collection_count = 0

        self._chroma_collection = None
        self._llm_adapter = None
        self._local_llm_adapter = None

        self._setup_readline()
        self._init_chroma()
        self._update_status()

    def _update_status(self) -> None:
        """Update status bar with current state."""
        self.status_bar.update(
            mode=self.mode,
            provider=self.provider,
            model=self.model,
            rag_enabled=self.rag_enabled,
            docs_count=self.collection_count,
            local_model=self.local_model,
        )

    def _init_chroma(self) -> None:
        """Initialize ChromaDB connection."""
        try:
            import chromadb
            from chromadb.config import Settings

            chroma_db_dir = Path(__file__).parent.parent.parent.parent.parent / "chroma_db"
            client = chromadb.PersistentClient(
                path=str(chroma_db_dir),
                settings=Settings(anonymized_telemetry=False)
            )
            self._chroma_collection = client.get_collection(name="local_rag_docs")
            self.collection_count = self._chroma_collection.count()
        except Exception as e:
            self.console.print_warning(f"ChromaDB not available: {e}")

    def _get_adapter(self):
        """Get or create LLM adapter based on current mode."""
        if self.mode == "local":
            if self._local_llm_adapter is None:
                from .adapters.factory import get_llm_adapter
                self._local_llm_adapter = get_llm_adapter("local")
                self.local_model = get_default_local_model() or "unknown"
            return self._local_llm_adapter
        else:
            if self._llm_adapter is None:
                from .adapters.factory import get_llm_adapter
                self._llm_adapter = get_llm_adapter("cloud", self.provider, self.model)
            return self._llm_adapter

    def _get_context(self) -> dict[str, Any]:
        """Get context for command execution."""
        return {
            "mode": self.mode,
            "provider": self.provider,
            "model": self.model,
            "rag_enabled": self.rag_enabled,
            "rag_top_k": self.rag_top_k,
            "collection_count": self.collection_count,
            "local_model": self.local_model,
            "commands": {},  # For compatibility with help command
        }

    def _update_context(self, updates: dict[str, Any]) -> None:
        """Update state from command result."""
        if "mode" in updates:
            new_mode = updates["mode"]
            if new_mode != self.mode:
                self.mode = new_mode
                self._llm_adapter = None
                if new_mode == "local":
                    self._load_local_model()
                else:
                    self._local_llm_adapter = None

        if "provider" in updates:
            self.provider = updates["provider"]
            self._llm_adapter = None

        if "model" in updates:
            self.model = updates["model"]
            self._llm_adapter = None

        if "rag_enabled" in updates:
            self.rag_enabled = updates["rag_enabled"]

        if "rag_top_k" in updates:
            self.rag_top_k = updates["rag_top_k"]

        if "local_model" in updates:
            self.local_model = updates["local_model"]

        self._update_status()

    def _load_local_model(self) -> None:
        """Load local llama.cpp model."""
        try:
            self.console.print_info("Loading local model...")
            self._local_llm_adapter = get_llm_adapter("local")
            self.local_model = get_default_local_model() or "unknown"
            self.console.print_success(f"Local model loaded: {self.local_model.split('/')[-1]}")
        except Exception as e:
            self.console.print_error(f"Failed to load local model: {e}")
            self.mode = "cloud"
            self._llm_adapter = None

    def _setup_readline(self) -> None:
        """Enable readline features."""
        readline.parse_and_bind("tab: complete")
        readline.parse_and_bind("set editing-mode vi")

    def _parse_input(self, line: str) -> tuple[bool, dict[str, Any]]:
        """
        Parse user input to determine if it's a command or query.

        Returns:
            (is_query, command_data)
            - is_query: True if text should be sent to LLM
            - command_data: dict with 'command' and 'args' if a command
        """
        line = line.strip()
        if not line:
            return False, {}

        first_word = line.lower().split()[0]

        if first_word.startswith("/"):
            cmd_name = first_word[1:]
            args = line.split()[1:]
            return False, {"command": cmd_name, "args": args}

        if first_word in self.KNOWN_COMMANDS and len(line.split()) <= 2:
            parts = line.lower().split()
            return False, {"command": parts[0], "args": parts[1:] if len(parts) > 1 else []}

        return True, {}

    def _handle_command(self, command: str, args: list[str]) -> tuple[bool, dict[str, Any], str]:
        """
        Execute a command and return result.

        Returns:
            (handled, data, message)
        """
        cmd_map = {
            "help": HelpCommand(),
            "?": HelpCommand(),
            "exit": ExitCommand(),
            "quit": ExitCommand(),
            "clear": ClearCommand(),
            "providers": ProvidersCommand(),
            "provider": ProviderCommand(),
            "models": ModelsCommand(),
            "model": ModelCommand(),
            "rag": RagCommand(),
            "index": IndexCommand(),
            "stats": StatsCommand(),
            "status": StatsCommand(),
            "mode": ModeCommand(),
            "m": ModeCommand(),
        }

        if command not in cmd_map:
            return False, {}, f"Unknown command: {command}"

        cmd = cmd_map[command]
        context = self._get_context()
        result = cmd.execute(args, context)

        if result.data:
            self._update_context(result.data)

        return True, result.data if result.data else {}, result.message

    def _search_chroma(self, query: str, k: int = 3) -> list[dict[str, Any]]:
        """Search ChromaDB for similar documents."""
        if not self._chroma_collection:
            return []

        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            embeddings = HuggingFaceEmbeddings(
                model_name="BAAI/bge-large-en-v1.5",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True, "batch_size": 32}
            )
            query_emb = embeddings.embed_query(query)
            results = self._chroma_collection.query(
                query_embeddings=[query_emb],
                n_results=k,
                include=["documents", "metadatas"]
            )
            docs = []
            if results and results.get("documents"):
                for i, doc in enumerate(results["documents"][0]):
                    meta = results.get("metadatas", [[{}]])[0][i] if results.get("metadatas") else {}
                    docs.append({"content": doc, "metadata": meta})
            return docs
        except Exception as e:
            self.console.print_error(f"ChromaDB error: {e}")
            return []

    def _build_rag_context(self, question: str) -> tuple[str, list[str]]:
        """Build context from ChromaDB for RAG query."""
        is_comparative = any(kw in question.lower() for kw in [
            "mas importante", "mejor", "diferencia", "compar", "vs", "versus",
            "heaviest", "tallest", "best", "worst", "most", "least"
        ])
        k = 15 if is_comparative else self.rag_top_k

        docs = self._search_chroma(question, k=k)
        if not docs:
            return "", []

        context_parts = []
        sources = []
        for doc in docs:
            content = doc["content"][:1500]
            context_parts.append(content)
            source = doc["metadata"].get("source", "unknown")
            sources.append(source)

        context = "\n\n".join(context_parts)
        return context, sources

    def _stream_chat(self, prompt: str) -> None:
        """Send chat with streaming output."""
        try:
            adapter = self._get_adapter()

            if self.rag_enabled and self._chroma_collection:
                context, sources = self._build_rag_context(prompt)

                if context:
                    full_prompt = f"""Contexto de documentos:
{context}

Pregunta: {prompt}

Responde de forma directa, sin bloques de pensamiento. Usa SOLO la información del contexto. Si no hay suficiente información, di 'No tengo información suficiente en los documentos'."""

                    self.console.print_dim(f"[Sources: {', '.join(sources[:3])}]")
                    self.console.print()

                    full_response = ""
                    for token in adapter.generate_stream(full_prompt, max_tokens=1024):
                        print(token, end="", flush=True)
                        full_response += token
                    print()
                    return
                else:
                    self.console.print_warning("No documents found in RAG. Falling back to chat mode.")

            full_response = ""
            for token in adapter.generate_stream(prompt, max_tokens=1024):
                print(token, end="", flush=True)
                full_response += token
            print()

        except Exception as e:
            self.console.print_error(f"Error: {e}")

    def _print_welcome(self) -> None:
        """Print welcome banner and status."""
        self.console.console.print()
        self.status_bar.print()
        self.console.console.print()
        self.console.print_dim("Type /help for commands or ask a question")
        self.console.console.print()

    def run(self) -> None:
        """Main REPL loop."""
        self._print_welcome()

        while self.running:
            try:
                line = input("> ").strip()

                if not line:
                    continue

                is_query, cmd_data = self._parse_input(line)

                if not is_query:
                    handled, data, msg = self._handle_command(cmd_data["command"], cmd_data["args"])

                    if msg:
                        self.console.console.print(msg)

                    if data.get("exit"):
                        break

                    if not handled:
                        self.console.print_error(msg if msg else "Unknown command")

                    continue

                self._stream_chat(line)

            except KeyboardInterrupt:
                self.console.console.print("\n[dim](Use /exit to quit)[/dim]")
                continue
            except EOFError:
                self.console.console.print("\n[cyan]Goodbye![/cyan]")
                break

        self.console.console.print("[dim]Session ended.[/dim]")


def run_repl() -> None:
    """Entry point."""
    from dotenv import load_dotenv

    env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    repl = REPL()
    repl.run()


if __name__ == "__main__":
    run_repl()
