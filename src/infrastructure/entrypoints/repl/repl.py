"""
Main REPL loop - orchestrates everything.
"""

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import readline

from .commands.base import Command, CommandResult
from .commands.help import HelpCommand, ExitCommand, ClearCommand
from .commands.model import ProvidersCommand, ProviderCommand, ModelsCommand, ModelCommand
from .commands.rag import RagCommand, IndexCommand, StatsCommand
from .session import SessionManager
from .history import History


GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"


def colored(text: str, color: str) -> str:
    return f"{color}{text}{RESET}"


class REPL:
    def __init__(self):
        self.running = True
        self.rag_enabled = False
        self.rag_top_k = 5
        self.provider = "minimax"
        self.model = "MiniMax-M2.7"
        self.collection_count = 0
        self._chroma_collection = None
        self._embedding_model = None
        self._llm_adapter = None

        self.history = History()
        self.session_manager = SessionManager()
        self.current_session = self.session_manager.get_or_create_default()

        self._setup_commands()
        self._setup_readline()
        self._init_chroma()

    def _init_chroma(self) -> None:
        """Initialize ChromaDB connection."""
        try:
            import chromadb
            from chromadb.config import Settings
            from langchain_huggingface import HuggingFaceEmbeddings

            CHROMA_DB_DIR = Path(__file__).parent.parent.parent.parent.parent / "chroma_db"
            client = chromadb.PersistentClient(
                path=str(CHROMA_DB_DIR),
                settings=Settings(anonymized_telemetry=False)
            )
            self._chroma_collection = client.get_collection(name="local_rag_docs")
            self.collection_count = self._chroma_collection.count()

            self._embedding_model = HuggingFaceEmbeddings(
                model_name="BAAI/bge-large-en-v1.5",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True, "batch_size": 32}
            )
        except Exception as e:
            print(colored(f"Warning: ChromaDB not available: {e}", YELLOW))

    def _get_adapter(self):
        """Get or create LLM adapter."""
        if self._llm_adapter:
            return self._llm_adapter

        from src.infrastructure.adapters.cloud_llm_adapter import CloudLLMAdapter

        api_key_env = {
            "minimax": "MINIMAX_API_KEY",
            "groq": "GROQ_API_KEY",
            "openai": "OPENAI_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
        }

        env_var = api_key_env.get(self.provider, "MINIMAX_API_KEY")
        api_key = os.environ.get(env_var)

        if not api_key:
            api_key_env_full = {
                "minimax": os.environ.get("MINIMAX_API_KEY", ""),
                "groq": os.environ.get("GROQ_API_KEY", ""),
            }
            for k, v in api_key_env_full.items():
                if v:
                    api_key = v
                    self.provider = k
                    break

        if not api_key:
            raise RuntimeError(f"No API key found. Set {env_var} in .env")

        self._llm_adapter = CloudLLMAdapter(
            provider=self.provider,
            model=self.model,
            api_key=api_key,
        )
        return self._llm_adapter

    def _search_chroma(self, query: str, k: int = 3) -> list[dict]:
        """Search ChromaDB for similar documents."""
        if not self._chroma_collection or not self._embedding_model:
            return []

        try:
            query_emb = self._embedding_model.embed_query(query)
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
            print(colored(f"ChromaDB error: {e}", RED))
            return []

    def _setup_commands(self) -> None:
        self._commands: list[Command] = [
            HelpCommand(),
            ExitCommand(),
            ClearCommand(),
            ProvidersCommand(),
            ProviderCommand(),
            ModelsCommand(),
            ModelCommand(),
            RagCommand(),
            IndexCommand(),
            StatsCommand(),
        ]
        self._command_map = {cmd.name: cmd for cmd in self._commands}
        for cmd in self._commands:
            for alias in cmd.aliases:
                self._command_map[alias] = cmd

    def _setup_readline(self) -> None:
        readline.parse_and_bind("tab: complete")
        readline.parse_and_bind("set editing-mode vi")

    def _get_context(self) -> dict:
        return {
            "rag_enabled": self.rag_enabled,
            "rag_top_k": self.rag_top_k,
            "provider": self.provider,
            "model": self.model,
            "collection_count": self.collection_count,
            "commands": self._command_map,
            "session": self.current_session,
            "history": self.history,
        }

    def _update_context(self, updates: dict) -> None:
        if "rag_enabled" in updates:
            self.rag_enabled = updates["rag_enabled"]
        if "rag_top_k" in updates:
            self.rag_top_k = updates["rag_top_k"]
        if "provider" in updates:
            self.provider = updates["provider"]
            self._llm_adapter = None
        if "model" in updates:
            self.model = updates["model"]
            self._llm_adapter = None

    def _handle_command(self, line: str) -> tuple[bool, dict, str]:
        """Returns (is_user_input, data_dict, message)."""
        if not line.strip():
            return False, {}, ""

        if line.startswith("/"):
            parts = line.split()
            cmd_name = parts[0][1:].lower()
            args = parts[1:] if len(parts) > 1 else []

            if cmd_name in self._command_map:
                cmd = self._command_map[cmd_name]
                context = self._get_context()
                result = cmd.execute(args, context)

                if result.data:
                    self._update_context(result.data)

                    if result.data.get("exit"):
                        self.running = False

                return False, result.data if result.data else {}, result.message if result.should_print else ""
            else:
                return False, {"error": f"Unknown command: {cmd_name}"}, ""

        return True, {}, ""

    def _safe_progress_print(self, current: int, total: int, prefix: str = "") -> None:
        """Print progress bar with percentage using sys.stdout for safety."""
        if total <= 0:
            return
        pct = min(100, int(current / total * 100))
        bar_len = 30
        filled = int(bar_len * current / total)
        bar = "█" * filled + "░" * (bar_len - filled)
        prefix_str = f"{prefix} " if prefix else ""
        msg = f"\r{prefix_str}[{bar}] {pct}% ({current}/{total})"
        sys.stdout.write(msg)
        sys.stdout.flush()

    def _print_progress(self, current: int, total: int, prefix: str = "") -> None:
        """Print progress bar with percentage (deprecated - use _safe_progress_print)."""
        self._safe_progress_print(current, total, prefix)

    def _index_documents(self, directory: str, reindex: bool = False) -> None:
        """Index documents with progress reporting."""
        docs_dir = Path(directory).absolute()

        if not docs_dir.exists():
            print(colored(f"\nDirectory not found: {directory}", RED))
            return

        if reindex:
            import chromadb
            from chromadb.config import Settings
            chroma_path = docs_dir.parent / "chroma_db"
            try:
                client = chromadb.PersistentClient(
                    path=str(chroma_path),
                    settings=Settings(anonymized_telemetry=False)
                )
                client.delete_collection(name="local_rag_docs")
                print(colored("\nExisting collection deleted (--reindex)", YELLOW))
            except Exception:
                pass

        print(colored(f"\nIndexing documents from: {docs_dir}", GREEN))

        embeddings = self._embedding_model
        if embeddings is None:
            print("Loading embedding model...")
            from langchain_huggingface import HuggingFaceEmbeddings
            embeddings = HuggingFaceEmbeddings(
                model_name="BAAI/bge-large-en-v1.5",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True, "batch_size": 32}
            )

        print("Loading documents...")
        from src.infrastructure.adapters.langchain_loader_adapter import LangChainLoaderAdapter
        loader = LangChainLoaderAdapter(chunk_size=800, chunk_overlap=150)

        try:
            all_docs = loader.load_directory(str(docs_dir))
        except Exception as e:
            print(colored(f"Error loading documents: {e}", RED))
            return

        if not all_docs:
            print(colored("No documents found to index.", YELLOW))
            return

        total_chunks = len(all_docs)
        print(f"Loaded {total_chunks} chunks from documents")

        print("Indexing to ChromaDB...")
        import chromadb
        from chromadb.config import Settings
        from chromadb.api.client import Client

        chroma_path = docs_dir.parent / "chroma_db"

        client = chromadb.PersistentClient(
            path=str(chroma_path),
            settings=Settings(anonymized_telemetry=False)
        )

        try:
            collection = client.get_collection(name="local_rag_docs")
            if reindex:
                client.delete_collection(name="local_rag_docs")
                collection = client.create_collection(name="local_rag_docs")
        except Exception:
            collection = client.create_collection(name="local_rag_docs")

        batch_size = 100
        indexed = 0
        last_pct = -1
        n_batches = (total_chunks + batch_size - 1) // batch_size

        print(f"Indexing {total_chunks} chunks in {n_batches} batches (batch_size={batch_size})...")
        print("Using sequential processing (no threading)")

        completed = 0

        for i in range(0, total_chunks, batch_size):
            batch_start = i
            batch_num = (i // batch_size) + 1

            batch = all_docs[i:i + batch_size]
            texts = [doc.page_content for doc in batch]
            metadatas = [doc.metadata for doc in batch]

            emb_batch = embeddings.embed_documents(texts)

            batch_end = min(i + batch_size, total_chunks)
            ids = [f"doc_{j}" for j in range(i, batch_end)]

            collection.add(
                ids=ids,
                documents=texts,
                embeddings=emb_batch,
                metadatas=metadatas
            )

            completed += len(batch)
            pct = int(completed / total_chunks * 100)
            if pct != last_pct:
                self._safe_progress_print(completed, total_chunks, "Indexing:")
                last_pct = pct

        print(colored(f"\n\nIndexing complete! {total_chunks} chunks indexed.", GREEN))
        self.collection_count = collection.count()

    def _search_chroma(self, query: str, k: int = 3) -> list[dict]:
        """Search ChromaDB for similar documents."""
        if not self._chroma_collection or not self._embedding_model:
            return []

        try:
            query_emb = self._embedding_model.embed_query(query)
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
            print(colored(f"ChromaDB error: {e}", RED))
            return []

    def _get_adapter(self):
        """Get or create LLM adapter."""
        if self._llm_adapter:
            return self._llm_adapter

        from src.infrastructure.adapters.cloud_llm_adapter import CloudLLMAdapter

        api_key_env = {
            "minimax": "MINIMAX_API_KEY",
            "groq": "GROQ_API_KEY",
            "openai": "OPENAI_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
        }

        env_var = api_key_env.get(self.provider, "MINIMAX_API_KEY")
        api_key = os.environ.get(env_var)

        if not api_key:
            from dotenv import load_dotenv
            env_path = Path(__file__).parent.parent.parent.parent / ".env"
            load_dotenv(env_path)
            api_key = os.environ.get(env_var)

        if not api_key:
            raise RuntimeError(f"No API key found. Set {env_var} in .env")

        self._llm_adapter = CloudLLMAdapter(
            provider=self.provider,
            model=self.model,
            api_key=api_key,
        )
        return self._llm_adapter

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

                    print(colored(f"\n[Sources: {', '.join(sources[:3])}]\n", BLUE), end="", flush=True)
                    full_response = ""
                    for token in adapter.generate_stream(full_prompt, max_tokens=1024):
                        print(token, end="", flush=True)
                        full_response += token
                    print()
                    self.history.add("user", prompt)
                    self.history.add("assistant", full_response)
                    return
                else:
                    print(colored("No documents found in RAG. Falling back to chat mode.\n", YELLOW))

            payload = adapter._build_payload(prompt, None)
            headers = adapter._build_headers()

            import httpx
            with httpx.Client(timeout=adapter.timeout) as client:
                with client.stream(
                    "POST",
                    f"{adapter.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                ) as response:
                    response.raise_for_status()
                    full_response = ""
                    for line in response.iter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data.strip() == "[DONE]":
                                break
                            token = adapter._parse_sse_token(data)
                            if token:
                                print(token, end="", flush=True)
                                full_response += token
                    print()
                    self.history.add("user", prompt)
                    self.history.add("assistant", full_response)

        except Exception as e:
            print(colored(f"Error: {e}", RED))

    def _print_welcome(self) -> None:
        print()
        print(colored("╭─────────────────────────────────────────────────────────────╮", GREEN))
        print(colored("│                  MyLocalRAG REPL                             │", GREEN))
        print(colored("╰─────────────────────────────────────────────────────────────╯", GREEN))
        print()
        print(f"  Provider: {BLUE}{self.provider}{RESET}")
        print(f"  Model: {BLUE}{self.model}{RESET}")
        print(f"  RAG: {GREEN if self.rag_enabled else YELLOW}{'ON' if self.rag_enabled else 'OFF'}{RESET}")
        print(f"  Indexed docs: {self.collection_count}")
        print()
        print(f"  Type {BOLD}/help{RESET} for commands or just ask your question!")
        print()

    def prompt(self) -> str:
        prefix = colored("RAG", GREEN) if self.rag_enabled else colored("LLM", BLUE)
        return f"[{prefix}] mylocalrag > "

    def run(self) -> None:
        """Main REPL loop."""
        self._print_welcome()

        while self.running:
            try:
                line = input(self.prompt()).strip()

                if not line:
                    continue

                is_user_input, extra_data, cmd_msg = self._handle_command(line)

                if cmd_msg:
                    print(cmd_msg)

                if extra_data:
                    if "error" in extra_data:
                        print(colored(extra_data["error"], RED))
                    elif "action" in extra_data and extra_data["action"] == "index":
                        self._index_documents(
                            extra_data.get("directory", "./docs_to_ingest"),
                            extra_data.get("reindex", False)
                        )
                        continue

                if not is_user_input:
                    if extra_data and extra_data.get("exit"):
                        break
                    continue

                self._stream_chat(line)

            except KeyboardInterrupt:
                print("\n(Type /exit to quit)")
                continue
            except EOFError:
                print("\nGoodbye!")
                break

        self.session_manager.update_session(self.current_session)


def run_repl() -> None:
    """Entry point."""
    from dotenv import load_dotenv

    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    load_dotenv(env_path)

    repl = REPL()
    repl.run()


if __name__ == "__main__":
    run_repl()