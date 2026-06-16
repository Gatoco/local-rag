"""
Tests para autenticación JWT y hash de contraseñas.

Run: pytest tests/unit/test_security.py -v
"""

from datetime import timedelta

import pytest
from jose import JWTError, jwt

from src.infrastructure.security.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    SECRET_KEY,
    User,
    authenticate_user,
    create_access_token,
    get_password_hash,
    verify_password,
    verify_token,
)


class TestPasswordHashing:
    def test_hash_is_not_plain(self):
        h = get_password_hash("mypassword")
        assert h != "mypassword"
        assert len(h) > 50

    def test_verify_correct_password(self):
        h = get_password_hash("mypassword")
        assert verify_password("mypassword", h) is True

    def test_verify_wrong_password(self):
        h = get_password_hash("mypassword")
        assert verify_password("wrong", h) is False

    def test_hash_is_unique_per_call(self):
        h1 = get_password_hash("same")
        h2 = get_password_hash("same")
        assert h1 != h2


class TestAccessToken:
    def test_create_token_returns_string(self):
        token = create_access_token({"sub": "admin"})
        assert isinstance(token, str)
        assert len(token) > 20

    def test_token_contains_payload(self):
        token = create_access_token({"sub": "admin"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "admin"

    def test_token_uses_default_expiration(self):
        token = create_access_token({"sub": "admin"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "exp" in payload

    def test_custom_expiration(self):
        token = create_access_token({"sub": "admin"}, expires_delta=timedelta(minutes=5))
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "exp" in payload

    def test_algorithm_is_hs256(self):
        assert ALGORITHM == "HS256"

    def test_default_expiration_constant(self):
        assert ACCESS_TOKEN_EXPIRE_MINUTES == 60


class TestVerifyToken:
    def test_valid_token_returns_payload(self):
        token = create_access_token({"sub": "admin"})
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "admin"

    def test_invalid_token_returns_none(self):
        payload = verify_token("not.a.real.token")
        assert payload is None

    def test_tampered_token_returns_none(self):
        token = create_access_token({"sub": "admin"})
        tampered = token[:-3] + "xyz"
        payload = verify_token(tampered)
        assert payload is None

    def test_empty_token_returns_none(self):
        payload = verify_token("")
        assert payload is None


class TestUserModel:
    def test_user_is_not_admin_by_default(self):
        u = User(username="x", hashed_password="h")
        assert u.is_admin() is False

    def test_admin_role(self):
        u = User(username="x", hashed_password="h", role="admin")
        assert u.is_admin() is True

    def test_user_disabled_flag(self):
        u = User(username="x", hashed_password="h", disabled=True)
        assert u.disabled is True


class TestAuthenticateUser:
    def test_authenticate_valid_admin(self):
        user = authenticate_user("admin", "test-admin-password")
        assert user is not None
        assert user.username == "admin"
        assert user.is_admin() is True

    def test_authenticate_valid_user(self):
        user = authenticate_user("user", "test-user-password")
        assert user is not None
        assert user.username == "user"
        assert user.is_admin() is False

    def test_authenticate_wrong_password(self):
        user = authenticate_user("admin", "wrong-password")
        assert user is None

    def test_authenticate_unknown_user(self):
        user = authenticate_user("ghost", "anything")
        assert user is None
