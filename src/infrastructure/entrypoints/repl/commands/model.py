"""
Model and provider commands.
"""

from typing import Any

from src.infrastructure.adapters.cloud_llm_adapter import PROVIDER_CONFIG

from .base import Command, CommandResult


class ProvidersCommand(Command):
    name = "providers"
    aliases = []
    description = "List available providers"

    def execute(self, args: list[str], context: dict[str, Any]) -> CommandResult:
        current = context.get("provider", "minimax")

        lines = ["", "Available Providers:", ""]
        for provider_id, _cfg in PROVIDER_CONFIG.items():
            marker = " ← current" if provider_id == current else ""
            lines.append(f"  {provider_id}{marker}")

        lines.append("")

        return CommandResult(success=True, message="\n".join(lines))


class ProviderCommand(Command):
    name = "provider"
    aliases = []
    description = "Switch provider: /provider <name>"

    def execute(self, args: list[str], context: dict[str, Any]) -> CommandResult:
        if not args:
            return CommandResult(
                success=False,
                message="Usage: /provider <name>\nAvailable: " + ", ".join(PROVIDER_CONFIG.keys()),
            )

        new_provider = args[0].lower()
        if new_provider not in PROVIDER_CONFIG:
            return CommandResult(
                success=False,
                message=f"Unknown provider: {new_provider}\nAvailable: " + ", ".join(PROVIDER_CONFIG.keys()),
            )

        default_model = PROVIDER_CONFIG[new_provider]["default_model"]

        return CommandResult(
            success=True,
            message=f"Switched to {new_provider} (model: {default_model})",
            data={"provider": new_provider, "model": default_model},
        )


class ModelsCommand(Command):
    name = "models"
    aliases = []
    description = "List models for current provider"

    def execute(self, args: list[str], context: dict[str, Any]) -> CommandResult:
        provider = context.get("provider", "minimax")
        current_model = context.get("model", "")

        cfg = PROVIDER_CONFIG.get(provider, {})
        models = cfg.get("models", [])

        lines = [f"Models for {provider}:", ""]
        for model in models:
            marker = " ← current" if model == current_model else ""
            lines.append(f"  {model}{marker}")

        return CommandResult(success=True, message="\n".join(lines))


class ModelCommand(Command):
    name = "model"
    aliases = []
    description = "Switch model: /model <name>"

    def execute(self, args: list[str], context: dict[str, Any]) -> CommandResult:
        if not args:
            return CommandResult(
                success=False,
                message="Usage: /model <name>\nUse /models to see available models.",
            )

        new_model = args[0]
        provider = context.get("provider", "minimax")
        available_models = PROVIDER_CONFIG.get(provider, {}).get("models", [])

        if new_model not in available_models:
            return CommandResult(
                success=False,
                message=f"Unknown model: {new_model}\nAvailable: " + ", ".join(available_models),
            )

        return CommandResult(
            success=True,
            message=f"Switched to model: {new_model}",
            data={"model": new_model},
        )
