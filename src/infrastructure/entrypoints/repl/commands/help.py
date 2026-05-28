"""
Help command - shows available commands.
"""

from typing import Any

from .base import Command, CommandResult


class HelpCommand(Command):
    name = "help"
    aliases = ["?"]
    description = "Show this help message"

    def execute(self, args: list[str], context: dict[str, Any]) -> CommandResult:
        lines = [
            "",
            "[bold]Commands:[/bold]",
            "",
            "  [cyan]mode[/cyan] / [cyan]m[/cyan]          Switch mode (local/cloud)",
            "  [cyan]provider[/cyan]        Switch cloud provider",
            "  [cyan]model[/cyan]          Switch model",
            "  [cyan]providers[/cyan]       List available providers",
            "  [cyan]models[/cyan]          List models for current provider",
            "",
            "  [cyan]rag[/cyan] [on|off]     Toggle RAG mode",
            "  [cyan]index[/cyan] [--reindex]  Index documents",
            "  [cyan]stats[/cyan]            Show index statistics",
            "",
            "  [cyan]help[/cyan] / [cyan]?[/cyan]      Show this help",
            "  [cyan]clear[/cyan]            Clear screen",
            "  [cyan]exit[/cyan] / [cyan]quit[/cyan]   Exit",
            "",
            "[bold]Examples:[/bold]",
            "  mode local            Switch to local llama.cpp",
            "  mode cloud            Switch to cloud (MiniMax)",
            "  provider groq         Switch to Groq",
            "  rag off               Disable RAG",
            "",
            "[dim]Or just type your question directly![/dim]",
            "",
        ]

        return CommandResult(
            success=True,
            message="\n".join(lines),
        )


class ExitCommand(Command):
    name = "exit"
    aliases = ["quit", "q"]
    description = "Exit the REPL"

    def execute(self, args: list[str], context: dict[str, Any]) -> CommandResult:
        return CommandResult(success=True, message="Goodbye!", data={"exit": True})


class ClearCommand(Command):
    name = "clear"
    aliases = ["cls"]
    description = "Clear the screen"

    def execute(self, args: list[str], context: dict[str, Any]) -> CommandResult:
        return CommandResult(success=True, message="", data={"clear": True})
