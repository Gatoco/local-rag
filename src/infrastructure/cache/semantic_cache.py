"""
Caché semántico para consultas RAG.

Implementa caché con TTL (Time To Live) para:
- Reducir latencia en consultas repetidas
- Disminuir carga en el LLM
- Mejorar throughput del sistema

Uso:
    from src.infrastructure.cache.semantic_cache import SemanticCache

    cache = SemanticCache(ttl_seconds=3600, max_size=1000)

    # Intentar obtener de caché
    cached = cache.get("¿Qué es Python?")
    if cached:
        return cached

    # Ejecutar RAG y guardar en caché
    result = rag_service.ask("¿Qué es Python?")
    cache.set("¿Qué es Python?", result)
"""

import hashlib
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, cast

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Entrada de caché con metadata."""
    value: Any
    created_at: float = field(default_factory=time.time)
    access_count: int = 0
    last_access: float = field(default_factory=time.time)

    def is_expired(self, ttl_seconds: int) -> bool:
        """Verifica si la entrada expiró."""
        return (time.time() - self.created_at) > ttl_seconds

    def touch(self) -> None:
        """Actualiza tiempo de último acceso y contador."""
        self.last_access = time.time()
        self.access_count += 1


class SemanticCache:
    """
    Caché semántico con TTL y LRU (Least Recently Used).

    Características:
    - TTL configurable por entrada
    - LRU eviction cuando se alcanza max_size
    - Hash semántico basado en contenido de la pregunta
    - Estadísticas de hit/miss

    Attributes:
        ttl_seconds: Tiempo de vida de las entradas (default: 1 hora)
        max_size: Máximo número de entradas (default: 1000)
        hits: Número de hits en caché
        misses: Número de misses en caché

    Example:
        cache = SemanticCache(ttl_seconds=3600, max_size=1000)

        # Guardar en caché
        cache.set("¿Qué es Python?", {"answer": "Python es...", "sources": []})

        # Obtener de caché
        result = cache.get("¿Qué es Python?")
        if result:
            print(f"Cache hit! {result}")

        # Estadísticas
        print(f"Hit rate: {cache.hit_rate:.2%}")
    """

    def __init__(self, ttl_seconds: int = 3600, max_size: int = 1000):
        """
        Inicializa la caché semántico.

        Args:
            ttl_seconds: Tiempo de vida de las entradas en segundos
            max_size: Máximo número de entradas en caché
        """
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.hits = 0
        self.misses = 0

        logger.info(f"SemanticCache inicializado: ttl={ttl_seconds}s, max_size={max_size}")

    def _hash_query(self, query: str) -> str:
        """
        Genera hash único para una consulta.

        Args:
            query: Texto de la consulta

        Returns:
            Hash SHA256 de la consulta normalizada
        """
        # Normalizar: lowercase, strip whitespace
        normalized = query.lower().strip()
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:16]

    def get(self, query: str) -> dict[str, Any] | None:
        """
        Obtiene una respuesta de caché.

        Args:
            query: La pregunta del usuario

        Returns:
            La respuesta cacheada o None si no existe/expiró
        """
        query_hash = self._hash_query(query)

        if query_hash not in self._cache:
            self.misses += 1
            logger.debug(f"Cache miss: {query[:50]}...")
            return None

        entry = self._cache[query_hash]

        # Verificar expiración
        if entry.is_expired(self.ttl_seconds):
            self._remove(query_hash)
            self.misses += 1
            logger.debug(f"Cache expired: {query[:50]}...")
            return None

        # Actualizar acceso (LRU)
        entry.touch()
        self._cache.move_to_end(query_hash)

        self.hits += 1
        logger.debug(f"Cache hit: {query[:50]}... (access_count={entry.access_count})")

        return cast(dict[str, Any] | None, entry.value)

    def set(self, query: str, value: dict[str, Any]) -> None:
        """
        Guarda una respuesta en caché.

        Args:
            query: La pregunta del usuario
            value: La respuesta a cachear
        """
        query_hash = self._hash_query(query)

        # Si ya existe, actualizar
        if query_hash in self._cache:
            self._cache[query_hash] = CacheEntry(value=value)
            self._cache.move_to_end(query_hash)
            logger.debug(f"Cache updated: {query[:50]}...")
            return

        # Eviction si está lleno (LRU)
        if len(self._cache) >= self.max_size:
            self._remove_oldest()

        # Insertar nueva entrada
        self._cache[query_hash] = CacheEntry(value=value)
        logger.debug(f"Cache set: {query[:50]}...")

    def _remove(self, query_hash: str) -> None:
        """Elimina una entrada de caché."""
        if query_hash in self._cache:
            del self._cache[query_hash]

    def _remove_oldest(self) -> None:
        """Elimina la entrada más antigua (LRU)."""
        if self._cache:
            oldest_hash = next(iter(self._cache))
            self._remove(oldest_hash)
            logger.debug("Cache eviction: removed oldest entry")

    def clear(self) -> None:
        """Limpia toda la caché."""
        self._cache.clear()
        self.hits = 0
        self.misses = 0
        logger.info("Cache cleared")

    def invalidate(self, query: str) -> bool:
        """
        Invalida una entrada específica de caché.

        Args:
            query: La pregunta a invalidar

        Returns:
            True si se eliminó, False si no existía
        """
        query_hash = self._hash_query(query)
        if query_hash in self._cache:
            self._remove(query_hash)
            logger.debug(f"Cache invalidated: {query[:50]}...")
            return True
        return False

    @property
    def size(self) -> int:
        """Número de entradas en caché."""
        return len(self._cache)

    @property
    def hit_rate(self) -> float:
        """Porcentaje de hits en caché."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return self.hits / total

    def get_stats(self) -> dict[str, Any]:
        """
        Obtiene estadísticas de la caché.

        Returns:
            Dict con estadísticas de uso
        """
        return {
            "size": self.size,
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(self.hit_rate, 4),
            "ttl_seconds": self.ttl_seconds,
            "memory_entries": len(self._cache),
        }

    def cleanup_expired(self) -> int:
        """
        Limpia entradas expiradas.

        Returns:
            Número de entradas eliminadas
        """
        expired_hashes = [
            hash for hash, entry in self._cache.items()
            if entry.is_expired(self.ttl_seconds)
        ]

        for hash in expired_hashes:
            self._remove(hash)

        if expired_hashes:
            logger.info(f"Cleaned up {len(expired_hashes)} expired entries")

        return len(expired_hashes)


