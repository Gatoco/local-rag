"""
Session management for REPL - handles conversation state and persistence.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


class Session:
    def __init__(
        self,
        session_id: str | None = None,
        created_at: str | None = None,
        messages: list[dict[str, Any]] | None = None,
        rag_enabled: bool = False,
        provider: str = "minimax",
        model: str = "MiniMax-M2.7",
    ):
        self.id = session_id or str(uuid.uuid4())[:8]
        self.created_at = created_at or datetime.utcnow().isoformat() + "Z"
        self.messages: list[dict[str, Any]] = messages or []
        self.rag_enabled = rag_enabled
        self.provider = provider
        self.model = model

    def add_message(self, role: str, content: str) -> None:
        self.messages.append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "messages": self.messages,
            "rag_enabled": self.rag_enabled,
            "provider": self.provider,
            "model": self.model,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Session":
        return cls(
            session_id=data.get("id"),
            created_at=data.get("created_at"),
            messages=data.get("messages", []),
            rag_enabled=data.get("rag_enabled", False),
            provider=data.get("provider", "minimax"),
            model=data.get("model", "MiniMax-M2.7"),
        )


class SessionManager:
    def __init__(self, sessions_dir: Path | None = None):
        if sessions_dir is None:
            home = Path.home()
            self.sessions_dir = home / ".config" / "mylocalrag" / "sessions"
        else:
            self.sessions_dir = sessions_dir
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self._sessions: dict[str, Session] = {}
        self._load_sessions()

    def _session_file(self, session_id: str) -> Path:
        return self.sessions_dir / f"{session_id}.json"

    def _load_sessions(self) -> None:
        for file in self.sessions_dir.glob("*.json"):
            try:
                data = json.loads(file.read_text())
                session = Session.from_dict(data)
                self._sessions[session.id] = session
            except Exception:
                continue

    def _save_session(self, session: Session) -> None:
        file = self._session_file(session.id)
        file.write_text(json.dumps(session.to_dict(), indent=2))

    def create_session(
        self,
        provider: str = "minimax",
        model: str = "MiniMax-M2.7",
        rag_enabled: bool = False,
    ) -> Session:
        session = Session(
            rag_enabled=rag_enabled,
            provider=provider,
            model=model,
        )
        self._sessions[session.id] = session
        self._save_session(session)
        return session

    def get_session(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[Session]:
        return sorted(
            self._sessions.values(),
            key=lambda s: s.created_at,
            reverse=True,
        )

    def update_session(self, session: Session) -> None:
        self._sessions[session.id] = session
        self._save_session(session)

    def delete_session(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            file = self._session_file(session_id)
            if file.exists():
                file.unlink()
            return True
        return False

    def get_or_create_default(self) -> Session:
        sessions = self.list_sessions()
        if sessions:
            return sessions[0]
        return self.create_session()
