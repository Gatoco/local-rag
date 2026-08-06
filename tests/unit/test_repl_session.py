"""
Tests para REPL session models.
"""

from datetime import UTC, datetime

import pytest

from src.infrastructure.entrypoints.repl.session.models import (
    Message,
    Session,
    SessionState,
)


class TestMessage:
    """Tests para Message model."""

    def test_message_init_default(self):
        """Test: Message initialization with defaults."""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.sources is None
        assert msg.model is None
        assert msg.provider is None
        assert msg.latency_ms is None

    def test_message_init_custom(self):
        """Test: Message with custom fields."""
        msg = Message(
            role="assistant",
            content="Hi there",
            sources=["doc1.pdf"],
            model="gpt-4",
            provider="openai",
            latency_ms=150,
        )
        assert msg.role == "assistant"
        assert msg.sources == ["doc1.pdf"]
        assert msg.model == "gpt-4"
        assert msg.provider == "openai"
        assert msg.latency_ms == 150

    def test_message_to_dict(self):
        """Test: Message serialization."""
        msg = Message(role="user", content="test")
        result = msg.to_dict()

        assert result["role"] == "user"
        assert result["content"] == "test"
        assert "timestamp" in result

    def test_message_from_dict(self):
        """Test: Message deserialization."""
        data = {
            "role": "assistant",
            "content": "response",
            "timestamp": "2024-06-01T12:00:00Z",
        }
        msg = Message.from_dict(data)

        assert msg.role == "assistant"
        assert msg.content == "response"
        assert msg.timestamp.year == 2024


class TestSessionState:
    """Tests para SessionState model."""

    def test_session_state_defaults(self):
        """Test: SessionState with defaults."""
        state = SessionState()
        assert state.mode == "cloud"
        assert state.provider == "minimax"
        assert state.model == "MiniMax-M2.7"
        assert state.rag_enabled is True
        assert state.rag_top_k == 5
        assert state.local_model == "none"
        assert state.docs_count == 0
        assert state.theme == "dark"

    def test_session_state_custom(self):
        """Test: SessionState with custom values."""
        state = SessionState(
            mode="local",
            provider="ollama",
            model="llama3",
            rag_enabled=False,
            rag_top_k=3,
        )
        assert state.mode == "local"
        assert state.provider == "ollama"
        assert state.rag_enabled is False
        assert state.rag_top_k == 3


class TestSession:
    """Tests para Session model."""

    def test_session_init_default(self):
        """Test: Session initialization with defaults."""
        session = Session()
        assert session.id is not None
        assert len(session.id) == 8
        assert len(session.messages) == 0
        assert session.theme == "dark"
        assert isinstance(session.state, SessionState)

    def test_session_init_custom(self):
        """Test: Session with custom values."""
        session = Session(
            id="custom123",
            messages=[Message(role="user", content="Hello")],
        )
        assert session.id == "custom123"
        assert len(session.messages) == 1
        assert session.messages[0].content == "Hello"

    def test_session_add_message(self):
        """Test: Adding messages to session."""
        session = Session()
        msg = session.add_message("user", "Hello")

        assert len(session.messages) == 1
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert isinstance(msg, Message)

    def test_session_to_dict(self):
        """Test: Session serialization."""
        session = Session(id="test123")
        session.add_message("user", "test")

        result = session.to_dict()

        assert result["id"] == "test123"
        assert len(result["messages"]) == 1
        assert result["messages"][0]["content"] == "test"
        assert "created_at" in result
        assert "updated_at" in result

    def test_session_from_dict(self):
        """Test: Session deserialization."""
        data = {
            "id": "test456",
            "created_at": "2024-06-01T12:00:00Z",
            "updated_at": "2024-06-01T12:00:00Z",
            "messages": [
                {"role": "user", "content": "test", "timestamp": "2024-06-01T12:00:00Z"}
            ],
            "state": {"mode": "local", "provider": "ollama"},
            "theme": "light",
        }

        session = Session.from_dict(data)

        assert session.id == "test456"
        assert len(session.messages) == 1
        assert session.state.mode == "local"
        assert session.theme == "light"

    def test_session_from_dict_with_datetime_objects(self):
        """Test: Session.from_dict handles datetime objects."""
        now = datetime.now(UTC)
        data = {
            "id": "test789",
            "created_at": now,
            "updated_at": now,
            "messages": [],
            "state": {},
        }

        session = Session.from_dict(data)
        assert session.id == "test789"