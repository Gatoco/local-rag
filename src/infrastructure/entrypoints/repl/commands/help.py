"""
Help command - shows available commands.
"""

from .base import Command, CommandResult


class HelpCommand(Command):
    name = "help"
    aliases = ["?"]
    description = "Show this help message"

    def execute(self, args: list[str], context: dict[str, Any]) -> CommandResult:
        commands = context.get("commands", {})

        lines = [
            "",
            "╭─────────────────────────────────────────────╮",
            "│          MyLocalRAG Commands               │",
            "╰─────────────────────────────────────────────╯",
            "",
            "  COMMANDS:",
            "    /help, /?      Show this help",
            "    /exit, /quit   Exit the REPL",
            "    /clear        Clear the screen",
            "",
            "  MODEL & PROVIDER:",
            "    /providers     List available providers",
            "    /provider <n>  Switch provider (minimax/groq/openai/deepseek)",
            "    /models        List models for current provider",
            "    /model <name>  Switch model",
            "",
            "  RAG:",
            "    /rag           Toggle RAG mode (on/off)",
            "    /rag status    Show RAG status",
            "    /rag topk <n>  Set top_k (1-20)",
            "    /stats         Show indexed documents stats",
            "    /index              Index ./docs_to_ingest",
            "    /index --reindex    Re-index from scratch",
            "    /index <dir>        Index specific directory",
            "",
            "  SESSIONS:",
            "    /session list      List saved sessions",
            "    /session new       Create new session",
            "    /session save      Save current session",
            "",
            "  EXAMPLES:",
            "    /rag on            Enable RAG",
            "    /provider groq     Switch to Groq",
            "    /index --reindex   Rebuild index",
            "",
            "  Or just type your question directly!",
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
        return CommandResult(success=True, message="\033[2J\033[H", data={"clear": True})