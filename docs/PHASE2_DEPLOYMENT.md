# Phase 2 Deployment Guide

**Version:** 2.0.0  
**Last Updated:** April 16, 2026  
**Status:** Production-Ready

---

## Overview

This guide covers deploying the Policy-Aware AI Gateway with Phase 2 Agent Orchestration system.

---

## Prerequisites

### System Requirements
- Python 3.9+
- PostgreSQL 12+ (optional, SQLite default)
- 2GB RAM minimum
- Docker & Docker Compose (for containerized deployment)

### API Keys & Credentials
- Claude API key (from Anthropic)
- Ollama server (optional, for local models)

---

## Local Development Setup

### 1. Clone & Navigate

```bash
git clone https://github.com/anthropics/ai-control-plane.git
cd ai-control-plane/backend
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Create `.env` file:

```env
# API Keys
CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxx
OLLAMA_ENDPOINT=http://localhost:11434

# Gateway Config
GATEWAY_MODE=hybrid
MODELS_WHITELIST=claude-sonnet-4-6,claude-haiku-4-5-20251001-v1:0
BUDGET_PER_REQUEST_USD=1.0
BUDGET_PER_USER_PER_DAY_USD=50.0
RATE_LIMIT_REQ_PER_MINUTE=10

# Database
DATABASE_URL=sqlite:///./gateway.db  # Or: postgresql://user:password@localhost/gateway

# Logging
LOG_LEVEL=INFO
```

### 5. Initialize Database

```bash
python -m src.database
# Creates tables: audit_requests, user_policies, agent_executions, tool_approvals, etc.
```

### 6. Run Development Server

```bash
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Server will be available at `http://localhost:8000`

### 7. Verify Installation

```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy", ...}

curl http://localhost:8000/tools
# Expected: List of available tools
```

---

## Docker Deployment

### 1. Build Image

```bash
docker build -t ai-gateway:2.0.0 .
```

### 2. Run Container

```bash
docker run -d \
  -p 8000:8000 \
  -e CLAUDE_API_KEY=sk-ant-xxxx \
  -e DATABASE_URL=postgresql://user:password@db:5432/gateway \
  -v /data/gateway:/app/data \
  --name gateway \
  ai-gateway:2.0.0
```

### 3. Using Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: gateway
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  gateway:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:secure_password@postgres:5432/gateway
      CLAUDE_API_KEY: ${CLAUDE_API_KEY}
      GATEWAY_MODE: hybrid
    depends_on:
      - postgres
    volumes:
      - ./logs:/app/logs

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  postgres_data:
  ollama_data:
```

Deploy:

```bash
docker-compose up -d
docker-compose logs -f gateway
```

---

## Production Deployment

### Prerequisites
- Load balancer (nginx, HAProxy)
- SSL/TLS certificates
- Database backups configured
- Monitoring setup (Prometheus, Grafana)

### 1. Configure Secrets Manager

Use environment variable files or secrets manager:

```bash
# Via secrets manager
docker secret create CLAUDE_API_KEY key.txt

# Via env file (secure)
docker run --env-file secrets.env ...
```

### 2. Configure Database

For PostgreSQL (recommended):

```bash
# Create database
createdb -h localhost -U postgres gateway

# Run migrations (if using Alembic)
alembic upgrade head
```

### 3. Setup SSL/TLS

Configure nginx as reverse proxy:

```nginx
upstream gateway {
    server localhost:8000;
}

