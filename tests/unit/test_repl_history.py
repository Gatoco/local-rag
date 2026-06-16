"""
Tests para REPL history management.
"""

from datetime import UTC

import pytest

from src.infrastructure.entrypoints.repl.history import History, HistoryEntry


class TestHistoryEntry:
    """Tests para HistoryEntry class."""

    def test_entry_init(self):
        """Test: HistoryEntry initialization."""
        entry = HistoryEntry("user", "Hello world")
        assert entry.role == "user"
        assert entry.content == "Hello world"
        assert entry.timestamp is not None

    def test_entry_to_dict(self):
        """Test: HistoryEntry serialization."""
        entry = HistoryEntry("assistant", "Response")
        result = entry.to_dict()

        assert result["role"] == "assistant"
        assert result["content"] == "Response"
        assert "timestamp" in result


class TestHistory:
    """Tests para History class."""

    def test_history_init_default(self):
        """Test: History initialization with defaults."""
        history = History()
        assert len(history) == 0
        assert history.max_entries == 1000

    def test_history_init_custom_max(self):
        """Test: History with custom max_entries."""
        history = History(max_entries=100)
        assert history.max_entries == 100

    def test_history_add_entry(self):
        """Test: Adding entries to history."""
        history = History()
        history.add("user", "Hello")
        history.add("assistant", "Hi")

        assert len(history) == 2
        assert history._entries[0].content == "Hello"
        assert history._entries[1].content == "Hi"

    def test_history_add_truncates_old_entries(self):
        """Test: Old entries are truncated when max_entries exceeded."""
        history = History(max_entries=3)
        history.add("user", "1")
        history.add("user", "2")
        history.add("user", "3")
        history.add("user", "4")

        assert len(history) == 3
        assert history._entries[0].content == "2"
        assert history._entries[2].content == "4"

    def test_history_get_messages(self):
        """Test: Getting all messages as dicts."""
        history = History()
        history.add("user", "Hello")
        history.add("assistant", "Hi")

        messages = history.get_messages()
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"
        assert "timestamp" in messages[0]

    def test_history_get_messages_for_llm(self):
        """Test: Getting messages in LLM format (role + content only)."""
        history = History()
        history.add("user", "Hello")
        history.add("assistant", "Hi")

        messages = history.get_messages_for_llm()
        assert len(messages) == 2
        assert messages == [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ]

    def test_history_clear(self):
        """Test: Clearing history."""
        history = History()
        history.add("user", "Hello")
        history.add("assistant", "Hi")

        history.clear()
        assert len(history) == 0

    def test_history_len(self):
        """Test: len() on history."""
        history = History()
        assert len(history) == 0

        history.add("user", "Hello")
        assert len(history) == 1

        history.add("assistant", "Hi")
        assert len(history) == 2

    def test_history_repr(self):
        """Test: repr of history."""
        history = History()
        history.add("user", "Hello")
        assert repr(history) == "History(entries=1)"