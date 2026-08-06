"""
Tests para SemanticCache (TTL + LRU + hit/miss).

Run: pytest tests/unit/test_semantic_cache.py -v
"""

import time
from unittest.mock import patch

import pytest

from src.infrastructure.cache.semantic_cache import CacheEntry, SemanticCache


class TestCacheEntry:
    def test_new_entry_not_expired(self):
        e = CacheEntry(value="x")
        assert e.is_expired(60) is False

    def test_old_entry_expired(self):
        e = CacheEntry(value="x", created_at=time.time() - 120)
        assert e.is_expired(60) is True

    def test_touch_updates_access(self):
        e = CacheEntry(value="x")
        first = e.last_access
        time.sleep(0.01)
        e.touch()
        assert e.last_access > first
        assert e.access_count == 1
        e.touch()
        assert e.access_count == 2


class TestSemanticCacheBasic:
    def test_init_defaults(self):
        c = SemanticCache()
        assert c.ttl_seconds == 3600
        assert c.max_size == 1000
        assert c.hits == 0
        assert c.misses == 0
        assert c.size == 0

    def test_set_and_get(self):
        c = SemanticCache()
        c.set("¿Qué es Python?", {"answer": "Un lenguaje"})
        result = c.get("¿Qué es Python?")
        assert result == {"answer": "Un lenguaje"}

    def test_get_missing_returns_none(self):
        c = SemanticCache()
        result = c.get("nunca seteada")
        assert result is None
        assert c.misses == 1

    def test_set_increases_size(self):
        c = SemanticCache()
        c.set("q1", {"a": 1})
        assert c.size == 1
        c.set("q2", {"a": 2})
        assert c.size == 2

    def test_update_existing(self):
        c = SemanticCache()
        c.set("q1", {"a": 1})
        c.set("q1", {"a": 2})
        assert c.size == 1
        assert c.get("q1") == {"a": 2}

    def test_query_normalization(self):
        c = SemanticCache()
        c.set("Hola Mundo", {"a": 1})
        assert c.get("HOLA MUNDO") is not None
        assert c.get("  hola mundo  ") is not None

    def test_clear(self):
        c = SemanticCache()
        c.set("q1", {"a": 1})
        c.set("q2", {"a": 2})
        c.clear()
        assert c.size == 0
        assert c.hits == 0
        assert c.misses == 0


class TestSemanticCacheStats:
    def test_hits_increment(self):
        c = SemanticCache()
        c.set("q1", {"a": 1})
        c.get("q1")
        c.get("q1")
        assert c.hits == 2

    def test_misses_increment(self):
        c = SemanticCache()
        c.get("nope1")
        c.get("nope2")
        assert c.misses == 2

    def test_hit_rate_zero_when_empty(self):
        c = SemanticCache()
        assert c.hit_rate == 0.0

    def test_hit_rate_calculation(self):
        c = SemanticCache()
        c.set("q1", {"a": 1})
        c.get("q1")
        c.get("q1")
        c.get("miss")
        assert c.hit_rate == pytest.approx(2 / 3)


class TestSemanticCacheTTL:
    def test_expired_entry_returns_none(self):
        c = SemanticCache(ttl_seconds=1)
        c.set("q1", {"a": 1})
        with patch.object(CacheEntry, "is_expired", return_value=True):
            result = c.get("q1")
        assert result is None
        assert c.misses == 1

    def test_expired_entry_removed(self):
        c = SemanticCache(ttl_seconds=1)
        c.set("q1", {"a": 1})
        with patch.object(CacheEntry, "is_expired", return_value=True):
            c.get("q1")
        assert c.size == 0


class TestSemanticCacheLRU:
    def test_eviction_when_full(self):
        c = SemanticCache(max_size=2)
        c.set("q1", {"a": 1})
        c.set("q2", {"a": 2})
        c.set("q3", {"a": 3})
        assert c.size == 2
        assert c.get("q1") is None
        assert c.get("q2") is not None
        assert c.get("q3") is not None

    def test_lru_promotes_accessed_entry(self):
        c = SemanticCache(max_size=2)
        c.set("q1", {"a": 1})
        c.set("q2", {"a": 2})
        c.get("q1")
        c.set("q3", {"a": 3})
        assert c.get("q1") is not None
        assert c.get("q2") is None


class TestInvalidate:
    def test_invalidate_existing(self):
        c = SemanticCache()
        c.set("q1", {"a": 1})
        assert c.invalidate("q1") is True
        assert c.size == 0

    def test_invalidate_missing(self):
        c = SemanticCache()
        assert c.invalidate("nunca") is False
