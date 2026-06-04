"""
CloudChatCLI - CLI for RAG Cloud Chat.

Supports multiple cloud providers: OpenAI, Anthropic, Google, Groq, MiniMax, DeepSeek.
Supports RAG mode for querying indexed documents.
"""

import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from dotenv import load_dotenv
from rich.console import Console

from src.infrastructure.adapters.cloud_llm_adapter import PROVIDER_CONFIG, CloudLLMAdapter
from src.infrastructure.entrypoints.chat_cli import LLMChatCLI

logger = logging.getLogger("cloud-chat")

CHROMA_DB_DIR = os.path.join(Path(__file__).parent.parent.parent.parent, "chroma_db")
COLLECTION_NAME = "local_rag_docs"


class CloudChatCLI(LLMChatCLI):
    """
    Cloud Chat CLI implementation.

    Supports multi-provider cloud LLM access with streaming responses.
    Supports RAG mode for querying indexed documents.
    """

    def __init__(self):
        super().__init__(
            config_path="~/.config/mylocalrag.toml",
            description="RAG Cloud Chat - Multi-provider CLI for cloud LLMs",
        )
        self.console = Console()
        self._current_adapter: CloudLLMAdapter | None = None
        self._current_provider = "minimax"
        self._current_model = "MiniMax-M2.7"
        self._rag_mode = False
        self._rag_top_k = 5
        self._chroma_client = None
        self._chroma_collection = None
        self._init_chroma()

    def _init_chroma(self) -> None:
        """Initialize ChromaDB connection."""
        try:
            import chromadb
            from chromadb.config import Settings
            from langchain_huggingface import HuggingFaceEmbeddings

            self._chroma_client = chromadb.PersistentClient(
                path=CHROMA_DB_DIR, settings=Settings(anonymized_telemetry=False)
            )
            try:
                self._chroma_collection = self._chroma_client.get_collection(name=COLLECTION_NAME)
            except Exception:
                self._chroma_collection = None

            self._embedding_model = HuggingFaceEmbeddings(
                model_name="BAAI/bge-large-en-v1.5",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
            logger.info("ChromaDB initialized successfully with BGE-Large embeddings")
        except ImportError:
            logger.warning("ChromaDB not installed")
        except Exception as e:
            logger.warning(f"ChromaDB init failed: {e}")

    def _search_chroma(self, query: str, k: int = 2) -> list[dict]:
        """Search ChromaDB for similar documents."""
        if self._chroma_collection is None or not hasattr(self, "_embedding_model"):
            return []
        try:
            query_embedding = self._embedding_model.embed_query(query)
            results = self._chroma_collection.query(
                query_embeddings=[query_embedding], n_results=k, include=["documents", "metadatas"]
            )
            docs = []
            if results and results.get("documents"):
                for i, doc in enumerate(results["documents"][0]):
                    metadata = (
                        results.get("metadatas", [[{}]])[0][i] if results.get("metadatas") else {}
                    )
                    docs.append({"content": doc, "metadata": metadata})
            return docs
        except Exception as e:
            logger.warning(f"ChromaDB query failed: {e}")
            return []

    def _get_adapter(self, provider: str, model: str | None = None) -> CloudLLMAdapter:
        """
        Get or create CloudLLMAdapter for provider.

        Args:
            provider: Provider name
            model: Model name (uses default if None)

        Returns:
            CloudLLMAdapter instance
        """
        api_key_env = PROVIDER_CONFIG.get(provider, {}).get("api_key_env", "")
        api_key = os.environ.get(api_key_env) or os.environ.get(f"{provider.upper()}_API_KEY", "")

        if not api_key:
            raise ValueError(
                f"No API key for {provider}. Set {api_key_env} in .env or environment variable."
            )

        return CloudLLMAdapter(provider=provider, model=model, api_key=api_key)

    def add_extra_args(self, parser) -> None:
        """No extra args for CloudChatCLI."""
        pass

    def stream_generate_chat(
        self, prompt: str, config: dict, context: list[dict[str, str]] | None = None
    ) -> None:
        """
        Generate streaming chat response.

        Args:
            prompt: User prompt
            config: Configuration dict
            context: Conversation history (not used in current implementation)
        """
        provider = config.get("provider", self._current_provider)
        model = config.get("model", None)

        if self._rag_mode and self._chroma_collection is not None:
            self._rag_stream_query(prompt)
            return

        try:
            adapter = self._get_adapter(provider, model)
            self._current_adapter = adapter
            self._current_provider = provider

            # Build messages for chat
            messages = []
            if context:
                for msg in context:
                    messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({"role": "user", "content": prompt})

            # Create payload for streaming
            payload = adapter._build_payload(prompt, None)
            headers = adapter._build_headers()

            import httpx

            with httpx.Client(timeout=adapter.timeout) as client:
                with client.stream(
                    "POST", f"{adapter.base_url}/chat/completions", json=payload, headers=headers
                ) as response:
                    response.raise_for_status()

                    full_text = ""
                    for line in response.iter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data.strip() == "[DONE]":
                                break
                            token = adapter._parse_sse_token(data)
                            if token:
                                print(token, end="", flush=True)
                                full_text += token

            print()  # New line after response

            # Add to context
            if context is not None:
                context.append({"role": "user", "content": prompt})
                context.append({"role": "assistant", "content": full_text})

        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
            logger.error(f"Chat error: {e}", exc_info=True)

    def cmd_providers(self, args: list[str]) -> None:
        """List available providers."""
        self.console.print("[bold]Available Providers:[/bold]")
        for provider_id, cfg in PROVIDER_CONFIG.items():
            api_key_set = bool(os.environ.get(cfg["api_key_env"]))
            status = (
                "[green]✓ configured[/green]" if api_key_set else "[red]✗ not configured[/red]"
            )
            default = (
                f" (default: {cfg['default_model']})"
                if provider_id == self._current_provider
                else ""
            )
            self.console.print(f"  [cyan]{provider_id}[/cyan]{default} - {status}")

    def cmd_provider(self, args: list[str]) -> None:
        """Switch to a specific provider."""
        if not args or not args[0]:
            self.console.print("[yellow]Usage: /provider <name>[/yellow]")
            self.console.print("Available: " + ", ".join(PROVIDER_CONFIG.keys()))
            return

        new_provider = args[0].lower()
        if new_provider not in PROVIDER_CONFIG:
            self.console.print(f"[red]Unknown provider: {new_provider}[/red]")
            self.console.print("Available: " + ", ".join(PROVIDER_CONFIG.keys()))
            return

        api_key_env = PROVIDER_CONFIG[new_provider]["api_key_env"]
        if not os.environ.get(api_key_env):
            self.console.print(
                f"[red]No API key configured for {new_provider}.[/red]\n"
                f"Set {api_key_env} in your .env file."
            )
            return

        self._current_provider = new_provider
        self._current_model = PROVIDER_CONFIG[new_provider]["default_model"]
        self.console.print(
            f"[green]Switched to {new_provider}[/green] (model: {self._current_model})"
        )

    def cmd_models(self, args: list[str]) -> None:
        """List models for current provider."""
        provider = self._current_provider
        models = PROVIDER_CONFIG.get(provider, {}).get("models", [])
        default = PROVIDER_CONFIG.get(provider, {}).get("default_model", "")

        self.console.print(f"[bold]Models for {provider}:[/bold]")
        for model in models:
            marker = " [yellow](default)[/yellow]" if model == default else ""
            marker += " [cyan]*[/cyan]" if model == self._current_model else ""
            self.console.print(f"  {model}{marker}")

    def cmd_model(self, args: list[str]) -> None:
        """Switch to a specific model."""
        if not args or not args[0]:
            self.console.print("[yellow]Usage: /model <name>[/yellow]")
            self.cmd_models([])
            return

        new_model = args[0]
        provider_models = PROVIDER_CONFIG.get(self._current_provider, {}).get("models", [])

        if new_model not in provider_models:
            self.console.print(f"[red]Unknown model: {new_model}[/red]")
            self.console.print(f"Available models for {self._current_provider}:")
            for m in provider_models:
                self.console.print(f"  {m}")
            return

        self._current_model = new_model
        self.console.print(f"[green]Switched to model: {new_model}[/green]")

    def cmd_clear(self, args: list[str]) -> None:
        """Clear conversation history."""
        self.console.print("[cyan]Conversation history cleared.[/cyan]")

    def cmd_rag(self, args: list[str]) -> None:
        """Toggle RAG mode or configure it."""
        if self._chroma_collection is None:
            self.console.print("[red]RAG not available. No collection found.[/red]")
            self.console.print("[yellow]Make sure documents are indexed first.[/yellow]")
            return

        if args and args[0] in ("on", "off"):
            self._rag_mode = args[0] == "on"
            status = "[green]enabled[/green]" if self._rag_mode else "[yellow]disabled[/yellow]"
            self.console.print(f"RAG mode {status}")
        elif args and args[0] == "status":
            self._show_rag_status()
        elif args and args[0] == "topk" and len(args) > 1:
            try:
                new_k = int(args[1])
                if new_k < 1 or new_k > 20:
                    self.console.print("[yellow]top_k must be between 1 and 20[/yellow]")
                else:
                    self._rag_top_k = new_k
                    self.console.print(f"[green]top_k set to {new_k}[/green]")
            except ValueError:
                self.console.print(f"[red]Invalid number: {args[1]}[/red]")
        else:
            self._rag_mode = not self._rag_mode
            status = "[green]ON[/green]" if self._rag_mode else "[yellow]OFF[/yellow]"
            self.console.print(f"RAG mode {status} (use /rag on|off|topk <n>|status to change)")

    def cmd_index(self, args: list[str]) -> None:
        """List indexed documents info."""
        if self._chroma_collection is None:
            self.console.print("[yellow]No collection found.[/yellow]")
            self.console.print("Run ingestion to index documents first.")
            return

        try:
            count = self._chroma_collection.count()
            self.console.print(f"[bold]Indexed Documents:[/bold] {count}")

            if args and args[0] == "--sample" and count > 0:
                sample_query = self._embedding_model.embed_query("information")
                results = self._chroma_collection.query(
                    query_embeddings=[sample_query],
                    n_results=3,
                    include=["documents", "metadatas"],
                )
                self.console.print("\n[bold]Sample documents:[/bold]")
                for i, doc in enumerate(results.get("documents", [[]])[0]):
                    meta = results.get("metadatas", [[{}]])[0][i]
                    source = meta.get("source", "unknown") if meta else "unknown"
                    preview = doc[:150] + "..." if len(doc) > 150 else doc
                    self.console.print(f"  {i + 1}. [{source}]")
                    self.console.print(f"     {preview}")
        except Exception as e:
            self.console.print(f"[red]Error accessing index: {e}[/red]")

    def _show_rag_status(self) -> None:
        """Show RAG status."""
        self.console.print("[bold]RAG Status:[/bold]")
        self.console.print(
            f"  Mode: {'[green]ON[/green]' if self._rag_mode else '[yellow]OFF[/yellow]'}"
        )
        self.console.print(f"  Top_k: {self._rag_top_k}")
        if self._chroma_collection:
            try:
                count = self._chroma_collection.count()
                self.console.print(f"  Documents indexed: {count}")
            except Exception:
                self.console.print("  Documents indexed: unknown")
        else:
            self.console.print("  Documents indexed: (not initialized)")

    def _is_comparative_query(self, question: str) -> bool:
        """Detect if query is comparative (needs more docs for comparison)."""
        comparative_keywords = [
            "heaviest",
            "tallest",
            "best",
            "worst",
            "most",
            "least",
            "max",
            "min",
            "largest",
            "smallest",
            "highest",
            "lowest",
            "oldest",
            "youngest",
            "fastest",
            "slowest",
            "strongest",
            "biggest",
            "shortest",
            "slowest",
            "richest",
            "poorest",
            "compare",
            "versus",
            "vs",
            "difference",
            "between",
        ]
        q_lower = question.lower()
        return any(kw in q_lower for kw in comparative_keywords)

    def _deduplicate_docs(
        self, docs: list[dict], max_chars: int = 800
    ) -> tuple[list[dict], list[str]]:
        """Deduplicate docs by Fighter_Name extracted from content. Keeps one entry per fighter."""
        import re

        seen_fighters: set[str] = set()
        unique_docs = []
        sources_used = []

        for doc in docs:
            content = doc.get("content", "")
            name_match = re.search(r"Fighter_Name:\s*([^,]+)", content)
            fighter_name = name_match.group(1).strip() if name_match else content[:50]

            if fighter_name not in seen_fighters:
                seen_fighters.add(fighter_name)
                if len(content) > max_chars:
                    content = content[:max_chars] + "..."
                unique_docs.append({"content": content, "metadata": doc.get("metadata", {})})
                source = doc.get("metadata", {}).get("source", "unknown")
                sources_used.append(source)

        return unique_docs, sources_used

    def _rag_stream_query(self, question: str) -> None:
        """Execute RAG query with streaming."""
        if self._current_adapter is None:
            try:
                self._current_adapter = self._get_adapter(
                    self._current_provider, self._current_model
                )
            except Exception as e:
                self.console.print(f"[red]No adapter available: {e}[/red]")
                return

        is_comparative = self._is_comparative_query(question)
        effective_k = 15 if is_comparative else self._rag_top_k

        docs = self._search_chroma(question, k=effective_k)

        if not docs:
            self.console.print("[yellow]No documents found. Try with more general terms.[/yellow]")
            return

        unique_docs, sources_used = self._deduplicate_docs(docs)

        context_parts = []
        for doc in unique_docs:
            content = doc.get("content", "")
            if len(content) > 1500:
                content = content[:1500] + "..."
            context_parts.append(content)

        context = "\n\n".join(context_parts)

        prompt = (
            f"Contexto de documentos:\n"
            f"{context}\n\n"
            f"Pregunta: {question}\n\n"
            f"Responde de forma directa, sin bloques de pensamiento. "
            f"Usa SOLO la información del contexto para responder. "
            f'Si no hay suficiente información, responde "No tengo información suficiente '
            f'en los documentos". No inventes respuestas.'
        )

        try:
            payload = self._current_adapter._build_payload(prompt, None)
            headers = self._current_adapter._build_headers()

            import httpx

            with httpx.Client(timeout=self._current_adapter.timeout) as client:
                with client.stream(
                    "POST",
                    f"{self._current_adapter.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                ) as response:
                    response.raise_for_status()

                    print("\n[Sources used:", end="", flush=True)
                    for i, src in enumerate(sources_used):
                        print(f" {i + 1}: {src}", end="", flush=True)
                    print("]\n", flush=True)

                    for line in response.iter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data.strip() == "[DONE]":
                                break
                            token = self._current_adapter._parse_sse_token(data)
                            if token:
                                print(token, end="", flush=True)

            print()

        except Exception as e:
            self.console.print(f"[red]RAG query error: {e}[/red]")
            logger.error(f"RAG query error: {e}", exc_info=True)

    def cmd_history(self, args: list[str]) -> None:
        """Show conversation history."""
        self.console.print("[yellow]History not implemented yet.[/yellow]")
        self.console.print("Context is maintained during session.")


def main():
    """Entry point for mylocalrag command."""
    load_dotenv()
    CloudChatCLI().run()


if __name__ == "__main__":
    main()
