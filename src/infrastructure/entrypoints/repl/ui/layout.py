"""
Terminal Layout for REPL.

Provides OpenCode-inspired layout with header, messages, and input area.
"""

from dataclasses import dataclass, field
from typing import Any

from rich.box import ROUNDED, Box
from rich.console import Console as RichConsole
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .themes import Theme


@dataclass
class Message:
    """Represents a chat message."""

    role: str  # "user", "assistant", "system"
    content: str
    timestamp: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class TerminalLayout:
    """
    OpenCode-inspired terminal layout.

    Structure:
    ┌──────────────────────────────────────────┐
    │  HEADER: Status bar with mode, model    │
    ├──────────────────────────────────────────┤
    │                                          │
    │  MESSAGES: Chat history (scrollable)     │
    │                                          │
    ├──────────────────────────────────────────┤
    │  INPUT: Command input area               │
    └──────────────────────────────────────────┘
    """

    BOX: Box = ROUNDED

    def __init__(
        self,
        console: RichConsole,
        theme: Theme | None = None,
    ) -> None:
        self.console = console
        self.theme = theme or Theme(name="dark", colors=theme.colors if theme else None)
        self.layout = Layout()
        self._messages: list[Message] = []
        self._setup_layout()

    def _setup_layout(self) -> None:
        """Initialize the layout structure."""
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="messages"),
            Layout(name="input", size=3),
        )

    def render_header(
        self,
        mode: str,
        provider: str,
        model: str,
        rag_enabled: bool,
        docs_count: int,
    ) -> None:
        """Render the header/status bar."""
        mode_style = "green" if mode == "local" else "cyan"
        mode_text = f"[bold {mode_style}]{mode.upper()}[/bold {mode_style}]"

        rag_style = "green" if rag_enabled else "yellow"
        rag_text = f"[bold {rag_style}]RAG: {'ON' if rag_enabled else 'OFF'}[/bold {rag_style}]"

        docs_text = f"[yellow]docs: {docs_count:,}[/yellow]"

        if mode == "local":
            provider_text = provider.split("/")[-1] if provider else "none"
        else:
            provider_text = provider

        header_table = Table(
            box=self.BOX,
            show_header=False,
            pad_edge=False,
            border_style=self.theme.colors.panel_border,
        )
        header_table.add_column(style="cyan", width=1)
        header_table.add_column(style="white")
        header_table.add_column(style="cyan", width=1)
        header_table.add_column(style="white")

        header_table.add_row(
            "[bold cyan]LOCAL-RAG[/bold cyan]",
            f"{mode_text}  {rag_text}",
            provider_text,
            docs_text,
        )

        self.layout["header"].update(
            Panel(
                header_table,
                border_style=self.theme.colors.panel_border,
                padding=(0, 1),
                height=2,
            )
        )

    def render_messages(self) -> None:
        """Render the messages area."""
        if not self._messages:
            empty_state = Panel(
                "[dim]Ask a question or type /help for commands[/dim]",
                border_style="dim",
                padding=(1, 2),
            )
            self.layout["messages"].update(empty_state)
            return

        message_groups: list[Text] = []
        for msg in self._messages[-20:]:  # Last 20 messages
            if msg.role == "user":
                prefix = Text("❯ ", style="bold cyan")
                content = Text(msg.content, style="cyan")
                block = prefix + content
            elif msg.role == "assistant":
                prefix = Text("  ", style="white")
                content = Text(msg.content, style="white")
                block = prefix + content
            else:
                prefix = Text("[system] ", style="yellow")
                content = Text(msg.content, style="dim yellow")
                block = prefix + content

            message_groups.append(block)

        content = Text("\n").join(message_groups)
        self.layout["messages"].update(
            Panel(
                content,
                border_style=self.theme.colors.panel_border,
                title=f"[dim]Messages ({len(self._messages)})[/dim]",
                padding=(0, 1),
            )
        )

    def render_input_prompt(self, prompt_text: str = "❯") -> None:
        """Render the input area with prompt."""
        prompt = Text(f"[bold cyan]{prompt_text}[/bold cyan] ")
        self.layout["input"].update(
            Panel(
                prompt + Text("Type here... (/help for commands)"),
                border_style="dim",
                padding=(0, 1),
                height=2,
            )
        )

    def render(self) -> str:
        """Render the complete layout."""
        return self.layout.render(self.console)

    def add_message(self, role: str, content: str, metadata: dict[str, Any] = None) -> None:
        """Add a message to the history."""
        from datetime import datetime

        self._messages.append(
            Message(
                role=role,
                content=content,
                timestamp=datetime.now().isoformat(),
                metadata=metadata or {},
            )
        )

    def clear_messages(self) -> None:
        """Clear message history."""
        self._messages.clear()

    def get_messages(self) -> list[Message]:
        """Get all messages."""
        return self._messages.copy()


