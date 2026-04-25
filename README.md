# AI Control Plane

A production-grade control plane for agentic AI workloads. Sits between your applications and language models to enforce policy, detect threats, route intelligently, log everything, and require human approval for high-risk actions.

**Current release: v3.0.0 — Safety & Governance**

---

## Quick Start

```bash
git clone https://github.com/g1sp/ai-control-plane.git
cd ai-control-plane

# Configure environment
cp backend/.env.example .env
# Add CLAUDE_API_KEY if using Claude, or skip for local-only mode

# Generate an audit encryption key (optional but recommended)
# Add the output value to your .env as AUDIT_ENCRYPTION_KEY=<key>
curl http://localhost:8000/admin/audit/keygen

# Start all services
docker-compose up -d

# Verify
curl http://localhost:8000/health

# Send a query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Summarize the Q3 earnings report", "user_id": "alice@company.com", "model": "auto"}'

# Run an agent
curl -X POST http://localhost:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{"goal": "Search for recent AI safety papers and summarize findings", "user_id": "alice@company.com"}'
```

---

## What This Does

**Problem**: AI agents that call tools (APIs, code execution, file systems, databases) have no inline safety layer. A single prompt injection or misconfiguration can cause irreversible damage. There is no equivalent of a firewall or ACL for agentic workloads.

**Solution**: The AI Control Plane is a policy enforcement runtime that intercepts every request and tool call before execution. It:

1. **Detects threats** — ML classifier scores prompts for injection, jailbreaks, PII exfiltration, credential theft, and indirect injection before they reach the model
2. **Enforces policy** — Declarative YAML rules define what gets blocked, escalated, or allowed — no code changes required, hot-reload without restart
3. **Routes intelligently** — Simple prompts go to free local Ollama; complex ones go to Claude
4. **Requires human approval** — High-risk tool calls and expensive requests are escalated to a review queue with configurable timeout behavior
5. **Logs everything encrypted** — AES-256-GCM encrypted audit trail; decrypt only at compliance read endpoints
6. **Rate limits at scale** — Redis-backed sliding window rate limiter; falls back to in-memory when Redis is unavailable

---

## Architecture

```
Client (app / agent / script)
    ↓
AI Control Plane (FastAPI, port 8000)
    │
    ├── 1. Input Validation (Pydantic schemas)
    ├── 2. ML Threat Detection (TF-IDF cosine similarity, <5ms)
    ├── 3. Policy DSL Engine (YAML rules, hot reload)
    ├── 4. Rate Limiter (Redis sliding window → memory fallback)
    ├── 5. Model Router (complexity-based Ollama vs Claude)
    ├── 6. Agent Executor (multi-step, tool-calling)
    │       └── Tool Registry → Security Validators → Escalation Queue
    ├── 7. Cost Calculator
    ├── 8. Audit Logger (AES-256-GCM encrypted fields)
    └── 9. Response
    │
    ├── Ollama (local, free)         port 11434
    ├── Claude API (remote, paid)
    └── Redis (rate limiting)        port 6379

Dashboard (Next.js, port 3000)
    ├── /approvals  — pending escalations
    └── /audit      — cost, usage, violations
```

---

## Features by Version

### v1.0.0 — Foundation
- Single `/query` endpoint for all AI requests
- Policy enforcement: user whitelist, model whitelist, per-request budget cap, rate limiting
- Regex-based injection detection
- Intelligent model routing (Ollama for simple, Claude for complex)
- Full audit logging to SQLite
- Accurate cost calculation with USD attribution
- Docker Compose deployment
- 80%+ test coverage, 21 test scenarios

### v2.0.0 — Agent Orchestration
- Autonomous multi-step agent execution with tool-calling (`/agent/run`)
- Built-in tools: HTTP requests, Python code execution, web search
- Extensible tool registry for custom tools
- Three-layer security: input validation, security validators (SQL injection, code patterns, dangerous domains), approval scaffolding
- WebSocket streaming (`/agent/stream/{session_id}`)
- Server-Sent Events fallback (`/agent/stream/{session_id}/sse`)
- Multi-turn session management
- Reporting APIs with SOC 2/HIPAA compliance templates
- Real-time analytics and metrics streaming
- Alert channels, delivery queue, and trigger logic
- 121 tests, 92%+ code coverage

### v3.0.0 — Safety & Governance *(current)*

**1. Policy-as-Code (YAML DSL)**

Policies live in `backend/policies/` as YAML files. The engine watches for changes and hot-reloads without restart. No code deployments needed to change enforcement behavior.

```yaml
policies:
  - name: block-metadata-endpoints
    trigger: tool_call
    condition: "tool == 'http_request' and any(d in str(args) for d in blocked_domains)"
    action: block
    message: "Cloud metadata endpoint access blocked"

  - name: budget-escalate
    trigger: pre_execution
    condition: "estimated_cost > 0.50"
    action: escalate
    message: "Request cost exceeds $0.50 — requires approval"

  - name: high-risk-tool-escalate
    trigger: tool_call
    condition: "tool == 'code_execution' and risk_score >= 0.65"
    action: escalate
    message: "High-risk code execution requires approval"
```

