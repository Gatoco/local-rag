"""
Rate limiting para la API REST.

Implementa:
- Rate limiting por IP
- Rate limiting por usuario
- Límites configurables por endpoint
- Headers de rate limit (X-RateLimit-*)
- Backend Redis para escalabilidad horizontal

Uso:
    from src.infrastructure.security.rate_limiter import RedisRateLimiter

    limiter = RedisRateLimiter(
        redis_url="redis://localhost:6379",
        requests_per_minute=60
    )
"""

import logging
import threading
import time
from collections import defaultdict
from typing import cast

import redis
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimiterUnavailableError(Exception):
    """Excepción cuando el rate limiter no puede operar (ej: Redis down)."""
    pass


class RedisRateLimiter:
    """
    Rate limiter con Redis como backend.

    Usa un sorted set de Redis para implementar ventana deslizante:
    - Score: timestamp del request
    - Member: identificador único del request

    Attributes:
        redis_url: URL de conexión a Redis
        requests_per_minute: Máximo de requests por minuto
        requests_per_hour: Máximo de requests por hora

    Example:
        limiter = RedisRateLimiter(redis_url="redis://localhost:6379")
        if not limiter.is_allowed("192.168.1.1"):
            raise HTTPException(429, "Too many requests")
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
    ):
        self.redis_url = redis_url
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self._redis = None
        self._redis_available = True

    def _get_redis(self) -> redis.Redis:
        """Lazy connection a Redis."""
        if self._redis is None:
            self._redis = redis.from_url(self.redis_url, decode_responses=True)
        return self._redis

    def _make_key(self, key: str, window: str) -> str:
        """Genera clave para Redis."""
        return f"ratelimit:{window}:{key}"

    def _cleanup_old_requests(self, key: str, window_seconds: int) -> None:
        """Elimina requests antiguos fuera de la ventana."""
        try:
            r = self._get_redis()
            cutoff = time.time() - window_seconds
            r.zremrangebyscore(self._make_key(key, str(window_seconds)), "-inf", cutoff)
            self._redis_available = True
        except redis.ConnectionError:
            self._redis_available = False
            logger.warning("Redis unavailable during cleanup")

    def _get_request_count(self, key: str, window_seconds: int) -> int:
        """Obtiene número de requests en la ventana."""
        try:
            r = self._get_redis()
            redis_key = self._make_key(key, str(window_seconds))
            cutoff = time.time() - window_seconds
            count = r.zcount(redis_key, cutoff, "+inf")
            self._redis_available = True
            return cast(int, count)
        except redis.ConnectionError as err:
            self._redis_available = False
            raise RateLimiterUnavailableError("Redis unavailable for rate limiting") from err

    def _record_request(self, key: str) -> None:
        """Registra un nuevo request."""
        try:
            r = self._get_redis()
            now = time.time()
            minute_key = self._make_key(key, "60")
            hour_key = self._make_key(key, "3600")

            r.zadd(minute_key, {str(now): now})
            r.zadd(hour_key, {str(now): now})
            r.expire(minute_key, 120)
            r.expire(hour_key, 3700)
            self._redis_available = True
        except redis.ConnectionError as err:
            self._redis_available = False
            raise RateLimiterUnavailableError("Redis unavailable for rate limiting") from err

    def is_allowed(self, key: str, endpoint: str | None = None) -> tuple[bool, dict[str, str]]:
        """
        Verifica si el request está permitido.

        Args:
            key: Identificador (IP o user ID)
            endpoint: Endpoint específico (para límites por endpoint)

        Returns:
            Tupla (allowed, headers)

        Raises:
            RateLimiterUnavailableError: Si Redis no está disponible (fail-closed)
        """
        key = f"{key}:{endpoint}" if endpoint else key

        try:
            self._cleanup_old_requests(key, 60)
            self._cleanup_old_requests(key, 3600)

            count_minute = self._get_request_count(key, 60)
            count_hour = self._get_request_count(key, 3600)

            allowed = count_minute < self.requests_per_minute and count_hour < self.requests_per_hour

            reset_minute = int(time.time()) + 60
            reset_hour = int(time.time()) + 3600

            headers = {
                "X-RateLimit-Limit-Minute": str(self.requests_per_minute),
                "X-RateLimit-Remaining-Minute": str(
                    max(0, self.requests_per_minute - count_minute - 1)
                ),
                "X-RateLimit-Reset-Minute": str(reset_minute),
                "X-RateLimit-Limit-Hour": str(self.requests_per_hour),
                "X-RateLimit-Remaining-Hour": str(max(0, self.requests_per_hour - count_hour - 1)),
                "X-RateLimit-Reset-Hour": str(reset_hour),
            }

            if allowed:
                self._record_request(key)

            return allowed, headers
        except RateLimiterUnavailableError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in rate limiter: {e}")
            raise RateLimiterUnavailableError(f"Rate limiter error: {e}") from e


class RateLimiter:
    """
    Rate limiter in-memory con ventana deslizante.

    Deprecated: Usar RedisRateLimiter para producción.

    Attributes:
        requests_per_minute: Máximo de requests por minuto
        requests_per_hour: Máximo de requests por hora
        burst_limit: Máximo de requests en ráfaga (segundos)

    Example:
        limiter = RateLimiter(requests_per_minute=60, requests_per_hour=1000)

        if not limiter.is_allowed("192.168.1.1"):
            raise HTTPException(429, "Too many requests")
    """

    def __init__(
        self, requests_per_minute: int = 60, requests_per_hour: int = 1000, burst_limit: int = 10
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_limit = burst_limit

        # Almacenamiento de requests: {key: [timestamps]}
        self._requests: dict[str, list] = defaultdict(list)

        # Limites por endpoint
        self._endpoint_limits: dict[str, int] = {}

        # Cleanup time-based en vez de request-count-based
        self._last_cleanup_time = time.time()
        self._cleanup_interval_seconds = 300.0  # Full cleanup cada 5 min
        self._cleanup_lock = threading.Lock()

    def set_endpoint_limit(self, endpoint: str, limit: int):
        """Establece límite específico para un endpoint."""
        self._endpoint_limits[endpoint] = limit

    def _cleanup_old_requests(self, key: str, window_seconds: int) -> None:
        """Elimina requests antiguos fuera de la ventana."""
        now = time.time()
        cutoff = now - window_seconds

        self._requests[key] = [ts for ts in self._requests[key] if ts > cutoff]

        if not self._requests[key]:
            del self._requests[key]

    def _cleanup_all_old_requests(self, window_seconds: int) -> None:
        """Elimina requests antiguos de todas las keys. Llamar periodicamente."""
        now = time.time()
        cutoff = now - window_seconds
        keys_to_remove = []
        for key, timestamps in self._requests.items():
            self._requests[key] = [ts for ts in timestamps if ts > cutoff]
            if not self._requests[key]:
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del self._requests[key]

    def _get_request_count(self, key: str, window_seconds: int) -> int:
        """Obtiene número de requests en la ventana."""
        self._cleanup_old_requests(key, window_seconds)
        return len(self._requests[key])

    def _record_request(self, key: str) -> None:
        """Registra un nuevo request."""
        self._requests[key].append(time.time())

    def is_allowed(self, key: str, endpoint: str | None = None) -> tuple[bool, dict[str, str]]:
        """
        Verifica si un request está permitido.

        Args:
            key: Identificador (IP o user ID)
            endpoint: Endpoint específico (opcional)

        Returns:
            Tuple[allowed, headers]
            - allowed: True si el request está permitido
            - headers: Headers de rate limit para la respuesta
        """
        now = time.time()
        headers = {}

        # Verificar límite de endpoint si existe
        if endpoint and endpoint in self._endpoint_limits:
            limit = self._endpoint_limits[endpoint]
            window = 60  # 1 minuto
            count = self._get_request_count(key, window)

            headers["X-RateLimit-Limit"] = str(limit)
            headers["X-RateLimit-Remaining"] = str(max(0, limit - count - 1))
            headers["X-RateLimit-Reset"] = str(int(now + window))

            if count >= limit:
                logger.warning(f"Rate limit excedido para {key} en {endpoint}")
                return False, headers

        # Verificar límite por minuto
        minute_count = self._get_request_count(key, 60)
        if minute_count >= self.requests_per_minute:
            logger.warning(f"Rate limit por minuto excedido para {key}")
            headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
            headers["X-RateLimit-Remaining"] = "0"
            headers["X-RateLimit-Reset"] = str(int(now + 60))
            return False, headers

        # Verificar límite por hora
        hour_count = self._get_request_count(key, 3600)
        if hour_count >= self.requests_per_hour:
            logger.warning(f"Rate limit por hora excedido para {key}")
            headers["X-RateLimit-Hour-Limit"] = str(self.requests_per_hour)
            headers["X-RateLimit-Hour-Remaining"] = "0"
            headers["X-RateLimit-Hour-Reset"] = str(int(now + 3600))
            return False, headers

        # Verificar burst limit
        burst_count = self._get_request_count(key, 1)  # 1 segundo
        if burst_count >= self.burst_limit:
            logger.warning(f"Burst limit excedido para {key}")
            headers["X-RateLimit-Burst-Limit"] = str(self.burst_limit)
            headers["X-RateLimit-Burst-Remaining"] = "0"
            headers["X-RateLimit-Burst-Reset"] = str(int(now + 1))
            return False, headers

        # Request permitido
        self._record_request(key)

        # Cleanup time-based (no basado en contador de requests)
        now = time.time()
        if now - self._last_cleanup_time > self._cleanup_interval_seconds:
            with self._cleanup_lock:
                if now - self._last_cleanup_time > self._cleanup_interval_seconds:
                    self._cleanup_all_old_requests(3600)
                    self._last_cleanup_time = now

        # Actualizar headers
        if not headers:
            headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
            headers["X-RateLimit-Remaining"] = str(
                max(0, self.requests_per_minute - minute_count - 1)
            )
            headers["X-RateLimit-Reset"] = str(int(now + 60))

        return True, headers

    def get_stats(self, key: str) -> dict[str, int]:
        """Obtiene estadísticas de rate limit para una key."""
        return {
            "requests_last_minute": self._get_request_count(key, 60),
            "requests_last_hour": self._get_request_count(key, 3600),
            "requests_last_second": self._get_request_count(key, 1),
            "limit_per_minute": self.requests_per_minute,
            "limit_per_hour": self.requests_per_hour,
            "burst_limit": self.burst_limit,
        }

    def reset(self, key: str | None = None) -> None:
        """Reseta el rate limit para una key o todas."""
        if key:
            self._requests[key] = []
        else:
            self._requests.clear()


# Rate limiter global
_global_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    """Obtiene el rate limiter global."""
    global _global_limiter
    if _global_limiter is None:
        _global_limiter = RateLimiter(
            requests_per_minute=60, requests_per_hour=1000, burst_limit=10
        )
    return _global_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware de rate limiting para FastAPI.

    Características:
    - Rate limiting por IP
    - Rate limiting por usuario (si está autenticado)
    - Headers X-RateLimit-*
    - Respuesta 429 cuando se excede el límite
    - Backend Redis para escalabilidad horizontal
    """

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_limit: int = 10,
        whitelist: list | None = None,
        redis_url: str | None = None,
    ):
        super().__init__(app)
        self.limiter = RedisRateLimiter(
            redis_url=redis_url,
            requests_per_minute=requests_per_minute,
            requests_per_hour=requests_per_hour,
        )
        self.whitelist = whitelist or []

    async def dispatch(self, request: Request, call_next):
        # Obtener identificador (IP o user ID)
        client_ip = request.client.host if request.client else "unknown"

        # Verificar whitelist
        if client_ip in self.whitelist:
            return await call_next(request)

        # Priorizar user ID si está autenticado
        user_id = None
        if hasattr(request.state, "user") and request.state.user:
            user_id = f"user:{request.state.user.username}"

        key = user_id or f"ip:{client_ip}"

        # Obtener endpoint
        endpoint = f"{request.method}:{request.url.path}"

        # Verificar rate limit
        try:
            allowed, headers = self.limiter.is_allowed(key, endpoint)
        except RateLimiterUnavailableError:
            logger.error("Rate limiter unavailable, denying request (fail-closed)")
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "detail": "Service temporarily unavailable",
                    "error": "rate_limiter_unavailable",
                },
            )

        if not allowed:
            logger.warning(f"Rate limit excedido para {key} en {endpoint}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Demasiadas solicitudes",
                    "error": "rate_limit_exceeded",
                    "retry_after": headers.get("X-RateLimit-Reset", "60"),
                },
                headers=headers,
            )

        # Ejecutar request
        response = await call_next(request)

        # Agregar headers de rate limit
        for header, value in headers.items():
            response.headers[header] = value

        return response


def rate_limit_middleware(
    requests_per_minute: int = 60,
    requests_per_hour: int = 1000,
    burst_limit: int = 10,
    whitelist: list | None = None,
):
    """
    Factory para crear middleware de rate limiting.

    Args:
        requests_per_minute: Máximo de requests por minuto
        requests_per_hour: Máximo de requests por hora
        burst_limit: Máximo de requests por segundo (ráfaga)
        whitelist: Lista de IPs exentas de rate limiting

    Returns:
        Clase de middleware configurada
    """
    return lambda app: RateLimitMiddleware(
        app,
        requests_per_minute=requests_per_minute,
        requests_per_hour=requests_per_hour,
        burst_limit=burst_limit,
        whitelist=whitelist,
    )
