"""
Rich Console wrapper for REPL output.

Provides styled output using rich library with consistent formatting.
Enhanced with spinners, markdown rendering, and live updates.
"""

from typing import Any

from rich.console import Console as RichConsole
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.syntax import Syntax
from rich.theme import Theme
from rich.tree import Tree

custom_theme = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "error": "red",
        "success": "green",
        "prompt": "bold cyan",
        "mode.local": "green",
        "mode.cloud": "cyan",
        "rag.on": "green",
        "rag.off": "yellow",
    }
)


class Console:
    """
    Rich console wrapper for styled output.

    Usage:
        console = Console()
        console.print("Hello world")
        console.print("[success]Success![/success]")
        console.print_markdown("# Header\\nSome text")
    """

    def __init__(self, stderr: bool = False) -> None:
        self.console = RichConsole(stderr=stderr, theme=custom_theme)
        self._width = 80

    @property
    def width(self) -> int:
        """Get console width."""
        return self.console.width

    def print(self, *args: Any, style: str | None = None, **kwargs: Any) -> None:
        """Print with optional style."""
        if style:
            self.console.print(*args, style=style, **kwargs)
        else:
            self.console.print(*args, **kwargs)

    def print_markdown(self, text: str) -> None:
        """Print markdown-formatted text."""
        self.console.print(Markdown(text, code_theme="monokai"))

    def print_error(self, message: str) -> None:
        """Print error message in red."""
        self.console.print(f"[red]Error: {message}[/red]")

    def print_warning(self, message: str) -> None:
        """Print warning message in yellow."""
        self.console.print(f"[yellow]Warning: {message}[/yellow]")

    def print_success(self, message: str) -> None:
        """Print success message in green."""
        self.console.print(f"[green]✓[/green] {message}")

    def print_info(self, message: str) -> None:
        """Print info message in cyan."""
        self.console.print(f"[cyan]ℹ[/cyan] {message}")

    def print_dim(self, message: str) -> None:
        """Print dimmed message."""
        self.console.print(f"[dim]{message}[/dim]")

    def print_bold(self, message: str) -> None:
        """Print bold message."""
        self.console.print(f"[bold]{message}[/bold]")

    def print_panel(
        self,
        content: str,
        title: str = "",
        border_style: str = "cyan",
        width: int | None = None,
    ) -> None:
        """Print content inside a panel."""
        w = width or self.width - 4
        panel = Panel(
            content,
            title=title,
            border_style=border_style,
            width=w,
            padding=(0, 1),
        )
        self.console.print(panel)

    def print_code(
        self,
        code: str,
        language: str = "python",
        title: str = "",
        line_numbers: bool = False,
    ) -> None:
        """Print syntax-highlighted code block."""
        syntax = Syntax(code, language, line_numbers=line_numbers, theme="monokai")
        if title:
            self.print_panel(
                syntax,
                title=title,
                border_style="blue",
            )
        else:
            self.console.print(syntax)

    def print_tree(self, data: dict[str, Any], title: str = "") -> None:
        """Print data as a tree structure."""
        tree = Tree(title or "Structure")
        self._add_to_tree(tree, data)
        self.console.print(tree)

    def _add_to_tree(self, tree: Tree, data: dict[str, Any], prefix: str = "") -> None:
        """Recursively add data to tree."""
        for key, value in data.items():
            if isinstance(value, dict):
                branch = tree.add(f"[cyan]{key}[/cyan]")
                self._add_to_tree(branch, value, prefix + "  ")
            else:
                tree.add(f"[cyan]{key}[/cyan]: [white]{value}[/white]")

    def print_streaming(self, token_generator: Any) -> str:
        """
        Print streaming response token by token.

        Args:
            token_generator: Generator yielding text tokens

        Returns:
            Full response text
        """
        full_text = ""
        for token in token_generator:
            print(token, end="", flush=True)
            full_text += token
        print()
        return full_text

    def print_streaming_markdown(
        self,
        token_generator: Any,
        show_sources: str = "",
    ) -> str:
        """
        Print streaming response as markdown with live updates.

        Args:
            token_generator: Generator yielding text tokens
            show_sources: Optional sources footer

        Returns:
            Full response text
        """
        full_text = ""
        sources_text = f"\n\n---\n[dim]Sources: {show_sources}[/dim]" if show_sources else ""

        with Live(
            Markdown(full_text),
            refresh_per_second=15,
            console=self.console,
            vertical_overflow="ellipsis",
        ) as live:
            for token in token_generator:
                full_text += token
                live.update(Markdown(full_text + sources_text))
            live.update(Markdown(full_text + sources_text))

        return full_text

    def print_streaming_raw(self, token_generator: Any) -> str:
        """
        Print streaming response with markdown rendering on completion.

        Better for long responses where live updates cause flicker.

        Args:
            token_generator: Generator yielding text tokens

        Returns:
            Full response text
        """
        full_text = ""
        buffer = ""

        for token in token_generator:
            buffer += token
            full_text += token
            print(token, end="", flush=True)

        print()
        return full_text

    def clear(self) -> None:
        """Clear the console."""
        self.console.clear()

    def input(self, prompt: str = "> ") -> str:
        """Get user input with custom prompt."""
        return self.console.input(f"[bold cyan]{prompt}[/bold cyan]")

    def confirm(self, message: str) -> bool:
        """Ask for confirmation."""
        from rich.prompt import Confirm

        return Confirm.ask(f"[yellow]{message}[/yellow]")

    def spinner(
        self,
        text: str,
        spinner_name: str = "dots",
    ) -> "Progress":
        """
        Create a progress context with spinner.

        Usage:
            with console.spinner("Loading...") as progress:
                # do work
                pass
        """
        progress = Progress(
            SpinnerColumn(spinner_name, text_format=text),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=self.console,
            transient=True,
        )
        return progress

    def status(self, message: str, spinner_name: str = "dots"):
        """
        Create a status indicator.

        Usage:
            with console.status("Working..."):
                # do work
                pass
        """
        return self.console.status(message, spinner=spinner_name)


class OutputBuffer:
    """Buffer for accumulating streaming output."""

    def __init__(self, console: Console, render_md: bool = True) -> None:
        self.console = console
        self.render_md = render_md
        self.content = ""
        self._live = None

    def __enter__(self) -> "OutputBuffer":
        if self.render_md:
            self._live = Live(
                Markdown(""),
                refresh_per_second=15,
                console=self.console.console,
                vertical_overflow="visible",
            )
            self._live.__enter__()
        return self

    def __exit__(self, *args: Any) -> None:
        if self._live:
            self._live.__exit__(*args)

    def update(self, text: str) -> None:
        """Update buffered content."""
        self.content = text
        if self._live:
            self._live.update(Markdown(self.content))

    def flush(self) -> str:
        """Flush buffer and return content."""
        if self._live:
            self._live.update(Markdown(self.content))
        return self.content
