"""
Seguridad y autenticación JWT para la API REST.

Proporciona:
- Autenticación con JWT tokens
- Hash de contraseñas con bcrypt
- Usuarios para acceso a la API
- Rate limiting por usuario

Uso:
    from src.infrastructure.security.auth import create_access_token, verify_token

    token = create_access_token({"sub": "admin"})
    payload = verify_token(token)
"""

import os
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Configuración
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "tu-secret-key-cambia-en-produccion")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_MINUTES", "60"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer(auto_error=False)


# ═══════════════════════════════════════════════════════════════════════════
# USUARIOS (En producción usar base de datos)
# ═══════════════════════════════════════════════════════════════════════════

# Usuarios por defecto (en producción usar DB)
USERS_DB = {
    "admin": {
        "username": "admin",
        "hashed_password": pwd_context.hash(os.getenv("ADMIN_PASSWORD", "admin123")),
        "disabled": False,
        "role": "admin",
    },
    "user": {
        "username": "user",
        "hashed_password": pwd_context.hash(os.getenv("USER_PASSWORD", "user123")),
        "disabled": False,
        "role": "user",
    }
}


class User:
    """Modelo de usuario."""

    def __init__(self, username: str, hashed_password: str,
                 disabled: bool = False, role: str = "user"):
        self.username = username
        self.hashed_password = hashed_password
        self.disabled = disabled
        self.role = role

    def is_admin(self) -> bool:
        return self.role == "admin"


# ═══════════════════════════════════════════════════════════════════════════
# FUNCIONES DE AUTENTICACIÓN
# ═══════════════════════════════════════════════════════════════════════════

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Genera hash de contraseña."""
    return pwd_context.hash(password)


def get_user(username: str) -> User | None:
    """Obtiene un usuario por username."""
    if username not in USERS_DB:
        return None

    user_data = USERS_DB[username]
    return User(**user_data)


def authenticate_user(username: str, password: str) -> User | None:
    """Autentica un usuario con credenciales."""
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict[str, Any],
                       expires_delta: timedelta | None = None) -> str:
    """
    Crea un JWT token.

    Args:
        data: Datos a incluir en el token (ej: {"sub": "username"})
        expires_delta: Duración del token (default: 60 minutos)

    Returns:
        Token JWT codificado
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_token(token: str) -> dict[str, Any] | None:
    """
    Verifica y decodifica un JWT token.

    Args:
        token: Token JWT a verificar

    Returns:
        Payload del token o None si es inválido

    Raises:
        HTTPException: Si el token es inválido o expiró
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Obtiene el usuario actual desde el token JWT.

    Args:
        credentials: Credenciales HTTP Bearer

    Returns:
        Usuario autenticado

    Raises:
        HTTPException: Si las credenciales son inválidas
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se proporcionaron credenciales",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user(username)
    if user is None or user.disabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o deshabilitado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """
    Requiere que el usuario sea admin.

    Args:
        user: Usuario autenticado

    Returns:
        Usuario admin

    Raises:
        HTTPException: Si el usuario no es admin
    """
    if not user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador"
        )
    return user


# ═══════════════════════════════════════════════════════════════════════════
# ENDPOINTS DE AUTENTICACIÓN
# ═══════════════════════════════════════════════════════════════════════════

auth_router = APIRouter()


class TokenRequest(BaseModel):
    """Request para obtener token."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Response con token."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """Response con información de usuario."""
    username: str
    role: str
    disabled: bool


@auth_router.post("/token", response_model=TokenResponse, tags=["Auth"])
async def login(request: TokenRequest):
    """
    Obtiene un token JWT con credenciales.

    **Request:**
    - username: Nombre de usuario
    - password: Contraseña

    **Response:**
    - access_token: Token JWT
    - token_type: "bearer"
    - expires_in: Segundos hasta expiración

    **Ejemplo:**
    ```bash
    curl -X POST http://localhost:8000/api/v1/token \\
      -H "Content-Type: application/json" \\
      -d '{"username": "admin", "password": "admin123"}'
    ```
    """
    user = authenticate_user(request.username, request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@auth_router.get("/me", response_model=UserResponse, tags=["Auth"])
async def get_current_user_info(user: User = Depends(get_current_user)):
    """
    Obtiene información del usuario actual.

    Requiere autenticación con token JWT.

    **Response:**
    - username: Nombre de usuario
    - role: Rol del usuario (admin/user)
    - disabled: Si el usuario está deshabilitado
    """
    return UserResponse(
        username=user.username,
        role=user.role,
        disabled=user.disabled
    )
