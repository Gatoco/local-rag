"""
Base command class for REPL commands.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class CommandResult:
    success: bool
    message: str
    data: Any = None
    should_print: bool = True


class Command(ABC):
    """Base class for all REPL commands."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Command name (e.g., 'help', 'model')."""
        pass

    @property
    @abstractmethod
    def aliases(self) -> list[str]:
        """Alternative names for the command."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Short description for help."""
        pass

    @abstractmethod
    def execute(self, args: list[str], context: dict[str, Any]) -> CommandResult:
        """Execute the command with args and current context."""
        pass

    def matches(self, cmd_name: str) -> bool:
        """Check if this command matches the given name."""
        return cmd_name in [self.name] + self.aliases