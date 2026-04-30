# Policy-Aware AI Gateway

A local, production-grade control plane for AI requests. Every request gets logged, routed intelligently, validated against policy, and costed accurately.

## ⚠️ Security Notice (v1.1+)

**API Key Authentication Required**: Starting with v1.1, all requests require an `Authorization: Bearer` header with a valid API key. See [Quick Start](#quick-start-5-minutes) for how to generate keys.

**Output Handling**: The gateway returns raw LLM outputs. Your application is responsible for secure output handling (sanitization, validation, sandboxing). See [CLIENT_SECURITY.md](./CLIENT_SECURITY.md) for best practices.

## Quick Start (5 Minutes)

```bash
# Clone and enter directory
git clone <this-repo>
cd policy-ai-gateway

# Copy environment template
cp .env.example .env
# Edit .env: Add your CLAUDE_API_KEY (or skip for local-only mode)

# Start the gateway
docker-compose up -d

# Verify it's running
curl http://localhost:8000/health

# Generate an API key (first time only)
API_KEY=$(curl -X POST http://localhost:8000/auth/keys \
  -H "Authorization: Bearer pk-demo:sk-demo-secret-123" \
  -H "Content-Type: application/json" | jq -r '.key_secret')

# Send a test query (requires Authorization header)
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer pk-demo:$API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is 2+2?",
    "model": "auto"
  }'

# View audit log
curl "http://localhost:8000/audit?user=demo&hours=1"

# Get compliance status
curl -H "Authorization: Bearer pk-demo:sk-demo-secret-123" \
  http://localhost:8000/api/v1/security/owasp-compliance | jq .

# View dashboard
# Frontend: http://localhost:5173 (Vite dev server)
# - Home: Real-time metrics
# - OWASP LLM Status: Compliance scorecard
# - Configuration: Policy editing + rollback timeline
```

## What This Does

**Problem**: You can't see, control, or audit AI requests. Tokens leak, costs spike, and there's no audit trail.

**Solution**: The Policy-Aware AI Gateway sits between your applications and language models. It:

1. **Logs everything** – Timestamp, user, prompt, response, cost, policy decision
2. **Routes intelligently** – Uses cheap local Ollama for simple tasks, expensive Claude for complex ones
3. **Enforces policy** – Whitelist models, cap budgets, rate limit per user
4. **Validates input** – Detects prompt injection attempts before they reach the model
5. **Calculates costs** – Accurate token counting and price breakdown (USD)

## Features

### Phase 1-4: Core Gateway (v1.0)
- [x] Single `/query` endpoint for all AI requests
- [x] Policy enforcement (budget limits, rate limiting, model whitelist)
- [x] Model routing (Ollama vs Claude)
- [x] Complete audit logging (SQLite)
- [x] Cost calculation and attribution
- [x] Injection detection (regex-based heuristics)
- [x] Health check endpoint
- [x] Docker Compose (local deployment)
- [x] API key authentication (SHA256 hashing)

### Phase 5: Configuration Management (v1.1)
- [x] Runtime policy configuration (no restart required)
- [x] Configuration persistence (SQLite history)
- [x] Configuration audit trail (who changed what, when)
- [x] Dashboard UI for policy editing

### Phase 5.5: Configuration Rollback (v1.2)
- [x] One-click config rollback to any point in history
- [x] Visual timeline showing state transitions
- [x] Change diff display (old → new values)
- [x] Full version history with restore buttons

### Phase 6: OWASP LLM Compliance (v1.3)
- [x] OWASP LLM Top 10 compliance scorecard
- [x] 7/10 controls implemented (70% compliance)
- [x] Expandable compliance details per control
- [x] Dedicated security status dashboard
- [x] Truthful synthetic data reflecting actual capabilities

## Architecture

```
Clients (apps, scripts)
    ↓ POST /query
    │
Gateway (FastAPI)
    ├─ 1. Validate input
    ├─ 2. Check policy (budget, rate limit, injection)
    ├─ 3. Route to model (Ollama or Claude)
    ├─ 4. Execute with timeout
    ├─ 5. Calculate cost
    └─ 6. Log to audit.db
    │
    ├─ Ollama (free, fast, local)
    └─ Claude API (powerful, costs $)

Dashboard (Next.js)
    └─ Queries audit.db for real-time metrics
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for full system design.

## API

### POST /query

**Request**:
```json
{
  "prompt": "What is the capital of France?",
  "model": "auto",
  "user_id": "alice@company.com",
  "budget_usd": 0.10,
  "timeout_seconds": 30
}
```

**Response (200 OK)**:
```json
{
  "request_id": "req_abc123",
  "response": "The capital of France is Paris.",
  "model_used": "ollama",
  "tokens_in": 12,
  "tokens_out": 8,
  "cost_usd": 0.0,
  "policy_decision": "approved",
  "duration_ms": 245,
  "timestamp": "2024-03-17T14:23:15Z"
}
```

**Response (403 Policy Violation)**:
```json
{
  "error": "policy_violation",
  "reason": "budget_exceeded",
  "request_id": "req_abc123"
}
```

### GET /health

Check gateway status and available models.

### GET /audit?user=<id>&hours=<n>

Query audit log for a user (recent requests).

### GET /audit/summary?days=<n>

Get cost breakdown and usage statistics.

### GET /audit/violations?hours=<n>

Get recent policy violations.

See [API.md](./API.md) for full endpoint reference.

## Security & Threat Model

See [THREAT_MODEL.md](./THREAT_MODEL.md) for:
- Trust boundaries
- Attack scenarios and mitigations
- Policy enforcement limits
- Audit logging security

**TL;DR**: v1 assumes local deployment with secure host OS. Prompts are logged (encrypted in v2).

## Configuration

Edit `.env`:

```bash
# Mode: "local" (Ollama) or "remote" (Claude API)
GATEWAY_MODE=local

# Claude API key (optional, required for remote mode)
CLAUDE_API_KEY=sk-ant-...

# Policy
BUDGET_PER_REQUEST_USD=0.10          # Per request cap
BUDGET_PER_USER_PER_DAY_USD=10.0     # Daily per-user cap
RATE_LIMIT_REQ_PER_MINUTE=60         # Rate limit
```

See [backend/.env.example](./backend/.env.example) for all options.

## Deployment

### Local Development

```bash
# Install dependencies
make install

# Run dev server (with auto-reload)
make dev
```

### Docker (Recommended)

```bash
# Build images
make docker-build

# Start services
make docker-up

# View logs
make docker-logs

# Stop
make docker-down
```

## Testing

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Specific test file
cd backend && python -m pytest tests/test_policy.py -v
```

**Current coverage**: 80%+ (policy, cost, injection detection)

## Dashboard

The web dashboard (`localhost:3000`) provides real-time monitoring and control:

- **Home**: Real-time metrics (queries, cost, latency, error rate)
- **OWASP LLM Status**: Compliance scorecard showing 7/10 controls implemented
- **Configuration**: Runtime policy editing with rollback timeline
- **Security Events**: Real-time violation tracking

## Roadmap

### v1.3 (Current)
- [x] Core gateway with policy enforcement
- [x] API key authentication
- [x] Runtime configuration management
- [x] Config rollback + timeline
- [x] OWASP LLM compliance dashboard

### v2.0 (Next)
- [ ] Streaming responses
- [ ] ML-based injection detection
- [ ] Config staging & approval workflows
- [ ] Compliance trending (historical scores)
- [ ] Risk scoring per vulnerability

### v3.0 (Future)
- [ ] Multi-tenancy support
- [ ] Human-in-the-loop approval workflows
- [ ] Tool execution sandbox
- [ ] Kubernetes deployment
- [ ] Supply chain vulnerability scanning

See [ROADMAP.md](./ROADMAP.md) for detailed planning.

## Development

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Claude API key (optional, for remote mode)

### Project Structure

```
backend/
  ├── src/
  │   ├── main.py              # FastAPI app + routes
  │   ├── config.py            # Configuration
  │   ├── models.py            # Pydantic schemas
  │   ├── database.py          # SQLite setup
  │   ├── services/            # Business logic
  │   │   ├── policy.py        # Policy engine
  │   │   ├── router.py        # Model routing
  │   │   ├── audit.py         # Audit logging
  │   │   └── cost_calculator.py
  │   └── integrations/        # External APIs
  │       ├── ollama.py
  │       └── claude.py
  ├── tests/
  ├── requirements.txt
  └── Dockerfile
```

### Adding Features

1. Update `models.py` (data schemas)
2. Implement service in `services/` or `integrations/`
3. Wire into `main.py` routes
4. Add tests in `tests/`
5. Update docs

## Contributing

1. Fork the repo
2. Create feature branch (`git checkout -b feat/cool-feature`)
3. Make changes + tests
4. Run tests (`make test`)
5. Commit with clear message
6. Push and create PR

See [CONTRIBUTING.md](./docs/CONTRIBUTING.md) for more.

## License

MIT License. See [LICENSE](./LICENSE) for details.

## Questions?

- See [FAQ.md](./docs/FAQ.md)
- Open an [issue](https://github.com/your-org/policy-ai-gateway/issues)
- Read [ARCHITECTURE.md](./ARCHITECTURE.md) for design decisions

---

**Status**: v1.3 — Production-ready with governance & compliance
**Current Version**: v1.3 (OWASP LLM Compliance Dashboard)
**Last Updated**: April 30, 2026