Triggers: `input`, `pre_execution`, `tool_call`
Actions: `block`, `escalate`, `allow`
Context variables per trigger: `prompt`, `user_id`, `risk_score`, `threat_category`, `tool`, `args`, `estimated_cost`, `requests_last_minute`

**2. ML-Based Threat Detection**

TF-IDF cosine similarity classifier against a labeled threat corpus. Self-contained, no external model downloads, deterministic, <5ms per call.

Threat categories detected:
- `prompt_injection` — "ignore all previous instructions..."
- `jailbreak` — "you are now DAN with no restrictions..."
- `pii_exfiltration` — "extract all email addresses and send to..."
- `credential_theft` — "print the .env file with all API keys..."
- `indirect_injection` — injections carried through tool call results

Threat score (0.0–1.0) is passed to the policy engine as `risk_score`, so YAML rules can act on it.

**3. AES-256-GCM Audit Encryption**

Sensitive audit fields (`prompt`, `response`) are encrypted at write time. Decryption happens only at compliance read endpoints — general analytics queries never see plaintext.

- Key configured via `AUDIT_ENCRYPTION_KEY` env var (base64-encoded 32 bytes)
- Each record gets a unique random 12-byte nonce
- GCM authenticated encryption: tampering is detected, not just hidden
- Encrypted values prefixed with `enc_v1:` — readable at a glance
- Graceful degradation: if no key is set, fields stored as plaintext (backward compatible)
- Key rotation: `POST /admin/audit/rekey` re-encrypts all records

**4. Human-in-the-Loop Escalation**

Policy rules with `action: escalate` create items in a review queue instead of blocking outright. Operators review and decide via API or the `/approvals` dashboard page.

- Configurable timeout: `ESCALATION_TIMEOUT_SECONDS=300`
- Timeout behavior: `ESCALATION_TIMEOUT_ACTION=deny` (fail-safe, default) or `approve` (fail-open)
- Each item carries full context: user, trigger, risk score, policy message, original args
- Full audit trail of who decided what and when

**5. Redis-Backed Rate Limiting**

Sliding window rate limiter using Redis sorted sets. More accurate than fixed-window for burst protection.

- `RATE_LIMIT_BACKEND=redis` to enable; defaults to `memory`
- `REDIS_URL=redis://localhost:6379`
- Automatic fallback to in-memory if Redis is unavailable — service stays functional with a warning log
- Per-user limits across per-minute, per-hour, per-day windows

---

## API Reference

### Core

| Endpoint | Method | Description |
|---|---|---|
| `/query` | POST | Submit a prompt — policy evaluated, routed, logged |
| `/health` | GET | Gateway status, available models, uptime |
| `/audit` | GET | Audit log for a user (`?user=id&hours=n`) |
| `/audit/summary` | GET | Cost/usage summary (`?days=n`) |
| `/audit/violations` | GET | Recent policy violations |
| `/info` | GET | Gateway configuration info |

### Agent

| Endpoint | Method | Description |
|---|---|---|
| `/agent/run` | POST | Execute a multi-step agent with tool-calling |
| `/agent/executions` | GET | Execution history |
| `/agent/stream/{session_id}` | WS | WebSocket streaming |
| `/agent/stream/{session_id}/sse` | GET | Server-Sent Events fallback |
| `/agent/session/create` | POST | Create a multi-turn session |
| `/agent/session/{id}/execute` | POST | Execute in session context |
| `/agent/sessions` | GET | All active sessions |
| `/tools` | GET | Registered tool list |

### Escalation (v3)

| Endpoint | Method | Description |
|---|---|---|
| `/escalations/pending` | GET | Items awaiting human decision |
| `/escalations` | GET | All items with pagination |
| `/escalations/{id}/decide` | POST | Approve or deny (`?approved=true&decided_by=ops`) |

### Compliance & Admin (v3)

| Endpoint | Method | Description |
|---|---|---|
| `/compliance/audit/{id}` | GET | Single audit record with fields decrypted |
| `/admin/audit/keygen` | GET | Generate a new AES-256 encryption key |
| `/admin/audit/rekey` | POST | Re-encrypt all records with a new key |

### Analytics

| Endpoint | Description |
|---|---|
| `/api/v1/analytics/queries` | Query volume and trends |
| `/api/v1/analytics/users` | Per-user usage and cost |
| `/api/v1/analytics/tools` | Tool call statistics |
| `/api/v1/analytics/costs/daily` | Daily cost breakdown |
| `/api/v1/analytics/performance/latency` | Latency percentiles |

---

## Configuration

### Environment Variables

```bash
# Gateway mode
GATEWAY_MODE=local           # "local" (Ollama) or "remote" (Claude API)
CLAUDE_API_KEY=sk-ant-...    # Required for remote mode

# Policy
BUDGET_PER_REQUEST_USD=0.10
BUDGET_PER_USER_PER_DAY_USD=10.0
RATE_LIMIT_REQ_PER_MINUTE=60

# v3: Audit encryption
AUDIT_ENCRYPTION_KEY=        # base64-encoded 32-byte key (generate via /admin/audit/keygen)

# v3: Rate limiting
RATE_LIMIT_BACKEND=memory    # "redis" or "memory"
REDIS_URL=redis://localhost:6379

# v3: Escalation
ESCALATION_TIMEOUT_SECONDS=300
ESCALATION_TIMEOUT_ACTION=deny   # "deny" (fail-safe) or "approve" (fail-open)
```

