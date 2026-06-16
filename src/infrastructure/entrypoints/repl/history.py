"""
In-memory conversation history for current REPL session.
"""

from datetime import UTC, datetime
from typing import Any


class HistoryEntry:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content
        self.timestamp = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat().replace("+00:00", "Z"),
        }


class History:
    def __init__(self, max_entries: int = 1000):
        self._entries: list[HistoryEntry] = []
        self.max_entries = max_entries

    def add(self, role: str, content: str) -> None:
        self._entries.append(HistoryEntry(role, content))
        if len(self._entries) > self.max_entries:
            self._entries = self._entries[-self.max_entries :]

    def get_messages(self) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self._entries]

    def get_messages_for_llm(self) -> list[dict[str, str]]:
        return [{"role": e.role, "content": e.content} for e in self._entries]

    def clear(self) -> None:
        self._entries.clear()

    def __len__(self) -> int:
        return len(self._entries)

    def __repr__(self) -> str:
        return f"History(entries={len(self._entries)})"
