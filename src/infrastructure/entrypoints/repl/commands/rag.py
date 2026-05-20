"""
RAG commands for toggling and configuring RAG mode.
"""

from .base import Command, CommandResult


class RagCommand(Command):
    name = "rag"
    aliases = []
    description = "RAG mode control: /rag [on|off|status|topk <n>]"

    def execute(self, args: list[str], context: dict[str, Any]) -> CommandResult:
        rag_enabled = context.get("rag_enabled", False)
        rag_top_k = context.get("rag_top_k", 5)
        collection_count = context.get("collection_count", 0)

        if not args:
            new_state = not rag_enabled
            action = "enabled" if new_state else "disabled"
            return CommandResult(
                success=True,
                message=f"RAG mode {action}",
                data={"rag_enabled": new_state},
            )

        subcmd = args[0].lower()

        if subcmd == "on":
            return CommandResult(
                success=True,
                message="RAG mode enabled",
                data={"rag_enabled": True},
            )

        elif subcmd == "off":
            return CommandResult(
                success=True,
                message="RAG mode disabled",
                data={"rag_enabled": False},
            )

        elif subcmd == "status":
            status = "ON" if rag_enabled else "OFF"
            lines = [
                "",
                f"RAG Status: {status}",
                f"Top_k: {rag_top_k}",
                f"Documents indexed: {collection_count}",
                "",
            ]
            return CommandResult(success=True, message="\n".join(lines))

        elif subcmd == "topk" and len(args) > 1:
            try:
                k = int(args[1])
                if k < 1 or k > 20:
                    return CommandResult(
                        success=False,
                        message="top_k must be between 1 and 20",
                    )
                return CommandResult(
                    success=True,
                    message=f"top_k set to {k}",
                    data={"rag_top_k": k},
                )
            except ValueError:
                return CommandResult(
                    success=False,
                    message=f"Invalid number: {args[1]}",
                )

        else:
            return CommandResult(
                success=False,
                message="Usage: /rag [on|off|status|topk <n>]",
            )


class IndexCommand(Command):
    name = "index"
    aliases = []
    description = "Index documents: /index [--reindex] [directory]"

    def execute(self, args: list[str], context: dict[str, Any]) -> CommandResult:
        reindex = "--reindex" in args
        if reindex:
            args = [a for a in args if a != "--reindex"]

        directory = args[0] if args else "./docs_to_ingest"

        return CommandResult(
            success=True,
            message=f"Indexing started: {directory}" + (" (reindex)" if reindex else ""),
            data={
                "action": "index",
                "directory": directory,
                "reindex": reindex,
            },
        )


class StatsCommand(Command):
    name = "stats"
    aliases = ["info", "collection"]
    description = "Show indexed documents statistics"

    def execute(self, args: list[str], context: dict[str, Any]) -> CommandResult:
        collection_count = context.get("collection_count", 0)

        lines = [
            "",
            "╭─────────────────────────────────────────────╮",
            "│       Indexed Documents Stats              │",
            "╰─────────────────────────────────────────────╯",
            f"  Total chunks: {collection_count}",
            f"  Collection: local_rag_docs",
            f"  Embedding: BAAI/bge-large-en-v1.5 (1024 dims)",
            "",
        ]

        if collection_count > 0:
            lines.append("  ✓ Documents are indexed and ready for RAG queries")
        else:
            lines.append("  ✗ No documents indexed. Use /index to add documents")

        lines.append("")
        return CommandResult(success=True, message="\n".join(lines))