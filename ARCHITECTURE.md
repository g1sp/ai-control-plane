# Architecture: Policy-Aware AI Gateway

## System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENTS                                   │
│  (Python scripts, apps, services, Cursor plugins)                │
└───────────────────────────┬────────────────────────────────────┘
                            │ POST /query
                            │ { prompt, user_id, model, budget }
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              POLICY-AWARE GATEWAY (FastAPI)                     │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 1. INPUT VALIDATION (Pydantic)                          │   │
│  │    • Parse JSON                                         │   │
│  │    • Type validation                                    │   │
│  │    • Length validation                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│           ▼                                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 2. POLICY ENGINE                                        │   │
│  │    • Check user whitelist                               │   │
│  │    • Check injection (regex patterns)                   │   │
│  │    • Check model whitelist                              │   │
│  │    • Check rate limit (60 req/min per user)            │   │
│  │    • Check budget (<$0.10 per request)                 │   │
│  │    Result: APPROVED or REJECTED                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│           │                                                      │
│           ├─→ REJECTED? ──→ Log violation, return 403 error     │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 3. MODEL ROUTER                                         │   │
│  │    Decide: Ollama or Claude?                            │   │
│  │    • If local mode + Ollama available + prompt < 500c:  │   │
│  │      → Use Ollama (free, fast)                          │   │
│  │    • Else:                                               │   │
│  │      → Use Claude API (powerful)                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│           ▼                                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 4. EXECUTION                                            │   │
│  │    • Send to chosen model                               │   │
│  │    • 30-second timeout                                  │   │
│  │    • Handle errors gracefully                           │   │
│  │    Result: response text + token usage                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│           ▼                                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 5. COST CALCULATION                                     │   │
│  │    • Count input tokens (heuristic: 1 token = 4 chars)  │   │
│  │    • Count output tokens (from API response)            │   │
│  │    • Look up rate (Ollama=$0, Claude=varies)            │   │
│  │    • Calculate: (in_tokens * rate) + (out * rate)       │   │
│  │    Result: cost_usd                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│           ▼                                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 6. FINAL BUDGET CHECK                                   │   │
│  │    Verify: cost <= request.budget_usd                   │   │
│  │    If over: reject, log violation                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│           ▼                                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 7. AUDIT LOGGING                                        │   │
│  │    • Record request to SQLite                           │   │
│  │    • Log: user, prompt, response, model, cost, decision │   │
│  │    • Result: audit_requests table entry                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│           ▼                                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 8. RESPONSE                                             │   │
│  │    Return to client:                                    │   │
│  │      • response text                                    │   │
│  │      • model used                                       │   │
│  │      • tokens (in/out)                                  │   │
│  │      • cost (USD)                                       │   │
│  │      • policy_decision (approved)                       │   │
│  │      • request_id (for audit lookup)                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
     │
     ├─→ audit.db (SQLite)
     │   ├─ audit_requests (all requests)
     │   └─ audit_violations (rejections)
     │
     ├─→ Ollama (local model)
     │   └─ HTTP POST to http://ollama:11434/api/generate
     │
     └─→ Claude API (remote model)
         └─ HTTPS via Anthropic SDK


STORAGE & INTEGRATIONS
════════════════════════════════════════════════════════════════

audit.db (SQLite)
  ├─ audit_requests
  │   ├─ id, timestamp, user_id
  │   ├─ prompt, response
  │   ├─ model_used, tokens_in, tokens_out
  │   ├─ cost_usd, policy_decision
  │   └─ duration_ms, error_message
  │
  └─ audit_violations
      ├─ id, timestamp, user_id
      ├─ violation_reason
      └─ details

.env (Configuration)
  ├─ CLAUDE_API_KEY (API credentials)
  ├─ GATEWAY_MODE (local or remote)
  ├─ BUDGET_PER_REQUEST_USD ($0.10)
  ├─ RATE_LIMIT_REQ_PER_MINUTE (60)
  └─ (and more)

Ollama (HTTP)
  └─ GET /api/tags
  └─ POST /api/generate
     └─ Returns: response text, stream

Claude API (HTTPS)
  └─ messages.create() via Anthropic SDK
     └─ Returns: response, token usage
