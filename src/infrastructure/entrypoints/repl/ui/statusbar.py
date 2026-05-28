"""
Status bar display for REPL.

Shows current mode, provider, model, RAG status, and document count.
"""

from rich.panel import Panel

from ..ui.console import Console as REPLConsole


class StatusBar:
    """
    Status bar display for the REPL.

    Renders a compact header showing:
    - Mode: [local] or [cloud]
    - Provider/Model (context-dependent)
    - RAG status
    - Document count

    Usage:
        status = StatusBar()
        status.update(mode="local", provider="llama.cpp", model="mistral-7b", rag=True, docs=2400)
        status.render()
    """

    def __init__(self, console: REPLConsole | None = None) -> None:
        self.console = console or REPLConsole()
        self.mode = "cloud"
        self.provider = "minimax"
        self.model = "MiniMax-M2.7"
        self.rag_enabled = False
        self.docs_count = 0
        self.local_model = "none"

    def update(
        self,
        mode: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        rag_enabled: bool | None = None,
        docs_count: int | None = None,
        local_model: str | None = None,
    ) -> None:
        """Update status bar fields."""
        if mode is not None:
            self.mode = mode
        if provider is not None:
            self.provider = provider
        if model is not None:
            self.model = model
        if rag_enabled is not None:
            self.rag_enabled = rag_enabled
        if docs_count is not None:
            self.docs_count = docs_count
        if local_model is not None:
            self.local_model = local_model

    def _format_mode(self) -> str:
        """Format mode indicator."""
        if self.mode == "local":
            return "[bold green]local[/bold green]"
        return "[bold cyan]cloud[/bold cyan]"

    def _format_provider_info(self) -> str:
        """Format provider/model info."""
        if self.mode == "local":
            return f"[dim]{self.local_model}[/dim]"
        return f"[cyan]{self.provider}[/cyan]"

    def _format_rag(self) -> str:
        """Format RAG status indicator."""
        if self.rag_enabled:
            return "[bold green]RAG[/bold green]"
        return "[dim]RAG[/dim]"

    def _format_docs(self) -> str:
        """Format docs count."""
        return f"[dim]docs:[/dim][yellow]{self.docs_count}[/yellow]"

    def render(self) -> Panel:
        """Render the status bar as a Panel."""
        parts = [
            self._format_mode(),
            "[dim]|[/dim]",
            self._format_provider_info(),
            "[dim]|[/dim]",
            self._format_rag(),
            "[dim]|[/dim]",
            self._format_docs(),
        ]

        status_line = " ".join(parts)

        return Panel(
            status_line,
            style="cyan",
            border_style="cyan",
            title="[bold]local-rag[/bold]",
            title_align="left",
            padding=(0, 1),
        )

    def print(self) -> None:
        """Print the status bar to console."""
        self.console.console.print(self.render())

    def print_inline(self) -> None:
        """Print status bar inline (no panel formatting)."""
        parts = [
            self._format_mode(),
            self._format_provider_info(),
            self._format_rag(),
            f"docs:{self.docs_count}",
        ]
        self.console.console.print(" | ".join(parts))

    def clear_line(self) -> None:
        """Clear the current line (for progress updates)."""
        self.console.console.print("\033[2K", end="")  # ANSI clear line
        self.console.console.print("\033[0G", end="")  # ANSI cursor to column 0
