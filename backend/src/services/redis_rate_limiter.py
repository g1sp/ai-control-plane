"""
Redis-backed sliding window rate limiter.

Falls back to in-memory automatically if Redis is unavailable.
Config:
  RATE_LIMIT_BACKEND=redis|memory  (default: memory)
  REDIS_URL=redis://localhost:6379  (default)

Sliding window uses a Redis sorted set per (user, window) pair.
Members are unique tokens, scores are Unix timestamps.
This gives sub-millisecond per-request cost and O(log N) trimming.
"""

import logging
import os
import time
from collections import defaultdict
from threading import Lock
from typing import Optional

logger = logging.getLogger(__name__)

_BACKEND = os.environ.get("RATE_LIMIT_BACKEND", "memory").lower()
_REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")


class _RedisBackend:
    def __init__(self, url: str):
        import redis as redis_lib
        self._client = redis_lib.from_url(url, decode_responses=True, socket_connect_timeout=1)
        self._client.ping()
        logger.info("Redis rate limiter connected: %s", url)

    def is_allowed(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        """Sliding window check. Returns (allowed, current_count)."""
        now = time.time()
        window_start = now - window_seconds
        pipe = self._client.pipeline()
        pipe.zremrangebyscore(key, "-inf", window_start)
        pipe.zadd(key, {f"{now}:{id(object())}": now})
        pipe.zcard(key)
        pipe.expire(key, window_seconds + 1)
        results = pipe.execute()
        count = results[2]
        if count > limit:
            # Undo the zadd — we're over limit
            self._client.zpopmax(key)
            return False, count - 1
        return True, count

    def reset(self, key: str) -> None:
        self._client.delete(key)


class _MemoryBackend:
    def __init__(self):
        self._windows: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def is_allowed(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        now = time.time()
        window_start = now - window_seconds
        with self._lock:
            timestamps = self._windows[key]
            # Trim expired entries
            self._windows[key] = [t for t in timestamps if t > window_start]
            count = len(self._windows[key])
            if count >= limit:
                return False, count
            self._windows[key].append(now)
            return True, count + 1

    def reset(self, key: str) -> None:
        with self._lock:
            self._windows.pop(key, None)


def _build_backend():
    if _BACKEND == "redis":
        try:
            return _RedisBackend(_REDIS_URL)
        except Exception as e:
            logger.warning("Redis unavailable (%s) — falling back to in-memory rate limiting", e)
    return _MemoryBackend()


class RateLimiter:
    """
    Public interface. Single instance per process.
    Limits: (requests, window_seconds) keyed by window name.
    """

    _DEFAULT_LIMITS = {
        "per_minute": (60, 60),
        "per_hour": (1000, 3600),
        "per_day": (10000, 86400),
    }

    def __init__(self):
        self._backend = _build_backend()
        self._limits = dict(self._DEFAULT_LIMITS)
        self._using_redis = isinstance(self._backend, _RedisBackend)

    def configure(self, window: str, requests: int, seconds: int) -> None:
        self._limits[window] = (requests, seconds)

    def check(self, user_id: str, window: str = "per_minute") -> tuple[bool, dict]:
        """
        Check rate limit for user. Returns (allowed, info_dict).
        info_dict keys: limit, used, remaining, window_seconds, backend
        """
        if window not in self._limits:
            return True, {"error": "unknown_window"}

        limit, window_seconds = self._limits[window]
        key = f"rl:{user_id}:{window}"

        try:
            allowed, used = self._backend.is_allowed(key, limit, window_seconds)
        except Exception as e:
            logger.error("Rate limiter backend error: %s — allowing request", e)
            return True, {"error": str(e), "fallback": True}

        return allowed, {
            "limit": limit,
            "used": used,
            "remaining": max(0, limit - used),
            "window_seconds": window_seconds,
            "backend": "redis" if self._using_redis else "memory",
        }

    def reset(self, user_id: str) -> None:
        for window in self._limits:
            try:
                self._backend.reset(f"rl:{user_id}:{window}")
            except Exception as e:
                logger.error("Rate limiter reset error for %s/%s: %s", user_id, window, e)

    @property
    def backend_type(self) -> str:
        return "redis" if self._using_redis else "memory"


_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    global _limiter
    if _limiter is None:
        _limiter = RateLimiter()
    return _limiter