class RAGServiceWithCache:
    """
    Wrapper para RAGService con caché integrado.

    Decorador que agrega caché a RAGService sin modificar su código.

    Attributes:
        rag_service: El servicio RAG subyacente
        cache: La caché semántico

    Example:
        cached_service = RAGServiceWithCache(rag_service, ttl_seconds=3600)

        # Las consultas se cachean automáticamente
        result1 = cached_service.ask("¿Qué es Python?")  # Miss
        result2 = cached_service.ask("¿Qué es Python?")  # Hit (más rápido)
    """

    def __init__(
        self,
        rag_service: Any,
        ttl_seconds: int = 3600,
        max_size: int = 1000,
        enabled: bool = True,
    ):
        """
        Inicializa el wrapper con caché.

        Args:
            rag_service: El servicio RAG a envolver
            ttl_seconds: TTL de las entradas en caché
            max_size: Máximo número de entradas en caché
            enabled: Si False, bypass de caché (todo va al RAG)
        """
        self.rag_service = rag_service
        self.cache = SemanticCache(ttl_seconds=ttl_seconds, max_size=max_size)
        self.enabled = enabled

        logger.info(
            f"RAGServiceWithCache inicializado: "
            f"enabled={enabled}, ttl={ttl_seconds}s, max_size={max_size}"
        )

    def ask(self, question: str) -> dict[str, Any]:
        """
        Ejecuta consulta RAG con caché.

        Args:
            question: La pregunta del usuario

        Returns:
            Respuesta del RAG (de caché o ejecutada)
        """
        if not self.enabled:
            logger.debug("Cache disabled, executing RAG directly")
            result = self.rag_service.ask(question)
            return cast(dict[str, Any], result)

        # Intentar caché
        cached_result = self.cache.get(question)
        if cached_result:
            logger.info(f"Cache hit for query: {question[:50]}...")
            return cast(dict[str, Any], cached_result)

        # Ejecutar RAG
        logger.info(f"Cache miss, executing RAG for: {question[:50]}...")
        result = self.rag_service.ask(question)

        # Guardar en caché
        self.cache.set(question, result)

        return cast(dict[str, Any], result)

    def get_cache_stats(self) -> dict[str, Any]:
        """Obtiene estadísticas de la caché."""
        return self.cache.get_stats()

    def clear_cache(self) -> None:
        """Limpia la caché."""
        self.cache.clear()
        logger.info("Cache cleared by user request")

    def invalidate_cache(self, question: str) -> bool:
        """Invalida una pregunta específica de la caché."""
        return self.cache.invalidate(question)
