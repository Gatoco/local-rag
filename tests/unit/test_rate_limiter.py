"""
Tests para rate limiter (in-memory y Redis-backed).

Run: pytest tests/unit/test_rate_limiter.py -v
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.security.rate_limiter import RateLimiter, RedisRateLimiter


class TestRateLimiterInMemory:
    def test_first_request_allowed(self):
        limiter = RateLimiter(requests_per_minute=10, requests_per_hour=100)
        allowed, headers = limiter.is_allowed("192.168.1.1")
        assert allowed is True
        assert "X-RateLimit-Remaining" in headers or "X-RateLimit-Limit" in headers

    def test_blocks_after_minute_limit(self):
        limiter = RateLimiter(requests_per_minute=2, requests_per_hour=100)
        assert limiter.is_allowed("ip1")[0] is True
        assert limiter.is_allowed("ip1")[0] is True
        assert limiter.is_allowed("ip1")[0] is False

    def test_different_ips_independent(self):
        limiter = RateLimiter(requests_per_minute=1, requests_per_hour=100)
        assert limiter.is_allowed("ip1")[0] is True
        assert limiter.is_allowed("ip2")[0] is True
        assert limiter.is_allowed("ip1")[0] is False

    def test_endpoint_specific_key(self):
        limiter = RateLimiter(requests_per_minute=2, requests_per_hour=100)
        assert limiter.is_allowed("ip1", "/api/v1/query")[0] is True
        assert limiter.is_allowed("ip1", "/api/v1/health")[0] is True
        assert limiter.is_allowed("ip1", "/api/v1/query")[0] is False
        assert limiter.is_allowed("ip1", "/api/v1/health")[0] is False

    def test_set_endpoint_limit(self):
        limiter = RateLimiter(requests_per_minute=100, requests_per_hour=1000)
        limiter.set_endpoint_limit("/api/v1/query", 2)
        assert limiter.is_allowed("ip1", "/api/v1/query")[0] is True
        assert limiter.is_allowed("ip1", "/api/v1/query")[0] is True
        assert limiter.is_allowed("ip1", "/api/v1/query")[0] is False

    def test_old_requests_cleaned_by_window(self):
        limiter = RateLimiter(requests_per_minute=2, requests_per_hour=100)
        limiter.is_allowed("ip1")
        limiter.is_allowed("ip1")
        with patch("time.time", return_value=time.time() + 61):
            allowed, _ = limiter.is_allowed("ip1")
        assert allowed is True


class TestRedisRateLimiter:
    def test_init_defaults(self):
        limiter = RedisRateLimiter(redis_url="redis://test:6379")
        assert limiter.requests_per_minute == 60
        assert limiter.requests_per_hour == 1000

    def test_init_custom_limits(self):
        limiter = RedisRateLimiter(requests_per_minute=10, requests_per_hour=200)
        assert limiter.requests_per_minute == 10
        assert limiter.requests_per_hour == 200

    def test_init_lazy_redis(self):
        limiter = RedisRateLimiter(redis_url="redis://test:6379")
        assert limiter._redis is None

    def test_make_key_format(self):
        limiter = RedisRateLimiter(redis_url="redis://test:6379")
        key = limiter._make_key("ip1", "60")
        assert key == "ratelimit:60:ip1"

    def test_is_allowed_uses_redis(self):
        limiter = RedisRateLimiter(redis_url="redis://test:6379", requests_per_minute=2)
        mock_redis = MagicMock()
        mock_redis.zcount.return_value = 0
        mock_redis.zremrangebyscore.return_value = 0
        mock_redis.zadd.return_value = 1
        mock_redis.expire.return_value = True
        limiter._redis = mock_redis

        allowed, headers = limiter.is_allowed("ip1")
        assert allowed is True
        assert headers["X-RateLimit-Limit-Minute"] == "2"
        assert mock_redis.zadd.called

    def test_is_allowed_blocks_at_limit(self):
        limiter = RedisRateLimiter(redis_url="redis://test:6379", requests_per_minute=2)
        mock_redis = MagicMock()
        mock_redis.zcount.return_value = 5
        mock_redis.zremrangebyscore.return_value = 0
        limiter._redis = mock_redis

        allowed, _ = limiter.is_allowed("ip1")
        assert allowed is False

    def test_redis_connection_error_returns_zero_count(self):
        import redis as redis_mod

        limiter = RedisRateLimiter(redis_url="redis://test:6379")
        mock_redis = MagicMock()
        mock_redis.zcount.side_effect = redis_mod.ConnectionError("Connection refused")
        limiter._redis = mock_redis

        count = limiter._get_request_count("ip1", 60)
        assert count == 0

    def test_endpoint_appended_to_key(self):
        limiter = RedisRateLimiter(redis_url="redis://test:6379")
        mock_redis = MagicMock()
        mock_redis.zcount.return_value = 0
        mock_redis.zremrangebyscore.return_value = 0
        mock_redis.zadd.return_value = 1
        mock_redis.expire.return_value = True
        limiter._redis = mock_redis

        limiter.is_allowed("ip1", "/api/v1/query")
        minute_key = mock_redis.zadd.call_args_list[0][0][0]
        assert "ip1:/api/v1/query" in minute_key
