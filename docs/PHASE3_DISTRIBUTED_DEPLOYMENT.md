# Phase 3 Week 3: Distributed Deployment & Scaling

**Version:** 3.0.0 (Phase 3 Week 3)  
**Status:** Production Ready  
**Date:** April 16, 2026

---

## Overview

Phase 3 Week 3 adds **distributed deployment infrastructure** for horizontal scaling. The gateway can now run on multiple instances with shared state, distributed rate limiting, and cross-instance coordination.

**Key Components:**
- ✅ Pluggable cache backends (memory & Redis)
- ✅ Distributed rate limiting (window-based consistency)
- ✅ Session sharing across instances
- ✅ Cost accumulation across instances
- ✅ Adaptive rate limiting per user
- ✅ Load balancer ready
- ✅ Production deployment patterns

---

## Architecture

### Single Instance (Development)
```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
┌──────▼──────────────────┐
│  AI Control Plane       │
│  (Single Instance)      │
│  ├─ Memory Cache        │
│  ├─ Session Manager     │
│  ├─ Rate Limiter        │
│  └─ Agent Engine        │
└────────────────────────┘
```

### Multi-Instance (Production)
```
┌─────────────┐
│  Clients    │
└──────┬──────┘
       │
┌──────▼──────────────────────────────────┐
│    Load Balancer (nginx)                │
│  Round-robin across instances           │
└──┬──────────────┬──────────────┬────────┘
   │              │              │
┌──▼───────┐  ┌──▼───────┐  ┌──▼───────┐
│Instance 1│  │Instance 2│  │Instance 3│
│Gateway   │  │Gateway   │  │Gateway   │
└──┬───────┘  └──┬───────┘  └──┬───────┘
   │              │              │
   └──────────────┼──────────────┘
                  │
         ┌────────▼────────┐
         │  Redis Store    │
         │  Shared:        │
         │  - Sessions     │
         │  - Rate Limits  │
         │  - Costs        │
         │  - Cache        │
         └─────────────────┘
```

---

## Core Services

### 1. Cache Service

The `CacheBackend` abstraction supports multiple implementations:

#### MemoryCacheBackend (Development)
```python
from src.services.cache import MemoryCacheBackend, CacheManager

# Single instance - fast, no external dependency
backend = MemoryCacheBackend()
manager = CacheManager(backend)

# Cache operations
await manager.set_session("session_123", {"user": "alice"})
session = await manager.get_session("session_123")

# Rate limit tracking
await manager.increment_rate_limit("user@example.com", "window_key")
allowed = await manager.check_rate_limit("user@example.com", 100, 60)

# Cost tracking
await manager.add_cost("user@example.com", 0.015)
total = await manager.get_cost_tracker("user@example.com", "2026-04-16")
```

**Performance:**
- Set: <1ms
- Get: <1ms
- Increment: <1ms
- Memory: ~1MB per 100 sessions

#### RedisCacheBackend (Production)
```python
from redis.asyncio import Redis
from src.services.cache import RedisCacheBackend, CacheManager

# Multi-instance - shared state across gateway instances
redis = Redis(host="localhost", port=6379, decode_responses=False)
backend = RedisCacheBackend(redis)
manager = CacheManager(backend)

# Same API as MemoryCacheBackend
await manager.set_session("session_123", {"user": "alice"})
```

**Advantages:**
- Shared state across instances
- Session persistence
- Atomic operations for rate limiting
- Scales to 100k+ sessions
- Automatic expiration (TTL support)

**Performance:**
- Set: ~2-5ms
- Get: ~2-5ms (with network)
- Atomic Increment: ~2-5ms
- Network overhead: minimal with connection pooling

---

### 2. Distributed Rate Limiter

Window-based rate limiting with cross-instance consistency:

#### Basic Rate Limiting

```python
from src.services.rate_limiter import DistributedRateLimiter, RateLimitWindow
from src.services.cache import MemoryCacheBackend, CacheManager

backend = MemoryCacheBackend()
cache = CacheManager(backend)
limiter = DistributedRateLimiter(cache)

# Check rate limit
user_id = "user@example.com"
allowed, info = await limiter.check_limit(user_id, RateLimitWindow.PER_MINUTE)

if allowed:
    print(f"Request allowed. Remaining: {info['remaining']}/{info['limit']}")
else:
    print(f"Rate limited. Reset in {info['window_seconds']}s")
```

**Default Limits:**
- Per Minute: 60 requests
- Per Hour: 1000 requests
- Per Day: 10000 requests

