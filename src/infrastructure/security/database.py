"""
Base de datos SQLite para usuarios.

Uso:
    from src.infrastructure.security.database import UserRepository, init_db

    # Inicializar DB
    init_db()

    # Crear repo
    repo = UserRepository()

    # Agregar usuario
    repo.create_user("admin", "password123", role="admin")

    # Obtener usuario
    user = repo.get_user("admin")
"""

import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()

DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/users.db")


@dataclass
class UserRecord:
    """Registro de usuario en la base de datos."""
    username: str
    hashed_password: str
    role: str
    disabled: bool


class Database:
    """Manejador de conexión SQLite."""

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

    @contextmanager
    def get_connection(self):
        """Context manager para conexiones."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_schema(self):
        """Inicializa el schema de la base de datos."""
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    hashed_password TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
                    disabled INTEGER NOT NULL DEFAULT 0
                )
            """)


class UserRepository:
    """Repositorio de usuarios con persistencia SQLite."""

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db = Database(db_path)
        self.db.init_schema()

    def get_user(self, username: str) -> UserRecord | None:
        """Obtiene un usuario por username."""
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT username, hashed_password, role, disabled FROM users WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()
            if row:
                return UserRecord(
                    username=row["username"],
                    hashed_password=row["hashed_password"],
                    role=row["role"],
                    disabled=bool(row["disabled"])
                )
            return None

    def create_user(self, username: str, password: str, role: str = "user") -> UserRecord:
        """Crea un nuevo usuario."""
        hashed = ph.hash(password)
        with self.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO users (username, hashed_password, role) VALUES (?, ?, ?)",
                (username, hashed, role)
            )
        return UserRecord(username=username, hashed_password=hashed, role=role, disabled=False)

    def update_password(self, username: str, new_password: str) -> bool:
        """Actualiza la contraseña de un usuario."""
        hashed = ph.hash(new_password)
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE users SET hashed_password = ? WHERE username = ?",
                (hashed, username)
            )
            return cursor.rowcount > 0

    def delete_user(self, username: str) -> bool:
        """Elimina un usuario."""
        with self.db.get_connection() as conn:
            cursor = conn.execute("DELETE FROM users WHERE username = ?", (username,))
            return cursor.rowcount > 0

    def list_users(self) -> list[UserRecord]:
        """Lista todos los usuarios."""
        with self.db.get_connection() as conn:
            cursor = conn.execute("SELECT username, hashed_password, role, disabled FROM users")
            return [
                UserRecord(
                    username=row["username"],
                    hashed_password=row["hashed_password"],
                    role=row["role"],
                    disabled=bool(row["disabled"])
                )
                for row in cursor.fetchall()
            ]


_db_instance: UserRepository | None = None


def get_user_repository() -> UserRepository:
    """Obtiene instancia global del repositorio."""
    global _db_instance
    if _db_instance is None:
        _db_instance = UserRepository()
    return _db_instance


def init_db():
    """Inicializa la base de datos."""
    get_user_repository()
