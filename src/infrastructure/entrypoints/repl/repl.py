"""
Main REPL loop for local-rag.

Refactored with OpenCode-inspired interface:
- Rich layout with header and messages
- Streaming markdown output
- Better keyboard shortcuts
- Cleaner status display
"""

import readline
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rich.panel import Panel

from .adapters.factory import get_default_local_model, get_llm_adapter
from .commands.help import ClearCommand, ExitCommand, HelpCommand
from .commands.mode import ModeCommand
from .commands.model import ModelCommand, ModelsCommand, ProviderCommand, ProvidersCommand
from .commands.rag import IndexCommand, RagCommand, StatsCommand
from .ui.console import Console
from .ui.layout import SimpleChatLayout
from .ui.themes import ThemeManager


@dataclass
class ChatMessage:
    """Represents a chat message with metadata."""

    role: str  # "user" or "assistant"
    content: str
    sources: list[str] | None = None


class REPL:
    """
    OpenCode-inspired REPL for local-rag.

    Features:
    - Rich terminal layout
    - Streaming markdown responses
    - Message history
    - Mode switching (local/cloud)
    - RAG toggle
    - Themes support
    """

    COMMANDS = {
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

    def __init__(self) -> None:
        self.running = True
        self.console = Console()
        self.theme_manager = ThemeManager()
        self.theme = self.theme_manager.current

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
        self._chat_history: list[ChatMessage] = []

        self._setup_readline()
        self._init_chroma()

    def _setup_readline(self) -> None:
        """Configure readline for better editing experience."""
        readline.parse_and_bind("tab: complete")
        readline.parse_and_bind("set editing-mode vi")
        readline.parse_and_bind("set show-all-if-ambiguous on")

    def _init_chroma(self) -> None:
        """Initialize ChromaDB connection."""
        try:
            import chromadb
            from chromadb.config import Settings

            chroma_db_dir = Path(__file__).parent.parent.parent.parent.parent / "chroma_db"
            client = chromadb.PersistentClient(
                path=str(chroma_db_dir), settings=Settings(anonymized_telemetry=False)
            )
            self._chroma_collection = client.get_collection(name="local_rag_docs")
            self.collection_count = self._chroma_collection.count()
        except Exception as e:
            self.console.print_dim(f"ChromaDB not available: {e}")

    def _get_adapter(self):
        """Get or create LLM adapter based on current mode."""
        if self.mode == "local":
            if self._local_llm_adapter is None:
                self._local_llm_adapter = get_llm_adapter("local")
                self.local_model = get_default_local_model() or "unknown"
            return self._local_llm_adapter
        else:
            if self._llm_adapter is None:
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
            "commands": {},
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

        if "exit" in updates:
            self.running = False

    def _load_local_model(self) -> None:
        """Load local llama.cpp model."""
        try:
            with self.console.status("[cyan]Loading local model...[/cyan]"):
                self._local_llm_adapter = get_llm_adapter("local")
                self.local_model = get_default_local_model() or "unknown"
            self.console.print_success(f"Local model: {self.local_model.split('/')[-1]}")
        except Exception as e:
            self.console.print_error(f"Failed to load local model: {e}")
            self.mode = "cloud"
            self._llm_adapter = None

    def _search_chroma(self, query: str, k: int = 3) -> list[dict[str, Any]]:
        """Search ChromaDB for similar documents."""
        if not self._chroma_collection:
            return []

        try:
            from langchain_huggingface import HuggingFaceEmbeddings

            embeddings = HuggingFaceEmbeddings(
                model_name="BAAI/bge-large-en-v1.5",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True, "batch_size": 32},
            )
            query_emb = embeddings.embed_query(query)
            results = self._chroma_collection.query(
                query_embeddings=[query_emb], n_results=k, include=["documents", "metadatas"]
            )
            docs = []
            if results and results.get("documents"):
                for i, doc in enumerate(results["documents"][0]):
                    meta = (
                        results.get("metadatas", [[{}]])[0][i] if results.get("metadatas") else {}
                    )
                    docs.append({"content": doc, "metadata": meta})
            return docs
        except Exception as e:
            self.console.print_error(f"ChromaDB error: {e}")
            return []

    def _build_rag_context(self, question: str) -> tuple[str, list[str]]:
        """Build context from ChromaDB for RAG query."""
        is_comparative = any(
            kw in question.lower()
            for kw in [
                "mas importante",
                "mejor",
                "diferencia",
                "compar",
                "vs",
                "versus",
                "heaviest",
                "tallest",
                "best",
                "worst",
                "most",
                "least",
            ]
        )
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

    def _handle_command(self, command: str, args: list[str]) -> tuple[bool, dict[str, Any], str]:
        """Execute a command and return result."""
        if command not in self.COMMANDS:
            return False, {}, f"Unknown command: {command}"

        cmd = self.COMMANDS[command]
        context = self._get_context()
        result = cmd.execute(args, context)

        if result.data:
            self._update_context(result.data)

        return True, result.data if result.data else {}, result.message

    def _parse_input(self, line: str) -> tuple[bool, dict[str, Any]]:
        """Parse user input to determine if it's a command or query."""
        line = line.strip()
        if not line:
            return False, {}

        first_word = line.lower().split()[0]

        if first_word.startswith("/"):
            cmd_name = first_word[1:]
            args = line.split()[1:]
            return False, {"command": cmd_name, "args": args}

        return True, {}

    def _stream_chat(self, prompt: str) -> None:
        """Send chat with streaming output."""
        try:
            adapter = self._get_adapter()
            sources = []

            if self.rag_enabled and self._chroma_collection:
                context, sources = self._build_rag_context(prompt)

                if context:
                    full_prompt = f"""Contexto de documentos:
{context}

Pregunta: {prompt}

Responde de forma directa, sin bloques de pensamiento. Usa SOLO la información del contexto. Si no hay suficiente información, di 'No tengo información suficiente en los documentos'."""

                    if sources:
                        self.console.print_dim(f"Sources: {', '.join(sources[:3])}")
                    self.console.print()

                    for token in adapter.generate_stream(full_prompt, max_tokens=1024):
                        print(token, end="", flush=True)
                    print()
                    return
                else:
                    self.console.print_warning(
                        "No documents found in RAG. Falling back to chat mode."
                    )

            for token in adapter.generate_stream(prompt, max_tokens=1024):
                print(token, end="", flush=True)
            print()

        except Exception as e:
            self.console.print_error(f"Error: {e}")

    def _print_welcome(self) -> None:
        """Print welcome message and header."""
        self.console.console.print()

    def _print_header(self) -> None:
        """Print the status header."""
        layout = SimpleChatLayout(self.console.console, self.theme)
        layout.render_header(
            mode=self.mode,
            provider=self.provider,
            model=self.model,
            rag_enabled=self.rag_enabled,
            docs_count=self.collection_count,
        )

    def _print_prompt(self) -> None:
        """Print the input prompt."""
        self.console.console.print()

    def run(self) -> None:
        """Main REPL loop."""
        self._print_welcome()
        self._print_header()
        self.console.console.print("[dim]Type /help for commands or ask a question[/dim]")

        while self.running:
            try:
                self._print_prompt()
                line = input("❯ ").strip()

                if not line:
                    continue

                is_query, cmd_data = self._parse_input(line)

                if not is_query:
                    handled, data, msg = self._handle_command(
                        cmd_data["command"], cmd_data["args"]
                    )

                    if msg:
                        if cmd_data["command"] in ("help", "?"):
                            self.console.console.print(Panel(msg, border_style="cyan"))
                        else:
                            self.console.console.print(msg)

                    if data.get("exit"):
                        break

                    if not handled:
                        self.console.print_error(msg if msg else "Unknown command")

                    self._print_header()
                    continue

                self._print_header()
                self.console.console.print(f"[cyan]❯ {line}[/cyan]")

                self._stream_chat(line)

            except KeyboardInterrupt:
                self.console.console.print("\n[dim](Ctrl+C to exit, /exit to quit)[/dim]")
                continue
            except EOFError:
                self.console.console.print("\n[cyan]Goodbye![/cyan]")
                break

        self.console.console.print("[dim]Session ended.[/dim]")


def run_repl() -> None:
    """Entry point for the REPL."""
    from dotenv import load_dotenv

    env_path = Path(__file__).parent.parent.parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    repl = REPL()
    repl.run()


if __name__ == "__main__":
    run_repl()