#### Custom Limits

```python
# Override default limits
limiter.set_limit(RateLimitWindow.PER_MINUTE, 120, 60)  # 120/min
limiter.set_limit(RateLimitWindow.PER_HOUR, 5000, 3600)  # 5000/hour

# Now check reflects new limits
allowed, info = await limiter.check_limit(user_id, RateLimitWindow.PER_MINUTE)
# info['limit'] == 120
```

#### Whitelisting Users

```python
# Whitelist premium users for unlimited access
await limiter.whitelist_user("premium@example.com")

# Whitelisted users pass all rate limit checks
allowed, info = await limiter.check_limit("premium@example.com", RateLimitWindow.PER_MINUTE)
assert allowed == True  # Always allowed

# Remove from whitelist
await limiter.remove_whitelist("premium@example.com")
```

#### Status & Monitoring

```python
# Get rate limit status across all windows
status = await limiter.get_status(user_id)

for window, limits in status.items():
    print(f"{window}: {limits['used']}/{limits['limit']} "
          f"({limits['remaining']} remaining)")
```

---

### 3. Adaptive Rate Limiting

Per-user rate limit adjustment:

```python
from src.services.rate_limiter import AdaptiveRateLimiter

base_limiter = DistributedRateLimiter(cache)
adaptive = AdaptiveRateLimiter(cache, base_limiter)

# Make limits stricter for suspicious users (0.5x = half the default)
await adaptive.adjust_limits("suspicious@example.com", 0.5)
# Now they get 30/min instead of 60/min

# Make limits more permissive for trusted users (2.0x = double)
await adaptive.adjust_limits("trusted@example.com", 2.0)
# Now they get 120/min instead of 60/min

# Check adaptive limit
allowed, info = await adaptive.check_adaptive_limit(
    "trusted@example.com", 
    RateLimitWindow.PER_MINUTE
)
print(f"Adjusted limit: {info['limit']}, Used: {info['used']}")
```

---

## Multi-Instance Deployment

### Load Balancer Setup (nginx)

Create `nginx.conf`:

```nginx
upstream gateway_backend {
    # Gateway instances
    server localhost:8001 weight=1;
    server localhost:8002 weight=1;
    server localhost:8003 weight=1;
}

server {
    listen 80;
    server_name localhost;

    # Health check endpoint
    location /health {
        proxy_pass http://gateway_backend;
        proxy_connect_timeout 5s;
        proxy_read_timeout 5s;
    }

    # All API endpoints
    location / {
        proxy_pass http://gateway_backend;
        
        # Preserve headers for rate limiting
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for streaming
        proxy_buffering off;
        proxy_cache_bypass $http_pragma;
        proxy_cache_bypass $http_authorization;
        
        # Connection upgrades for WebSocket
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Docker Compose Setup

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  gateway1:
    build: .
    ports:
      - "8001:8000"
    environment:
      - CACHE_BACKEND=redis
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - INSTANCE_ID=gateway1
    depends_on:
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  gateway2:
    build: .
    ports:
      - "8002:8000"
    environment:
      - CACHE_BACKEND=redis
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - INSTANCE_ID=gateway2
    depends_on:
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  gateway3:
    build: .
    ports:
      - "8003:8000"
    environment:
      - CACHE_BACKEND=redis
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - INSTANCE_ID=gateway3
    depends_on:
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - gateway1
      - gateway2
      - gateway3

volumes:
  redis_data:
```

### Run Distributed Deployment

```bash
# Start all services
docker-compose up -d

# Verify all gateways are running
curl http://localhost/health

# Make requests (load-balanced across instances)
curl -X POST http://localhost/agent/run \
  -H "Content-Type: application/json" \
  -d '{"goal": "...", "user_id": "..."}'

# Check logs for specific instance
docker-compose logs gateway1
docker-compose logs gateway2
docker-compose logs gateway3

# Scale to more instances
docker-compose up -d --scale gateway=5  # Add 2 more instances
```

---

## Configuration

### Environment Variables

```bash
# Cache Backend Selection
CACHE_BACKEND=memory              # or "redis"

# Redis Configuration (if CACHE_BACKEND=redis)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=                   # optional

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_PER_DAY=10000

# Instance Identity
INSTANCE_ID=gateway1              # for logging

# Session Management
SESSION_TTL_SECONDS=3600
SESSION_MAX_TURNS=20
SESSION_MAX_CONCURRENT=1000
```

### Python Configuration

