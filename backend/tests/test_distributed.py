"""Tests for distributed deployment features."""

import pytest
from datetime import datetime, timedelta
from src.services.cache import (
    MemoryCacheBackend, CacheManager, get_cache_manager
)
from src.services.rate_limiter import (
    DistributedRateLimiter, AdaptiveRateLimiter, RateLimitWindow
)


class TestMemoryCacheBackend:
    """Test in-memory cache backend."""

    @pytest.mark.asyncio
    async def test_set_and_get(self):
        """Test setting and getting cache."""
        cache = MemoryCacheBackend()

        await cache.set("test_key", "test_value", ttl_seconds=3600)
        value = await cache.get("test_key")

        assert value == "test_value"

    @pytest.mark.asyncio
    async def test_delete(self):
        """Test cache deletion."""
        cache = MemoryCacheBackend()

        await cache.set("test_key", "test_value")
        assert await cache.exists("test_key")

        assert await cache.delete("test_key")
        assert not await cache.exists("test_key")

    @pytest.mark.asyncio
    async def test_expiration(self):
        """Test cache expiration."""
        cache = MemoryCacheBackend()

        await cache.set("test_key", "test_value", ttl_seconds=1)
        assert await cache.exists("test_key")

        # Manually expire
        cache.store["test_key"] = (
            "test_value",
            datetime.utcnow() - timedelta(seconds=1)
        )
        assert not await cache.exists("test_key")

    @pytest.mark.asyncio
    async def test_increment(self):
        """Test counter increment."""
        cache = MemoryCacheBackend()

        result1 = await cache.increment("counter")
        assert result1 == 1

        result2 = await cache.increment("counter", 5)
        assert result2 == 6

    @pytest.mark.asyncio
    async def test_clear(self):
        """Test clearing cache."""
        cache = MemoryCacheBackend()

        await cache.set("key1", "value1")
        await cache.set("key2", "value2")

        await cache.clear()
        assert not await cache.exists("key1")
        assert not await cache.exists("key2")


class TestCacheManager:
    """Test cache manager."""

    @pytest.mark.asyncio
    async def test_session_cache(self):
        """Test session caching."""
        backend = MemoryCacheBackend()
        manager = CacheManager(backend)

        session_data = {"user_id": "test@example.com", "turns": 2}
        await manager.set_session("session123", session_data)

        retrieved = await manager.get_session("session123")
        assert retrieved == session_data

    @pytest.mark.asyncio
    async def test_rate_limit_tracking(self):
        """Test rate limit tracking."""
        backend = MemoryCacheBackend()
        manager = CacheManager(backend)

        # First 5 requests
        for i in range(5):
            count = await manager.increment_rate_limit("user@example.com", "test_window")
            assert count == i + 1

        # Check limit (positional: user_id, limit, window_seconds)
        allowed = await manager.check_rate_limit("user@example.com", 10, 60)
        assert allowed

    @pytest.mark.asyncio
    async def test_cost_tracking(self):
        """Test cost tracking."""
        backend = MemoryCacheBackend()
        manager = CacheManager(backend)

        cost1 = await manager.add_cost("user@example.com", 0.015)
        assert cost1 == 0.015

        cost2 = await manager.add_cost("user@example.com", 0.020)
        assert cost2 == 0.035

    @pytest.mark.asyncio
    async def test_execution_cache(self):
        """Test execution result caching."""
        backend = MemoryCacheBackend()
        manager = CacheManager(backend)

        exec_data = {"result": "success", "cost": 0.015}
        await manager.set_execution_cache("exec123", exec_data)

        retrieved = await manager.get_execution_cache("exec123")
        assert retrieved == exec_data


