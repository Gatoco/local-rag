"""
Status bar display for REPL.

Shows current mode, provider, model, RAG status, and document count.
Styled without emojis, using box-drawing characters.
"""

from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..ui.themes import Theme, ThemeManager


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

    def __init__(
        self,
        theme: Theme | None = None,
        theme_manager: ThemeManager | None = None,
    ) -> None:
        self._theme = theme
        self._theme_manager = theme_manager or ThemeManager()
        self.mode = "cloud"
        self.provider = "minimax"
        self.model = "MiniMax-M2.7"
        self.rag_enabled = False
        self.docs_count = 0
        self.local_model = "none"

    @property
    def theme(self) -> Theme:
        """Get current theme."""
        return self._theme or self._theme_manager.current

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

    def _get_mode_badge(self) -> Text:
        """Get formatted mode badge."""
        if self.mode == "local":
            return Text(" LOCAL ", style=self.theme.colors.status_mode_local)
        return Text(" CLOUD ", style=self.theme.colors.status_mode_cloud)

    def _get_rag_badge(self) -> Text:
        """Get formatted RAG status badge."""
        if self.rag_enabled:
            return Text(" RAG: ON ", style=self.theme.colors.status_rag_on)
        return Text(" RAG: OFF ", style=self.theme.colors.status_rag_off)

    def _get_docs_text(self) -> Text:
        """Get formatted document count."""
        docs_str = f"{self.docs_count:,}" if self.docs_count else "0"
        return Text(f"docs: {docs_str}", style=self.theme.colors.status_docs)

    def _get_provider_text(self) -> Text:
        """Get formatted provider/model info."""
        if self.mode == "local":
            # Truncate long model paths
            model_name = self.local_model.split("/")[-1] if self.local_model else "none"
            return Text(model_name, style=self.theme.colors.status_provider)
        return Text(self.provider, style=self.theme.colors.status_provider)

    def _get_model_text(self) -> Text:
        """Get formatted model name."""
        if self.mode == "local":
            return Text("")
        # Truncate model name if too long
        model_name = self.model
        if len(model_name) > 20:
            model_name = model_name[:18] + ".."
        return Text(model_name, style=self.theme.colors.status_model)

    def _build_header_line(self) -> Text:
        """Build the main header line."""
        header = Text("LOCAL-RAG", style=f"bold {self.theme.colors.primary}")
        mode_badge = self._get_mode_badge()
        rag_badge = self._get_rag_badge()

        line = header + Text("  ") + mode_badge + Text("  ") + rag_badge
        return line

    def _build_info_line(self) -> Text:
        """Build the info line with details."""
        docs = self._get_docs_text()
        provider = self._get_provider_text()

        parts: list[Text] = []

        if self.mode == "local":
            parts.append(Text("mode: local", style=self.theme.colors.dim))
            parts.append(provider)
        else:
            parts.append(Text("mode: cloud", style=self.theme.colors.dim))
            parts.append(provider)
            parts.append(Text(" / ", style=self.theme.colors.dim))
            parts.append(self._get_model_text())

        parts.append(Text("  ", style=self.theme.colors.dim))
        parts.append(docs)

        return Text("  │  ").join(parts)

    def render(self) -> Panel:
        """Render the status bar as a Panel."""
        header = self._build_header_line()
        info = self._build_info_line()

        # Create two-row layout
        content = f"{header}\n{info}"

        return Panel(
            content,
            border_style=self.theme.colors.panel_border,
            title=f"[bold]{self.theme.box_chars.top_left}{self.theme.box_chars.horizontal * 3}[/bold]",
            title_align="left",
            padding=(0, 1),
            height=3,
            style="none",
        )

    def print(self) -> None:
        """Print the status bar to console."""
        from ..ui.console import Console

        console = Console()
        console.console.print(self.render())

    def print_inline(self) -> None:
        """Print status bar inline (single line, no panel)."""
        from ..ui.console import Console

        console = Console()
        line = self._build_header_line()
        console.console.print(line)

    def clear_line(self) -> None:
        """Clear the current line (for progress updates)."""
        from ..ui.console import Console

        console = Console()
        console.console.print("\033[2K", end="")  # ANSI clear line
        console.console.print("\033[0G", end="")  # ANSI cursor to column 0

    def get_state_dict(self) -> dict:
        """Get current state as dict (useful for serialization)."""
        return {
            "mode": self.mode,
            "provider": self.provider,
            "model": self.model,
            "rag_enabled": self.rag_enabled,
            "docs_count": self.docs_count,
            "local_model": self.local_model,
        }