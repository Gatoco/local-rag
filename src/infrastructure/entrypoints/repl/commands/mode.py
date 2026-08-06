"""
Mode command for switching between local and cloud.
"""

from typing import Any

from ..adapters.factory import get_available_local_models, get_default_local_model
from .base import Command, CommandResult


class ModeCommand(Command):
    """
    Command to switch between local (llama.cpp) and cloud (MiniMax, Groq, etc.) modes.

    Usage:
        /mode              Show current mode
        /mode local        Switch to local mode (llama.cpp)
        /mode cloud        Switch to cloud mode (MiniMax by default)
        /mode list         List available modes

    Examples:
        /mode
        /mode local
        /mode cloud
        /mode list
    """

    name = "mode"
    aliases = ["m"]
    description = "Switch between local and cloud mode"

    def execute(self, args: list[str], context: dict[str, Any]) -> CommandResult:
        current_mode = context.get("mode", "cloud")

        if not args:
            return self._show_status(current_mode, context)

        subcmd = args[0].lower()

        if subcmd == "list":
            return self._list_modes(current_mode)

        if subcmd == "local":
            return self._switch_to_local(context)

        if subcmd == "cloud":
            return self._switch_to_cloud(context)

        if subcmd in ("status", "info"):
            return self._show_status(current_mode, context)

        return CommandResult(
            success=False,
            message=f"Unknown mode subcommand: {subcmd}\nUsage: /mode [local|cloud|list]",
        )

    def _show_status(self, current_mode: str, context: dict[str, Any]) -> CommandResult:
        """Show current mode status."""
        from ..adapters.factory import get_default_local_model

        local_model = get_default_local_model()
        model_name = local_model.split("/")[-1] if local_model else "none"

        status_lines = [
            "",
            f"Current mode: [bold]{current_mode.upper()}[/bold]",
            "",
        ]

        if current_mode == "local":
            status_lines.extend(
                [
                    f"Model: [cyan]{model_name}[/cyan]",
                    "Backend: [green]llama.cpp[/green]",
                ]
            )
        else:
            provider = context.get("provider", "minimax")
            model = context.get("model", "MiniMax-M2.7")
            status_lines.extend(
                [
                    f"Provider: [cyan]{provider}[/cyan]",
                    f"Model: [cyan]{model}[/cyan]",
                    "Backend: [cyan]cloud[/cyan]",
                ]
            )

        status_lines.append("")

        return CommandResult(
            success=True,
            message="\n".join(status_lines),
        )

    def _list_modes(self, current_mode: str) -> CommandResult:
        """List available modes."""
        available_models = get_available_local_models()

        lines = [
            "",
            "[bold]Available Modes:[/bold]",
            "",
            "  [green]local[/green]   - llama.cpp (local GGUF model)",
            "  [cyan]cloud[/cyan]    - Cloud LLM (MiniMax by default)",
            "",
            "[bold]Local Models:[/bold]",
        ]

        if available_models:
            for model in available_models:
                lines.append(f"  [dim]- {model}[/dim]")
        else:
            lines.append("  [dim]No models found in ./models[/dim]")

        lines.append("")
        lines.append("Usage: /mode local  |  /mode cloud")

        return CommandResult(
            success=True,
            message="\n".join(lines),
        )

    def _switch_to_local(self, context: dict[str, Any]) -> CommandResult:
        """Switch to local mode."""
        default_model = get_default_local_model()

        if not default_model:
            return CommandResult(
                success=False,
                message="No local model found.\n"
                "Set LLAMA_CPP_MODEL_PATH in .env or add a GGUF model to ./models",
            )

        model_name = default_model.split("/")[-1]

        return CommandResult(
            success=True,
            message="Switching to local mode...",
            data={
                "mode": "local",
                "local_model": model_name,
            },
        )

    def _switch_to_cloud(self, context: dict[str, Any]) -> CommandResult:
        """Switch to cloud mode."""
        default_provider = context.get("provider", "minimax")
        default_model = context.get("model", "MiniMax-M2.7")

        return CommandResult(
            success=True,
            message=f"Switching to cloud mode (default: {default_provider})...",
            data={
                "mode": "cloud",
                "provider": default_provider,
                "model": default_model,
            },
        )