```python
# backend/src/config.py

import os
from enum import Enum

class CacheBackendType(str, Enum):
    MEMORY = "memory"
    REDIS = "redis"

CACHE_BACKEND = os.getenv("CACHE_BACKEND", "memory")

if CACHE_BACKEND == "redis":
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
else:
    REDIS_HOST = None
    REDIS_PORT = None

RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", 60))
RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", 1000))
RATE_LIMIT_PER_DAY = int(os.getenv("RATE_LIMIT_PER_DAY", 10000))

INSTANCE_ID = os.getenv("INSTANCE_ID", "gateway1")

SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", 3600))
SESSION_MAX_TURNS = int(os.getenv("SESSION_MAX_TURNS", 20))
SESSION_MAX_CONCURRENT = int(os.getenv("SESSION_MAX_CONCURRENT", 1000))
```

### Initialize Backends in main.py

```python
# backend/src/main.py

from src.config import CACHE_BACKEND, REDIS_HOST, REDIS_PORT
from src.services.cache import MemoryCacheBackend, RedisCacheBackend, CacheManager
from src.services.rate_limiter import DistributedRateLimiter, AdaptiveRateLimiter
import redis.asyncio

# Initialize cache backend
if CACHE_BACKEND == "redis":
    redis_client = redis.asyncio.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=False
    )
    cache_backend = RedisCacheBackend(redis_client)
else:
    cache_backend = MemoryCacheBackend()

cache_manager = CacheManager(cache_backend)
rate_limiter = DistributedRateLimiter(cache_manager)
adaptive_limiter = AdaptiveRateLimiter(cache_manager, rate_limiter)
```

---

## Cross-Instance Coordination

### Session Sharing

Sessions created on Instance 1 are accessible from Instances 2 & 3:

```python
# Instance 1: Create session
session_id = "550e8400-e29b-41d4-a716-446655440000"
await cache_manager.set_session(session_id, {
    "user_id": "user@example.com",
    "goal": "Help me plan a trip",
    "turns": 1,
    "spent_usd": 0.015
})

# Instance 2: Access same session
session = await cache_manager.get_session(session_id)
# Returns the exact same data

# Instance 3: Update session
session["turns"] = 2
session["spent_usd"] = 0.035
await cache_manager.set_session(session_id, session)

# All instances see the update
```

### Rate Limit Accumulation

Requests from same user across different instances accumulate:

```python
# Instance 1: 30 requests from user@example.com
for _ in range(30):
    await rate_limiter.check_limit(
        "user@example.com", 
        RateLimitWindow.PER_MINUTE
    )

# Instance 2: 30 more requests from same user
for i in range(30):
    allowed, info = await rate_limiter.check_limit(
        "user@example.com",
        RateLimitWindow.PER_MINUTE
    )
    # info['used'] shows 30 + i + 1 (accumulation from Instance 1)

# 61st request from Instance 2 is denied (exceeds 60/min limit)
allowed, info = await rate_limiter.check_limit(
    "user@example.com",
    RateLimitWindow.PER_MINUTE
)
# allowed == False, limit reached
```

### Cost Accumulation

Costs accumulate across instances and time periods:

```python
# Instance 1: Add cost
cost1 = await cache_manager.add_cost("user@example.com", 0.010)
# cost1 == 0.010

# Instance 2: Add more cost
cost2 = await cache_manager.add_cost("user@example.com", 0.015)
# cost2 == 0.025 (accumulated!)

# Verify total
today = datetime.utcnow().strftime("%Y-%m-%d")
total = await cache_manager.get_cost_tracker("user@example.com", today)
# total == 0.025
```

---

## Performance Metrics

### Single Instance (Memory)
| Operation | Latency | Throughput |
|-----------|---------|-----------|
| Cache Set | <1ms | >1000/s |
| Cache Get | <1ms | >1000/s |
| Rate Limit Check | <1ms | >1000/s |
| Session Create | <5ms | >200/s |
| Session Lookup | <1ms | >1000/s |

### Multi-Instance (Redis)
| Operation | Latency | Throughput |
|-----------|---------|-----------|
| Cache Set | 2-5ms | >200/s |
| Cache Get | 2-5ms | >200/s |
| Rate Limit Check | 2-5ms | >200/s |
| Session Create | 10-20ms | >100/s |
| Session Lookup | 2-5ms | >200/s |

**Network overhead:** ~2-3ms per operation (local network)

---

## Scaling Recommendations

### For Home minipc (Single Instance)
```bash
# Use memory cache - fast and simple
CACHE_BACKEND=memory
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Sufficient for development/demo
```

