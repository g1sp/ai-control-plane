"""Distributed rate limiting for multi-instance deployment."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from enum import Enum


class RateLimitWindow(str, Enum):
    """Rate limit time windows."""
    PER_MINUTE = "per_minute"
    PER_HOUR = "per_hour"
    PER_DAY = "per_day"


class DistributedRateLimiter:
    """Distributed rate limiter using cache backend."""

    def __init__(self, cache_manager):
        """Initialize rate limiter."""
        self.cache = cache_manager
        # Config: (requests, window_seconds)
        self.limits: Dict[str, Tuple[int, int]] = {
            RateLimitWindow.PER_MINUTE: (60, 60),
            RateLimitWindow.PER_HOUR: (1000, 3600),
            RateLimitWindow.PER_DAY: (10000, 86400),
        }

    def set_limit(self, window: str, requests: int, seconds: int) -> None:
        """Set rate limit for window."""
        self.limits[window] = (requests, seconds)

    async def check_limit(self, user_id: str, window: str) -> Tuple[bool, Dict[str, int]]:
        """Check if user exceeds rate limit."""
        if window not in self.limits:
            return True, {"error": "unknown_window"}

        limit, window_seconds = self.limits[window]

        # Get current window index
        now = datetime.utcnow()
        window_index = int(now.timestamp() / window_seconds)
        key = f"rl:{user_id}:{window}:{window_index}"

        # Get current count
        count = await self.cache.backend.get(key)
        if count is None:
            count = 0

        # Check if limit exceeded
        exceeded = count >= limit

        # Increment for next call
        if not exceeded:
            await self.cache.backend.set(key, count + 1, window_seconds + 10)

        return not exceeded, {
            "limit": limit,
            "used": count + 1 if not exceeded else count,
            "remaining": max(0, limit - (count + 1 if not exceeded else count)),
            "window_seconds": window_seconds,
        }

    async def get_status(self, user_id: str) -> Dict[str, Dict[str, int]]:
        """Get rate limit status for user."""
        status = {}

        for window, (limit, window_seconds) in self.limits.items():
            allowed, info = await self.check_limit(user_id, window)
            status[window] = info

        return status

    async def reset_user(self, user_id: str) -> None:
        """Reset all rate limits for user."""
        # In production, would need pattern-based deletion
        # For now, limits auto-expire after window
        pass

    async def is_whitelisted(self, user_id: str) -> bool:
        """Check if user is whitelisted (no rate limits)."""
        whitelisted = await self.cache.backend.get(f"whitelist:{user_id}")
        return whitelisted is True

    async def whitelist_user(self, user_id: str, ttl_seconds: int = 86400 * 30) -> None:
        """Add user to whitelist (no rate limits)."""
        await self.cache.backend.set(f"whitelist:{user_id}", True, ttl_seconds)

    async def remove_whitelist(self, user_id: str) -> None:
        """Remove user from whitelist."""
        await self.cache.backend.delete(f"whitelist:{user_id}")


class AdaptiveRateLimiter:
    """Adaptive rate limiter based on user behavior."""

    def __init__(self, cache_manager, base_limiter: DistributedRateLimiter):
        """Initialize adaptive rate limiter."""
        self.cache = cache_manager
        self.base_limiter = base_limiter

    async def adjust_limits(self, user_id: str, factor: float) -> None:
        """Adjust limits for user (factor > 1 = more permissive)."""
        await self.cache.backend.set(f"limit_factor:{user_id}", factor, ttl_seconds=3600)

    async def get_effective_limit(self, user_id: str, window: str) -> int:
        """Get effective limit with adjustments."""
        limit, _ = self.base_limiter.limits.get(window, (100, 60))

        factor = await self.cache.backend.get(f"limit_factor:{user_id}")
        if factor:
            limit = int(limit * factor)

        return limit

    async def check_adaptive_limit(self, user_id: str, window: str) -> Tuple[bool, Dict[str, int]]:
        """Check adaptive rate limit."""
        if await self.base_limiter.is_whitelisted(user_id):
            return True, {"limited": False, "reason": "whitelisted"}

        # Get effective limit
        effective_limit, window_seconds = self.base_limiter.limits.get(window, (100, 60))
        factor = await self.cache.backend.get(f"limit_factor:{user_id}")
        if factor:
            effective_limit = int(effective_limit * factor)

        # Check against effective limit
        now = datetime.utcnow()
        window_index = int(now.timestamp() / window_seconds)
        key = f"rl:{user_id}:{window}:{window_index}"

        count = await self.cache.backend.get(key)
        if count is None:
            count = 0

        exceeded = count >= effective_limit

        if not exceeded:
            await self.cache.backend.set(key, count + 1, window_seconds + 10)

        return not exceeded, {
            "limit": effective_limit,
            "used": count + 1 if not exceeded else count,
            "remaining": max(0, effective_limit - (count + 1 if not exceeded else count)),
            "adjusted": factor is not None,
        }