class TestDistributedRateLimiter:
    """Test distributed rate limiter."""

    @pytest.mark.asyncio
    async def test_rate_limit_per_minute(self):
        """Test per-minute rate limiting."""
        backend = MemoryCacheBackend()
        cache_manager = CacheManager(backend)
        limiter = DistributedRateLimiter(cache_manager)

        # First request
        allowed, info = await limiter.check_limit("user@example.com", RateLimitWindow.PER_MINUTE)
        assert allowed
        assert info["used"] == 1

        # Multiple requests
        for i in range(2, 61):
            allowed, info = await limiter.check_limit("user@example.com", RateLimitWindow.PER_MINUTE)
            assert allowed
            assert info["used"] == i

        # 61st request should be denied
        allowed, info = await limiter.check_limit("user@example.com", RateLimitWindow.PER_MINUTE)
        assert not allowed

    @pytest.mark.asyncio
    async def test_rate_limit_per_hour(self):
        """Test per-hour rate limiting."""
        backend = MemoryCacheBackend()
        cache_manager = CacheManager(backend)
        limiter = DistributedRateLimiter(cache_manager)

        # Should allow up to 1000
        allowed, info = await limiter.check_limit("user@example.com", RateLimitWindow.PER_HOUR)
        assert allowed
        assert info["limit"] == 1000

    @pytest.mark.asyncio
    async def test_custom_limits(self):
        """Test setting custom limits."""
        backend = MemoryCacheBackend()
        cache_manager = CacheManager(backend)
        limiter = DistributedRateLimiter(cache_manager)

        # Set custom limit: 5 per minute
        limiter.set_limit(RateLimitWindow.PER_MINUTE, 5, 60)

        # First 5 should pass
        for i in range(5):
            allowed, _ = await limiter.check_limit("user@example.com", RateLimitWindow.PER_MINUTE)
            assert allowed

        # 6th should fail
        allowed, _ = await limiter.check_limit("user@example.com", RateLimitWindow.PER_MINUTE)
        assert not allowed

    @pytest.mark.asyncio
    async def test_whitelist(self):
        """Test user whitelist."""
        backend = MemoryCacheBackend()
        cache_manager = CacheManager(backend)
        limiter = DistributedRateLimiter(cache_manager)

        # User not whitelisted
        assert not await limiter.is_whitelisted("user@example.com")

        # Whitelist user
        await limiter.whitelist_user("user@example.com")
        assert await limiter.is_whitelisted("user@example.com")

        # Remove from whitelist
        await limiter.remove_whitelist("user@example.com")
        assert not await limiter.is_whitelisted("user@example.com")

    @pytest.mark.asyncio
    async def test_get_status(self):
        """Test rate limit status."""
        backend = MemoryCacheBackend()
        cache_manager = CacheManager(backend)
        limiter = DistributedRateLimiter(cache_manager)

        # Make some requests
        for _ in range(5):
            await limiter.check_limit("user@example.com", RateLimitWindow.PER_MINUTE)

        status = await limiter.get_status("user@example.com")

        assert RateLimitWindow.PER_MINUTE in status
        # get_status calls check_limit which increments, so we get 6 (5 + 1 from get_status)
        assert status[RateLimitWindow.PER_MINUTE]["used"] == 6


class TestAdaptiveRateLimiter:
    """Test adaptive rate limiting."""

    @pytest.mark.asyncio
    async def test_adjust_limits(self):
        """Test adjusting limits for user."""
        backend = MemoryCacheBackend()
        cache_manager = CacheManager(backend)
        base_limiter = DistributedRateLimiter(cache_manager)
        adaptive = AdaptiveRateLimiter(cache_manager, base_limiter)

        # Default limit is 60 per minute
        default_limit = base_limiter.limits[RateLimitWindow.PER_MINUTE][0]
        assert default_limit == 60

        # Adjust factor to 2x (allow 120 per minute)
        await adaptive.adjust_limits("user@example.com", 2.0)

        effective = await adaptive.get_effective_limit("user@example.com", RateLimitWindow.PER_MINUTE)
        assert effective == 120

    @pytest.mark.asyncio
    async def test_adaptive_check(self):
        """Test adaptive limit checking."""
        backend = MemoryCacheBackend()
        cache_manager = CacheManager(backend)
        base_limiter = DistributedRateLimiter(cache_manager)
        adaptive = AdaptiveRateLimiter(cache_manager, base_limiter)

        # Set factor to 0.5x (stricter limits)
        await adaptive.adjust_limits("user@example.com", 0.5)

        # Should allow fewer requests
        for i in range(30):
            allowed, info = await adaptive.check_adaptive_limit("user@example.com", RateLimitWindow.PER_MINUTE)
            assert allowed
            assert info["adjusted"]

        # 31st should fail (limit is 30, which is 60 * 0.5)
        allowed, _ = await adaptive.check_adaptive_limit("user@example.com", RateLimitWindow.PER_MINUTE)
        assert not allowed

    @pytest.mark.asyncio
    async def test_whitelist_bypass(self):
        """Test that whitelisted users bypass limits."""
        backend = MemoryCacheBackend()
        cache_manager = CacheManager(backend)
        base_limiter = DistributedRateLimiter(cache_manager)
        adaptive = AdaptiveRateLimiter(cache_manager, base_limiter)

        # Whitelist user
        await base_limiter.whitelist_user("user@example.com")

        # Can make unlimited requests
        for _ in range(1000):
            allowed, info = await adaptive.check_adaptive_limit("user@example.com", RateLimitWindow.PER_MINUTE)
            assert allowed
            assert not info.get("limited", True)