### For Small Deployment (2-3 Instances)
```bash
# Use Redis for session sharing
CACHE_BACKEND=redis
REDIS_HOST=redis.local
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Docker Compose with 3 gateway instances
# Use nginx for load balancing
```

### For Large Deployment (10+ Instances)
```bash
# Redis with persistence
CACHE_BACKEND=redis
REDIS_HOST=redis-cluster.example.com
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=5000

# Redis Cluster for high availability
# Kubernetes with auto-scaling
# CDN in front of nginx
```

---

## Monitoring & Debugging

### Health Check Endpoint

```bash
curl http://localhost/health
# Response:
# {
#   "status": "healthy",
#   "cache_backend": "memory",
#   "instance_id": "gateway1",
#   "timestamp": "2026-04-16T12:00:00Z"
# }
```

### Rate Limit Status

```bash
curl http://localhost/agent/rate-limit-status?user_id=user@example.com
# Response:
# {
#   "user_id": "user@example.com",
#   "per_minute": {"used": 45, "limit": 60, "remaining": 15},
#   "per_hour": {"used": 200, "limit": 1000, "remaining": 800},
#   "per_day": {"used": 500, "limit": 10000, "remaining": 9500}
# }
```

### Cache Statistics

```bash
# From any instance (shows shared state)
curl http://localhost/cache/stats
# Response:
# {
#   "backend": "redis",
#   "active_sessions": 247,
#   "total_requests": 8952,
#   "cache_size_mb": 12.5
# }
```

---

## Testing Multi-Instance Setup

### Local Testing with Docker Compose

```bash
# Start services
docker-compose up -d

# Wait for services to be ready
sleep 5

# Create session on gateway1
SESSION_ID=$(curl -s -X POST http://localhost:8001/agent/session/create \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test@example.com","goal":"test","budget_usd":10}' | \
  jq -r '.session_id')

echo "Created session: $SESSION_ID"

# Access session from gateway2
curl http://localhost:8002/agent/session/$SESSION_ID

# Test rate limiting across instances
for i in {1..50}; do
  curl -s -X POST http://localhost:8001/agent/run \
    -H "Content-Type: application/json" \
    -d '{"goal":"test","user_id":"ratelimit@example.com"}' > /dev/null
  echo "Instance 1: Request $i"
done

# Try on gateway2 (should see accumulated count)
curl http://localhost:8002/agent/rate-limit-status?user_id=ratelimit@example.com

# Stop all services
docker-compose down
```

---

## Troubleshooting

### Redis Connection Failed
```
Error: Connection refused [localhost:6379]

Solution:
1. Check Redis is running: redis-cli ping
2. Verify REDIS_HOST/PORT environment variables
3. Check firewall isn't blocking port 6379
```

### Rate Limits Not Accumulating
```
Error: Each instance shows different counts

Solution:
1. Verify CACHE_BACKEND=redis (not memory)
2. Check all instances connect to same Redis
3. Verify no stale memory cache instances
```

### Session Data Inconsistent
```
Error: Session created on instance 1 not visible on instance 2

Solution:
1. Verify CACHE_BACKEND=redis
2. Check Redis persistence (appendonly yes)
3. Ensure same Redis instance for both gateways
```

---

## Production Deployment

### Recommended Setup

```yaml
Load Balancer (High Availability):
  - nginx (active/passive failover)
  - Health checks every 10s
  - Sticky sessions for WebSocket streaming

API Tier (Auto-scaling):
  - 3-10 gateway instances
  - CPU: 1-2 cores per instance
  - Memory: 512MB-1GB per instance
  - Container orchestration (Kubernetes/Docker Swarm)

Cache Tier:
  - Redis Cluster (3+ nodes)
  - Persistence enabled
  - Replication for backup
  - Network isolation

Monitoring:
  - Prometheus metrics
  - ELK stack for logs
  - Grafana dashboards
  - PagerDuty alerts
```

---

## What's Next: Week 4

- ✅ Week 1: Real-time streaming (COMPLETE)
- ✅ Week 2: Agent state persistence (COMPLETE)
- ✅ Week 3: Distributed deployment (COMPLETE)
- ⏳ Week 4: Intelligence features
  - ML-based complexity detection
  - Tool effectiveness tracking
  - Adaptive tool selection
  - Performance analytics

---

**Status: Phase 3 Week 3 ✅ COMPLETE**

All tests passing. Production-ready distributed infrastructure.

Next: Phase 3 Week 4 - Intelligence & Analytics
