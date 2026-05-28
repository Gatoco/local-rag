"""
Rich Console wrapper for REPL output.

Provides styled output using rich library with consistent formatting.
"""

from typing import Any

from rich.console import Console as RichConsole
from rich.markdown import Markdown
from rich.style import Style
from rich.theme import Theme

custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red",
    "success": "green",
    "prompt": "bold cyan",
    "mode.local": "green",
    "mode.cloud": "cyan",
    "rag.on": "green",
    "rag.off": "yellow",
})


class Console:
    """
    Rich console wrapper for styled output.

    Usage:
        console = Console()
        console.print("Hello world")
        console.print("[success]Success![/success]")
        console.print_markdown("# Header\nSome text")
    """

    def __init__(self) -> None:
        self.console = RichConsole(theme=custom_theme)

    def print(self, *args: Any, style: str | None = None, **kwargs: Any) -> None:
        """Print with optional style."""
        if style:
            self.console.print(*args, style=style, **kwargs)
        else:
            self.console.print(*args, **kwargs)

    def print_markdown(self, text: str) -> None:
        """Print markdown-formatted text."""
        self.console.print(Markdown(text))

    def print_error(self, message: str) -> None:
        """Print error message in red."""
        self.console.print(f"[red]Error: {message}[/red]")

    def print_warning(self, message: str) -> None:
        """Print warning message in yellow."""
        self.console.print(f"[yellow]Warning: {message}[/yellow]")

    def print_success(self, message: str) -> None:
        """Print success message in green."""
        self.console.print(f"[green]✓ {message}[/green]")

    def print_info(self, message: str) -> None:
        """Print info message in cyan."""
        self.console.print(f"[cyan]{message}[/cyan]")

    def print_dim(self, message: str) -> None:
        """Print dimmed message."""
        self.console.print(f"[dim]{message}[/dim]")

    def print_bold(self, message: str) -> None:
        """Print bold message."""
        self.console.print(f"[bold]{message}[/bold]")

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

    def print_streaming_markdown(self, token_generator: Any) -> str:
        """
        Print streaming response as markdown with live updates.

        Args:
            token_generator: Generator yielding text tokens

        Returns:
            Full response text
        """
        from rich.live import Live

        full_text = ""
        with Live(Markdown(full_text), refresh_per_second=10, console=self.console) as live:
            for token in token_generator:
                full_text += token
                live.update(Markdown(full_text))
            live.update(Markdown(full_text))
        return full_text

    def clear(self) -> None:
        """Clear the console."""
        self.console.clear()

    def input(self, prompt: str = "> ") -> str:
        """Get user input with custom prompt."""
        return self.console.input(prompt)