class SimpleChatLayout:
    """
    Simpler chat-focused layout for REPL.

    Header + message history + input, without complex panels.
    """

    def __init__(
        self,
        console: RichConsole,
        theme: Theme | None = None,
    ) -> None:
        self.console = console
        self.theme = theme or Theme(name="dark", colors=theme.colors if theme else None)
        self.messages: list[Message] = []

    def render_header(
        self,
        mode: str,
        provider: str,
        model: str,
        rag_enabled: bool,
        docs_count: int,
    ) -> None:
        """Render compact header."""
        mode_indicator = "LOCAL" if mode == "local" else "CLOUD"
        mode_color = "green" if mode == "local" else "cyan"

        rag_indicator = "RAG" if rag_enabled else "no-RAG"
        rag_color = "green" if rag_enabled else "yellow"

        docs_indicator = f"docs:{docs_count}"

        line = Text()
        line.append("┌─ ", style="cyan")
        line.append("LOCAL-RAG", style="bold cyan")
        line.append(" ─", style="cyan")
        line.append(f"{mode_indicator:^8}", style=f"bold {mode_color}")
        line.append("│", style="cyan")
        line.append(f"{provider:^12}", style="white")
        line.append("│", style="cyan")
        line.append(f"{rag_indicator:^8}", style=f"bold {rag_color}")
        line.append("│", style="cyan")
        line.append(docs_indicator, style="yellow")
        line.append(" ─", style="cyan")

        self.console.print(line)

    def render_user_message(self, text: str) -> None:
        """Render a user message."""
        lines = text.strip().split("\n")
        first_line = lines[0][:80] + ("..." if len(lines[0]) > 80 or len(lines) > 1 else "")

        msg = Text()
        msg.append("❯ ", style="bold cyan")
        msg.append(first_line, style="cyan")
        self.console.print(msg)

    def render_assistant_message(self, text: str) -> None:
        """Render an assistant message with markdown support."""
        from rich.markdown import Markdown

        # For short messages, print inline
        if len(text) < 100 and "\n" not in text:
            msg = Text()
            msg.append("  ", style="white")
            msg.append(text, style="white")
            self.console.print(msg)
        else:
            # For longer messages, render as markdown
            self.console.print(Markdown(text, code_theme="monokai"))

    def render_sources(self, sources: list[str]) -> None:
        """Render source references."""
        if not sources:
            return
        unique_sources = list(dict.fromkeys(sources))[:3]
        self.console.print(f"[dim]Sources: {', '.join(unique_sources)}[/dim]")

    def render_separator(self) -> None:
        """Render a visual separator."""
        self.console.print("[dim]─" * 40 + "[/dim]")

    def render_loading(self, text: str = "Thinking...") -> Any:
        """Render loading indicator and return context manager."""
        return self.console.status(f"[cyan]{text}[/cyan]", spinner="dots")

    def render_help_tip(self) -> None:
        """Render hint text after help command."""
        self.console.print("[dim]Type a question or /command[/dim]")