server {
    listen 443 ssl;
    server_name api.example.com;

    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;

    location / {
        proxy_pass http://gateway;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4. Configure Logging

Mount logs directory:

```bash
docker run -v /var/log/gateway:/app/logs ...
```

Configure log rotation in systemd or docker:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

### 5. Setup Monitoring

Expose Prometheus metrics:

```bash
# Check /metrics endpoint
curl http://localhost:8000/metrics
```

Configure Prometheus scrape config:

```yaml
scrape_configs:
  - job_name: 'gateway'
    static_configs:
      - targets: ['localhost:8000']
```

---

## Database Configuration

### SQLite (Default - Development)

```env
DATABASE_URL=sqlite:///./gateway.db
```

### PostgreSQL (Recommended - Production)

```env
DATABASE_URL=postgresql://user:password@host:port/database
SQLALCHEMY_POOL_SIZE=20
SQLALCHEMY_POOL_RECYCLE=3600
SQLALCHEMY_POOL_PRE_PING=true
```

Connection pooling settings:
- `POOL_SIZE`: Number of connections (default: 5)
- `POOL_RECYCLE`: Recycle connections after N seconds (3600 = 1 hour)
- `POOL_PRE_PING`: Test connections before use

---

## Performance Tuning

### Application Settings

```env
# Concurrency
WORKER_COUNT=4
WORKER_THREADS=10

# Timeouts
REQUEST_TIMEOUT_SECONDS=60
CLAUDE_API_TIMEOUT_SECONDS=30

# Limits
MAX_REQUEST_SIZE_BYTES=10000000  # 10MB
MAX_RESPONSE_SIZE_BYTES=50000000  # 50MB
```

### Database Settings

```env
# Connection Pool
SQLALCHEMY_POOL_SIZE=20
SQLALCHEMY_MAX_OVERFLOW=10

# Query Optimization
SQLALCHEMY_ECHO=false
```

### Tool Execution

Edit `src/policies/restrictions.yaml`:

```yaml
tools:
  python_eval:
    timeout_seconds: 30
    memory_limit_mb: 256
  http_get:
    rate_limit_per_minute: 20
    timeout_seconds: 10
  search:
    max_results: 50
```

---

## Verification Checklist

### Pre-Production

- [ ] All dependencies installed
- [ ] Database initialized
- [ ] Claude API key valid
- [ ] SSL certificates configured
- [ ] Environment variables set
- [ ] Logs configured
- [ ] Monitoring setup

### Post-Deployment

- [ ] Health check passes: `curl /health`
- [ ] Endpoints responsive: `curl /tools`
- [ ] Database connected
- [ ] Logs flowing
- [ ] Metrics accessible
- [ ] Error handling working

### Run Tests

```bash
# Unit tests
pytest tests/test_tool_registry.py -v

# Integration tests
pytest tests/test_agent_integration.py -v

# Security tests
pytest tests/test_security_hardening.py -v

# Load tests
pytest tests/test_load.py -v

# Full suite with coverage
pytest tests/ --cov=src --cov-report=html
```

---

## Troubleshooting

### Gateway Won't Start

```bash
# Check logs
docker logs gateway

# Common issues:
# - CLAUDE_API_KEY not set
# - Database connection failed
# - Port already in use

# Fix database connection
export DATABASE_URL=sqlite:///./gateway.db
python -c "from src.database import init_db; init_db()"
```

### Slow Response Times

```bash
# Check database performance
# Monitor query times in logs

# Increase pool size
export SQLALCHEMY_POOL_SIZE=30

# Check tool timeouts in restrictions.yaml
```

### High Memory Usage

```bash
# Check for memory leaks in logs
docker stats gateway

# Restart container if needed
docker restart gateway

# Review agent execution patterns
curl http://localhost:8000/audit/summary
```

### Claude API Errors

```bash
# Verify API key is valid
python -c "from src.integrations.claude import ClaudeClient; c = ClaudeClient(); print('OK')"

# Check rate limits
curl -H "Authorization: Bearer $CLAUDE_API_KEY" https://api.anthropic.com/v1/account

# Check quota in dashboard
```

---

## Backup & Recovery

### Database Backup

```bash
# PostgreSQL
pg_dump gateway > gateway_backup.sql

# SQLite
cp gateway.db gateway_backup.db
```

### Restore Backup

```bash
# PostgreSQL
psql gateway < gateway_backup.sql

# SQLite
cp gateway_backup.db gateway.db
```

### Audit Log Backup

```bash
# Export audit logs
curl http://localhost:8000/audit/summary?days=30 > audit_export.json
```

---

## Scaling

### Horizontal Scaling

Deploy multiple gateway instances behind load balancer:

```nginx
upstream gateways {
    server gateway1:8000;
    server gateway2:8000;
    server gateway3:8000;
}

server {
    location / {
        proxy_pass http://gateways;
    }
}
```

### Vertical Scaling

Increase resources per instance:

```bash
docker run -m 4g -c 2 ...  # 4GB memory, 2 CPUs
```

### Database Scaling

For high load, use read replicas:

```env
PRIMARY_DATABASE_URL=postgresql://user:pass@primary/gateway
READ_REPLICA_URL=postgresql://user:pass@replica/gateway
```

---

## Monitoring Commands

```bash
# Health status
curl http://localhost:8000/health

# Audit summary
curl http://localhost:8000/audit/summary?days=1

# Violations
curl http://localhost:8000/audit/violations?hours=24

# Gateway info
curl http://localhost:8000/info

# Tool definitions
curl http://localhost:8000/tools | jq
```

---

## Support & Updates

- Documentation: https://github.com/anthropics/ai-control-plane/docs
- Issues: https://github.com/anthropics/ai-control-plane/issues
- Updates: Run `pip install -r requirements.txt --upgrade`