```

## Data Flow: Step-by-Step Example

**User sends query to gateway:**

```
POST /query
{
  "prompt": "What is the capital of France?",
  "user_id": "alice@company.com",
  "model": "auto",
  "budget_usd": 0.10
}
```

**Gateway processes:**

1. **Validation**: Check prompt length, user_id format ✓
2. **Policy**:
   - User "alice@company.com" in whitelist? ✓
   - Prompt contains injection patterns? ✗ (no)
   - Model "auto" is valid? ✓
   - User within rate limit (60/min)? ✓
   - Budget $0.10 ok? ✓
   - Decision: APPROVED
3. **Routing**:
   - Mode is "local" ✓
   - Ollama available? ✓
   - Prompt length 33 chars < 500? ✓
   - Route to: Ollama
4. **Execution**:
   - POST to http://ollama:11434/api/generate
   - Response: "The capital of France is Paris."
   - Tokens out: ~7
5. **Cost**:
   - Tokens in: 33/4 = 8 tokens
   - Tokens out: 7 tokens
   - Cost: (8 * $0/1k) + (7 * $0/1k) = $0.00
6. **Budget**: $0.00 <= $0.10 ✓
7. **Audit**: Log all details to SQLite
8. **Response**:

```json
{
  "request_id": "req_abc123xyz",
  "response": "The capital of France is Paris.",
  "model_used": "ollama",
  "tokens_in": 8,
  "tokens_out": 7,
  "cost_usd": 0.0,
  "policy_decision": "approved",
  "duration_ms": 145,
  "timestamp": "2024-03-17T14:23:15Z"
}
```

## Key Design Decisions

### Why Two Trust Boundaries?

**Boundary 1 (Before Execution)**: Policy engine enforces rules before sending to models
- Prevents wasteful requests
- Stops most attacks before they reach the model
- Fast rejection (no model cost)

**Boundary 2 (After Execution)**: Audit logging records everything
- Immutable record (for compliance)
- Detects anomalies (unusual cost spikes)
- Enables operator review

### Why Heuristic Token Counting (v1)?

- **Fast**: No API call needed
- **Simple**: 1 token ≈ 4 characters (industry standard)
- **Conservative**: Slight overestimate (safe for budgets)
- **v2**: Use actual tokenizer from API for accuracy

### Why SQLite (Not PostgreSQL)?

- **Local-first**: No external DB needed
- **Embedded**: Simpler deployment
- **Sufficient**: 100K+ requests/day easily handled
- **v2**: PostgreSQL option for scale

### Why Ollama First (Not Claude)?

- **Cost**: Free local inference
- **Speed**: No network latency
- **Privacy**: Prompts stay local
- **Offline**: Works without internet
- **Routing**: Save $$ on simple tasks

## Deployment Architecture

### Docker Compose (Local Development)

```
┌─────────────────────────────────┐
│   Docker Bridge Network         │
│                                 │
│  ┌─────────────────────────┐   │
│  │ Gateway (FastAPI)       │   │
│  │ Port: 8000              │   │
│  │ DB: /data/audit.db      │   │
│  └─────────────────────────┘   │
│           ↓                      │
│  ┌─────────────────────────┐   │
│  │ Ollama                  │   │
│  │ Port: 11434             │   │
│  │ Models: /models/        │   │
│  └─────────────────────────┘   │
│                                 │
└─────────────────────────────────┘
     ↑
External: Claude API (HTTPS)
```

## Scaling (Future)

### v2 (Multi-Instance)

```
Load Balancer
  ├─ Gateway #1 ──┐
  ├─ Gateway #2 ──┼─→ Shared PostgreSQL
  └─ Gateway #3 ──┘

  └─ Shared Redis (rate limiting, caching)
```

### v3 (Multi-Region)

```
Region 1                Region 2
┌──────────┐           ┌──────────┐
│ Gateway  │──┐   ┌───│ Gateway  │
└──────────┘  │   │   └──────────┘
     ↓        │   │        ↓
  Ollama      │   │     Ollama
              ↓   ↓
          Central Audit DB
          Central Policy Store
```

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Policy check | < 1ms | In-memory checks only |
| Ollama query | 100-500ms | Depends on model size |
| Claude query | 500-2000ms | Includes network latency |
| Cost calculation | < 1ms | Simple math |
| Audit logging | < 10ms | SQLite write |
| **Total (Ollama)** | **~150ms** | E2E with audit |
| **Total (Claude)** | **~600ms** | E2E with audit |

## Security Model

See [THREAT_MODEL.md](./THREAT_MODEL.md) for full security analysis.

**TL;DR**:
- Trust boundary 1: Policy engine (prevent bad requests)
- Trust boundary 2: Audit logging (record all decisions)
- Assume secure host OS (Linux hardening)
- Prompts logged (encrypted in v2)