class TestDistributedScenarios:
    """Test distributed deployment scenarios."""

    @pytest.mark.asyncio
    async def test_multi_instance_rate_limit(self):
        """Test rate limiting across instances."""
        # Simulate 2 instances with shared cache
        backend = MemoryCacheBackend()

        cache1 = CacheManager(backend)
        cache2 = CacheManager(backend)

        limiter1 = DistributedRateLimiter(cache1)
        limiter2 = DistributedRateLimiter(cache2)

        # Instance 1: 30 requests
        for _ in range(30):
            await limiter1.check_limit("user@example.com", RateLimitWindow.PER_MINUTE)

        # Instance 2: 30 requests (should see 60 total)
        for i in range(30):
            allowed, info = await limiter2.check_limit("user@example.com", RateLimitWindow.PER_MINUTE)
            assert allowed
            assert info["used"] == 30 + i + 1

        # 61st total request should fail
        allowed, _ = await limiter2.check_limit("user@example.com", RateLimitWindow.PER_MINUTE)
        assert not allowed

    @pytest.mark.asyncio
    async def test_session_sharing_across_instances(self):
        """Test session cache sharing across instances."""
        backend = MemoryCacheBackend()

        manager1 = CacheManager(backend)
        manager2 = CacheManager(backend)

        # Instance 1 caches session
        session_data = {"user_id": "test@example.com", "turns": 2}
        await manager1.set_session("session123", session_data)

        # Instance 2 retrieves same session
        retrieved = await manager2.get_session("session123")
        assert retrieved == session_data

    @pytest.mark.asyncio
    async def test_cost_tracking_distributed(self):
        """Test cost tracking across instances."""
        backend = MemoryCacheBackend()

        manager1 = CacheManager(backend)
        manager2 = CacheManager(backend)

        # Instance 1 adds cost
        cost1 = await manager1.add_cost("user@example.com", 0.010)

        # Instance 2 adds cost (should accumulate)
        cost2 = await manager2.add_cost("user@example.com", 0.015)

        assert cost2 == 0.025

        # Verify accumulation
        total = await manager2.get_cost_tracker("user@example.com", datetime.utcnow().strftime("%Y-%m-%d"))
        assert total == 0.025


class TestGlobalCacheManager:
    """Test global cache manager singleton."""

    @pytest.mark.asyncio
    async def test_get_cache_manager(self):
        """Test getting global cache manager."""
        manager1 = get_cache_manager()
        manager2 = get_cache_manager()
        assert manager1 is manager2


class TestCachePerformance:
    """Performance tests for caching."""

    @pytest.mark.asyncio
    async def test_cache_throughput(self):
        """Test cache throughput."""
        import time

        backend = MemoryCacheBackend()
        manager = CacheManager(backend)

        start = time.time()
        for i in range(1000):
            await manager.set_session(f"session_{i}", {"data": f"value_{i}"})
        elapsed = (time.time() - start) * 1000

        # Should handle 1000 sets in <100ms
        assert elapsed < 100

    @pytest.mark.asyncio
    async def test_rate_limit_throughput(self):
        """Test rate limiter throughput."""
        import time

        backend = MemoryCacheBackend()
        cache_manager = CacheManager(backend)
        limiter = DistributedRateLimiter(cache_manager)

        start = time.time()
        for _ in range(1000):
            await limiter.check_limit(f"user@example.com", RateLimitWindow.PER_MINUTE)
        elapsed = (time.time() - start) * 1000

        # Should handle 1000 checks in <500ms
        assert elapsed < 500
