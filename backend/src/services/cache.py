"""Distributed caching layer for multi-instance deployment."""

import json
import pickle
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from abc import ABC, abstractmethod


class CacheBackend(ABC):
    """Abstract cache backend interface."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """Set value in cache."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass

    @abstractmethod
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter."""
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """Clear all cache."""
        pass


class MemoryCacheBackend(CacheBackend):
    """In-memory cache backend (single instance)."""

    def __init__(self):
        """Initialize memory cache."""
        self.store: Dict[str, tuple[Any, Optional[datetime]]] = {}

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key not in self.store:
            return None

        value, expiry = self.store[key]
        if expiry and datetime.utcnow() > expiry:
            del self.store[key]
            return None

        return value

    async def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """Set value in cache."""
        expiry = datetime.utcnow() + timedelta(seconds=ttl_seconds) if ttl_seconds else None
        self.store[key] = (value, expiry)
        return True

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if key in self.store:
            del self.store[key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        if key not in self.store:
            return False

        value, expiry = self.store[key]
        if expiry and datetime.utcnow() > expiry:
            del self.store[key]
            return False

        return True

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter."""
        if key not in self.store:
            self.store[key] = (amount, None)
            return amount

        value, expiry = self.store[key]
        if isinstance(value, int):
            new_value = value + amount
            self.store[key] = (new_value, expiry)
            return new_value

        return 0

    async def clear(self) -> bool:
        """Clear all cache."""
        self.store.clear()
        return True


class RedisCacheBackend(CacheBackend):
    """Redis-backed distributed cache (multi-instance)."""

    def __init__(self, redis_client):
        """Initialize Redis cache."""
        self.redis = redis_client

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = await self.redis.get(key)
            if value is None:
                return None
            return pickle.loads(value)
        except Exception:
            return None

    async def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """Set value in cache."""
        try:
            serialized = pickle.dumps(value)
            await self.redis.setex(key, ttl_seconds, serialized)
            return True
        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception:
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        try:
            result = await self.redis.exists(key)
            return result > 0
        except Exception:
            return False

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter."""
        try:
            result = await self.redis.incrby(key, amount)
            return result
        except Exception:
            return 0

    async def clear(self) -> bool:
        """Clear all cache."""
        try:
            await self.redis.flushdb()
            return True
        except Exception:
            return False


class CacheManager:
    """Unified cache manager."""

    def __init__(self, backend: CacheBackend):
        """Initialize cache manager."""
        self.backend = backend

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get cached session."""
        return await self.backend.get(f"session:{session_id}")

    async def set_session(self, session_id: str, data: Dict[str, Any], ttl_seconds: int = 3600) -> bool:
        """Cache session data."""
        return await self.backend.set(f"session:{session_id}", data, ttl_seconds)

    async def delete_session(self, session_id: str) -> bool:
        """Delete cached session."""
        return await self.backend.delete(f"session:{session_id}")

    async def get_rate_limit(self, user_id: str, window: str) -> int:
        """Get rate limit counter."""
        count = await self.backend.get(f"ratelimit:{user_id}:{window}")
        return count if count is not None else 0

    async def increment_rate_limit(self, user_id: str, window: str, ttl_seconds: int = 60) -> int:
        """Increment rate limit counter."""
        key = f"ratelimit:{user_id}:{window}"

        # Initialize if not exists
        if not await self.backend.exists(key):
            await self.backend.set(key, 0, ttl_seconds)

        return await self.backend.increment(key)

    async def check_rate_limit(self, user_id: str, limit: int, window_seconds: int = 60) -> bool:
        """Check if rate limit exceeded."""
        window = f"{int(datetime.utcnow().timestamp() / window_seconds)}"
        count = await self.increment_rate_limit(user_id, window, window_seconds)
        return count <= limit

    async def get_cost_tracker(self, user_id: str, period: str) -> float:
        """Get tracked cost for period."""
        cost = await self.backend.get(f"cost:{user_id}:{period}")
        return float(cost) if cost is not None else 0.0

    async def add_cost(self, user_id: str, cost_usd: float, ttl_seconds: int = 86400) -> float:
        """Add to cost tracker."""
        period = datetime.utcnow().strftime("%Y-%m-%d")
        key = f"cost:{user_id}:{period}"

        if not await self.backend.exists(key):
            await self.backend.set(key, 0.0, ttl_seconds)

        # Increment as float (stored as string, converted on retrieval)
        current = await self.get_cost_tracker(user_id, period)
        new_cost = current + cost_usd
        await self.backend.set(key, new_cost, ttl_seconds)
        return new_cost

    async def get_execution_cache(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get cached execution result."""
        return await self.backend.get(f"execution:{execution_id}")

    async def set_execution_cache(self, execution_id: str, data: Dict[str, Any], ttl_seconds: int = 3600) -> bool:
        """Cache execution result."""
        return await self.backend.set(f"execution:{execution_id}", data, ttl_seconds)

    async def invalidate_user_cache(self, user_id: str) -> None:
        """Invalidate all cache for user."""
        # In production, would need pattern-based deletion
        # For now, individual deletions managed elsewhere
        pass

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "backend": self.backend.__class__.__name__,
            "timestamp": datetime.utcnow().isoformat(),
        }


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager(backend: Optional[CacheBackend] = None) -> CacheManager:
    """Get or create global cache manager."""
    global _cache_manager
    if _cache_manager is None:
        if backend is None:
            backend = MemoryCacheBackend()  # Default to memory cache
        _cache_manager = CacheManager(backend)
    return _cache_manager