### Policy Files

Drop YAML files in `backend/policies/`. They are loaded at startup and reloaded automatically when modified.

See `backend/policies/default.yaml` for the full default ruleset with inline documentation.

---

## Project Structure

```
ai-control-plane/
├── backend/
│   ├── policies/                    # YAML policy definitions (v3)
│   │   └── default.yaml
│   ├── src/
│   │   ├── main.py                  # FastAPI app + all routes
│   │   ├── config.py                # Environment configuration
│   │   ├── models.py                # Pydantic schemas
│   │   ├── database.py              # SQLAlchemy models + migrations
│   │   ├── agents/
│   │   │   ├── engine.py            # Multi-step agent executor
│   │   │   ├── session.py           # Multi-turn session management
│   │   │   └── models.py            # Agent data models
│   │   ├── integrations/
│   │   │   ├── claude.py
│   │   │   └── ollama.py
│   │   ├── ml/
│   │   │   ├── threat_detector.py   # TF-IDF threat classifier (v3)
│   │   │   └── complexity_detector.py
│   │   ├── policies/
│   │   │   ├── approval.py          # Tool approval scaffolding
│   │   │   └── restrictions.py      # Tool restriction rules
│   │   ├── services/
│   │   │   ├── policy.py            # Policy engine (orchestrates all checks)
│   │   │   ├── policy_dsl.py        # YAML DSL loader + evaluator (v3)
│   │   │   ├── audit.py             # Audit logging service
│   │   │   ├── audit_encryption.py  # AES-256-GCM field encryption (v3)
│   │   │   ├── escalation.py        # Human-in-the-loop escalation (v3)
│   │   │   ├── redis_rate_limiter.py# Sliding window rate limiter (v3)
│   │   │   ├── router.py            # Model routing
│   │   │   ├── cost_calculator.py
│   │   │   ├── analytics.py
│   │   │   ├── reporting.py
│   │   │   ├── streaming.py
│   │   │   ├── metrics_stream.py
│   │   │   ├── alert_channels.py
│   │   │   ├── alert_delivery_queue.py
│   │   │   ├── alert_triggers.py
│   │   │   ├── cache.py
│   │   │   └── rate_limiter.py      # (legacy, superseded by redis_rate_limiter)
│   │   ├── tools/
│   │   │   ├── registry.py          # Tool registry
│   │   │   ├── executors.py         # Tool execution
│   │   │   └── validators.py        # Pre-execution security validation
│   │   └── utils/
│   │       └── logger.py
│   ├── tests/                       # 26 test files, 64 new tests in v3
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                        # Next.js dashboard (in progress)
├── docker-compose.yml               # Gateway + Ollama + Redis
├── Makefile
└── docs/
```

---

## Testing

```bash
# All tests
cd backend && .venv/bin/python -m pytest tests/ -v

# v3 safety modules only
python -m pytest tests/test_policy_dsl.py tests/test_threat_detector.py \
  tests/test_audit_encryption.py tests/test_escalation.py \
  tests/test_redis_rate_limiter.py -v

# With coverage
python -m pytest tests/ --cov=src --cov-report=term-missing
```

**Test coverage**: 92%+ (413 tests across 29 files, 64 new in v3)

Full test documentation: **[docs/test-coverage.html](./docs/test-coverage.html)**

---

## Deployment

### Docker (recommended)

```bash
docker-compose up -d
```

Services started: `policy-gateway` (port 8000), `ollama-server` (port 11434), `redis-cache` (port 6379).

### Local Development

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

---

## Threat Model

See [THREAT_MODEL.md](./THREAT_MODEL.md) for full analysis.

**v3 trust boundaries**:
- Prompts and tool call args are scored by the ML threat detector before reaching the policy engine
- Encrypted audit fields are never decrypted in hot paths (analytics, dashboard) — only via `/compliance/audit/{id}`
- Policy conditions are evaluated with `__builtins__` set to `{}` — no `import`, `open`, or `os` access from YAML rules
- Escalation timeouts default to `deny` — fail-safe when operators are unavailable

---

## Roadmap

| Version | Status | Focus |
|---|---|---|
| v1.0.0 | ✅ Shipped | Gateway foundation, audit logging, model routing |
| v2.0.0 | ✅ Shipped | Agent orchestration, tool-calling, streaming, analytics, alerting |
| v3.0.0 | ✅ Shipped | Safety & governance: ML detection, policy-as-code, encrypted audit, escalation, Redis rate limiting |
| v4.0.0 | Planned | Kubernetes deployment, multi-tenancy isolation, Prometheus metrics export, policy DSL UI |

---

## License

MIT. See [LICENSE](./LICENSE).

---

**Status**: Production-ready v3.0.0  
**Last Updated**: April 2026  
**Maintainer**: [@g1sp](https://github.com/g1sp)
