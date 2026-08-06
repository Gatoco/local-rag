"""
LLMChatCLI - Abstract base class for CLI interfaces.

Provides common functionality for CLI tools that interact with LLMs.
"""

import argparse
import logging
import os
import sys
from abc import ABC, abstractmethod
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown

logger = logging.getLogger("llm-chat-cli")


class LLMChatCLI(ABC):
    """
    Base class for CLI interfaces that interact with LLMs.

    Provides:
    - Argument parsing
    - Config file reading (TOML)
    - Streaming response output with rich
    - Interactive command handling

    Usage:
        class MyChatCLI(LLMChatCLI):
            def stream_generate_chat(self, prompt, config, context):
                # Implement LLM interaction
                pass

        MyChatCLI().run()
    """

    DEFAULT_CONFIG_PATH = "~/.config/mylocalrag.toml"

    def __init__(self, config_path: str | None = None, description: str = "RAG Cloud Chat CLI"):
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.description = description
        self.console = Console()
        self.config: dict[str, Any] = {}
        self.logger = logger

    def read_config(self, custom_path: str | None = None) -> dict[str, Any]:
        """
        Read TOML config file.

        Args:
            custom_path: Override default config path

        Returns:
            Config dict
        """
        config_path = os.path.expanduser(custom_path or self.config_path)
        try:
            import tomllib

            with open(config_path, "rb") as f:
                config_data = tomllib.load(f)
            self.logger.info(f"Config loaded from {config_path}")
            return config_data
        except FileNotFoundError:
            self.logger.warning(f"Config file not found: {config_path}")
            return {}
        except Exception as e:
            self.logger.error(f"Error reading config from {config_path}: {e}")
            return {}

    def write_config(self, config: dict[str, Any], custom_path: str | None = None) -> None:
        """
        Write config to TOML file.

        Args:
            config: Config dict to write
            custom_path: Override default config path
        """
        config_path = os.path.expanduser(custom_path or self.config_path)
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)

            with open(config_path, "wb") as f:
                toml_str = self._dict_to_toml(config)
                f.write(toml_str.encode())
            self.logger.info(f"Config saved to {config_path}")
        except Exception as e:
            self.logger.error(f"Error writing config to {config_path}: {e}")

    def _dict_to_toml(self, d: dict, indent: int = 0) -> str:
        """Convert dict to TOML string."""
        lines = []
        for key, value in d.items():
            if isinstance(value, dict):
                lines.append(f"{key} = " + "{")
                for k, v in value.items():
                    lines.append(f"  {k} = {repr(v)}")
                lines.append("}")
            else:
                lines.append(f"{key} = {repr(value)}")
        return "\n".join(lines)

    def print_response_streaming(self, response_generator, use_markdown: bool = False) -> str:
        """
        Print streaming response using rich.

        Args:
            response_generator: Generator yielding text tokens
            use_markdown: If True, render as markdown

        Returns:
            Full response text
        """
        if use_markdown:
            return self._print_markdown_streaming(response_generator)
        else:
            return self._print_plain_streaming(response_generator)

    def _print_plain_streaming(self, response_generator) -> str:
        """Print streaming response as plain text."""
        full_text = ""
        for token in response_generator:
            print(token, end="", flush=True)
            full_text += token
        print()  # New line after response
        return full_text

    def _print_markdown_streaming(self, response_generator) -> str:
        """Print streaming response as markdown with live update."""
        full_text = ""
        with Live("", refresh_per_second=10, console=self.console) as live:
            for token in response_generator:
                full_text += token
                live.update(Markdown(full_text))
            live.update(Markdown(full_text))
        return full_text

    def args_parser(self) -> argparse.ArgumentParser:
        """
        Parse command line arguments.

        Returns:
            Configured ArgumentParser
        """
        parser = argparse.ArgumentParser(
            description=self.description, formatter_class=argparse.RawDescriptionHelpFormatter
        )

        parser.add_argument(
            "prompt",
            type=str,
            nargs="?",
            default=None,
            help="Prompt to send to the model. If not provided, enters interactive mode.",
        )
        parser.add_argument(
            "-p",
            "--provider",
            type=str,
            default=None,
            help="Provider to use (openai, anthropic, google, groq, minimax, deepseek)",
        )
        parser.add_argument(
            "-m",
            "--model",
            type=str,
            default=None,
            help="Model to use (e.g., gpt-4o-mini, claude-sonnet-4, MiniMax-M2.7)",
        )
        parser.add_argument(
            "-c",
            "--config-file",
            type=str,
            default=self.config_path,
            help=f"Path to config file (default: {self.config_path})",
        )
        parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
        parser.add_argument(
            "--markdown", action="store_true", help="Output in markdown format", default=False
        )
        parser.add_argument(
            "--system", type=str, default=None, help="System prompt / context for the conversation"
        )

        self.add_extra_args(parser)
        return parser

    @abstractmethod
    def add_extra_args(self, parser: argparse.ArgumentParser) -> None:
        """
        Add extra arguments specific to implementation.

        Override in subclass to add custom args.

        Args:
            parser: ArgumentParser instance
        """
        pass

    def cmd_rag(self, args: list[str]) -> None:
        """Handle /rag command. Override in subclass for RAG support."""
        self.console.print("[yellow]RAG not supported in this mode[/yellow]")

    def cmd_index(self, args: list[str]) -> None:
        """Handle /index command. Override in subclass to show indexed docs."""
        self.console.print("[yellow]Index info not available in this mode[/yellow]")

    def handle_command(self, line: str) -> bool:
        """
        Handle a CLI command (starts with /).

        Args:
            line: Input line

        Returns:
            True if command was handled, False otherwise
        """
        if not line.startswith("/"):
            return False

        parts = line.split()
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        handlers = {
            "/quit": (self.cmd_quit, 0),
            "/exit": (self.cmd_quit, 0),
            "/q": (self.cmd_quit, 0),
            "/help": (self.cmd_help, 0),
            "/?": (self.cmd_help, 0),
            "/providers": (self.cmd_providers, 0),
            "/p": (self.cmd_providers, 0),
            "/provider": (self.cmd_provider, 1),
            "/models": (self.cmd_models, 0),
            "/m": (self.cmd_models, 0),
            "/model": (self.cmd_model, 1),
            "/clear": (self.cmd_clear, 0),
            "/c": (self.cmd_clear, 0),
            "/history": (self.cmd_history, 0),
            "/h": (self.cmd_history, 0),
            "/rag": (self.cmd_rag, 0),
            "/index": (self.cmd_index, 0),
        }

        if command in handlers:
            handler, min_args = handlers[command]
            if len(args) < min_args:
                handler([""])
            else:
                handler(args)
            return True

        self.console.print(f"[yellow]Unknown command: {command}[/yellow]")
        self.cmd_help([])
        return True

    def cmd_quit(self, args: list[str]) -> None:
        """Exit the CLI."""
        self.console.print("[cyan]Goodbye![/cyan]")
        sys.exit(0)

    def cmd_help(self, args: list[str]) -> None:
        """Show help."""
        help_text = """
[bold]Commands:[/bold]
  /quit, /exit, /q     Exit the CLI
  /help, /?            Show this help
  /providers, /p       List available providers
  /provider <name>     Switch to provider
  /models, /m           List models for current provider
  /model <name>         Switch to model
  /clear, /c            Clear conversation history
  /history, /h          Show conversation history
  /rag [on|off|status]  Toggle or configure RAG mode
  /index [--sample]     Show indexed documents count (or sample)

[bold]Examples:[/bold]
  /provider openai      Switch to OpenAI
  /model gpt-4o-mini    Switch to gpt-4o-mini
  /rag on               Enable RAG mode
  /rag status           Show RAG status
  /index --sample       Show sample of indexed documents
  /clear                Start fresh conversation
"""
        self.console.print(help_text)

    @abstractmethod
    def cmd_providers(self, args: list[str]) -> None:
        """List available providers."""
        pass

    @abstractmethod
    def cmd_provider(self, args: list[str]) -> None:
        """Switch to a specific provider."""
        pass

    @abstractmethod
    def cmd_models(self, args: list[str]) -> None:
        """List models for current provider."""
        pass

    @abstractmethod
    def cmd_model(self, args: list[str]) -> None:
        """Switch to a specific model."""
        pass

    @abstractmethod
    def cmd_clear(self, args: list[str]) -> None:
        """Clear conversation history."""
        pass

    @abstractmethod
    def cmd_history(self, args: list[str]) -> None:
        """Show conversation history."""
        pass

    @abstractmethod
    def stream_generate_chat(
        self, prompt: str, config: dict[str, Any], context: list[dict[str, str]] | None
    ) -> None:
        """
        Generate chat response with streaming.

        Args:
            prompt: User prompt
            config: Configuration dict
            context: Conversation history as list of {"role": "user"/"assistant", "content": str}
        """
        pass

    def run(self) -> None:
        """
        Main entry point for the CLI.
        """
        parser = self.args_parser()
        args = parser.parse_args()

        if args.verbose:
            logging.basicConfig(level=logging.INFO)
            self.logger.setLevel(logging.INFO)

        self.config = self.read_config(args.config_file)

        if args.provider:
            self.config["provider"] = args.provider
        if args.model:
            self.config["model"] = args.model
        if args.system:
            self.config["system"] = args.system

        self.console.print("[bold cyan]RAG Cloud Chat CLI[/bold cyan]")
        self.console.print(f"Provider: [yellow]{self.config.get('provider', 'minimax')}[/yellow]")
        self.console.print(f"Model: [yellow]{self.config.get('model', 'MiniMax-M2.7')}[/yellow]")
        self.console.print("Type /help for commands\n")

        context: list[dict[str, str]] = []

        if args.prompt:
            self.stream_generate_chat(args.prompt, self.config, context)
        else:
            self.run_interactive(context)

    def run_interactive(self, context: list[dict[str, str]]) -> None:
        """
        Run interactive mode.

        Args:
            context: Conversation history
        """
        while True:
            try:
                user_input = input("mylocalrag > ").strip()
                if not user_input:
                    continue

                if user_input.startswith("/"):
                    if self.handle_command(user_input):
                        continue

                context.append({"role": "user", "content": user_input})

                self.console.print()
                self.stream_generate_chat(user_input, self.config, context)
                self.console.print()
            except KeyboardInterrupt:
                self.console.print("\n[cyan]Ctrl+C detected. Type /quit to exit.[/cyan]")
            except EOFError:
                break

        self.console.print("[cyan]Goodbye![/cyan]")
