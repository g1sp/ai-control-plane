"""Tests for Redis-backed rate limiter (runs against in-memory backend)."""

import os
import pytest

from src.services.redis_rate_limiter import RateLimiter, _MemoryBackend, _RedisBackend


@pytest.fixture
def limiter():
    rl = RateLimiter.__new__(RateLimiter)
    rl._backend = _MemoryBackend()
    rl._limits = {"per_minute": (5, 60), "per_hour": (100, 3600)}
    rl._using_redis = False
    return rl


def test_allows_up_to_limit(limiter):
    for i in range(5):
        allowed, info = limiter.check("alice", "per_minute")
        assert allowed, f"Request {i+1} should be allowed"
        assert info["remaining"] == 4 - i


def test_blocks_over_limit(limiter):
    for _ in range(5):
        limiter.check("alice", "per_minute")
    allowed, info = limiter.check("alice", "per_minute")
    assert not allowed
    assert info["remaining"] == 0


def test_different_users_independent(limiter):
    for _ in range(5):
        limiter.check("alice", "per_minute")
    allowed, _ = limiter.check("bob", "per_minute")
    assert allowed


def test_unknown_window_passes(limiter):
    allowed, info = limiter.check("alice", "per_decade")
    assert allowed
    assert "error" in info


def test_reset_clears_counts(limiter):
    for _ in range(5):
        limiter.check("alice", "per_minute")
    limiter.reset("alice")
    allowed, _ = limiter.check("alice", "per_minute")
    assert allowed


def test_backend_type_memory(limiter):
    assert limiter.backend_type == "memory"


def test_configure_custom_limit(limiter):
    limiter.configure("burst", 2, 10)
    limiter.check("alice", "burst")
    limiter.check("alice", "burst")
    allowed, _ = limiter.check("alice", "burst")
    assert not allowed


def test_returns_info_dict(limiter):
    allowed, info = limiter.check("alice", "per_minute")
    assert "limit" in info
    assert "used" in info
    assert "remaining" in info
    assert "window_seconds" in info
    assert "backend" in info


def test_redis_backend_not_available_falls_back(monkeypatch):
    """When Redis is unavailable, RateLimiter silently falls back to memory."""
    monkeypatch.setenv("RATE_LIMIT_BACKEND", "redis")
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:19999")  # nothing listening
    rl = RateLimiter()
    assert rl.backend_type == "memory"
    allowed, _ = rl.check("alice", "per_minute")
    assert allowed


def test_memory_backend_sliding_window():
    """Entries older than window_seconds should not count."""
    import time
    backend = _MemoryBackend()
    key = "test_key"
    backend.is_allowed(key, 2, 1)
    backend.is_allowed(key, 2, 1)
    time.sleep(1.1)
    allowed, count = backend.is_allowed(key, 2, 1)
    assert allowed
    assert count == 1
