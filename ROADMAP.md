# Roadmap: Policy-Aware AI Gateway

## v1.0 (Current - March 2026)

**Status**: ✅ COMPLETE

### Features
- [x] Single `/query` endpoint
- [x] Policy enforcement (budget, rate limit, whitelist)
- [x] Model routing (Ollama vs Claude)
- [x] Audit logging (SQLite)
- [x] Cost calculation
- [x] Injection detection (regex-based)
- [x] Health check + info endpoints
- [x] Docker Compose deployment
- [x] 80%+ test coverage

### Known Limitations
- Single instance (no horizontal scaling)
- Prompts logged in plaintext
- Heuristic token counting
- No dashboard (API-only)
- Local network only (not internet-exposed)

---

## v1.1 (Q2 2026)

**Estimated**: 2-3 weeks after v1.0

### Features
- [ ] Dashboard (Next.js)
  - Real-time cost trends
  - Top users chart
  - Policy violations timeline
  - Request count metrics

- [ ] API improvements
  - Pagination for audit queries
  - Filtering (by date, user, model)
  - Export to CSV/JSON

- [ ] Configuration
  - YAML policy files (v2, more flexible)
  - Environment variables validation
  - Hot reload for policy changes

### Breaking Changes
None - backward compatible with v1.0

---

## v2.0 (Q3 2026)

**Estimated**: 1 month after v1.1

### Major Features

#### 1. Streaming Responses
- Server-sent events (SSE) for streaming
- Partial token counting during stream
- Cost estimated vs actual (post-execution)
- Dashboard real-time streaming display

#### 2. ML-Based Injection Detection
- Train on known attack patterns
- Replace/supplement regex heuristics
- Higher accuracy, fewer false positives
- Feedback loop from violations

#### 3. Secrets Management
- Integrate with AWS Secrets Manager (or Vault)
- Remove API keys from .env
- Automated key rotation
- Audit trail for secret access

#### 4. Multi-Tenancy (Basic)
- Multiple orgs/teams per instance
- Separate audit logs per tenant
- Tenant-level budget caps
- API key authentication

#### 5. Dashboard Enhancements
- Cost attribution by feature/endpoint
- Per-user audit log view
- Real-time alerts
- Export reports

#### 6. Encryption at Rest
- Encrypt prompts in audit.db (AES-256)
- Encrypt sensitive config
- Key management (KMS)

### Breaking Changes
- None (additive features)

---

## v3.0 (Q4 2026+)

**Estimated**: 2+ months planning

### Major Features

#### 1. Advanced Policy Language
- DSL for complex policies
- Time-based rules (peak pricing)
- Model-specific policies
- Approval workflows (human-in-the-loop)

#### 2. Tool Execution Integration
- Integrate with OpenClaw agent lab
- Tool approval gates
- Dangerous tool restrictions
- Tool usage logging

#### 3. Distributed Deployment
- Load balancing (multiple gateway instances)
- PostgreSQL replication
- Redis for distributed rate limiting
- Horizontal scaling

#### 4. Advanced Monitoring
- Distributed tracing (correlation IDs)
- Metrics export (Prometheus)
- Alerting (PagerDuty, Slack)
- Custom dashboards (Grafana)

#### 5. Compliance Features
- Audit log immutability (blockchain-inspired)
- Compliance reports (SOC 2, HIPAA templates)
- Data retention policies
- GDPR data deletion

#### 6. AI-Powered Features
- Anomaly detection (behavior deviation)
- Cost optimization suggestions
- Policy recommendations
- Predictive usage forecasting

### Breaking Changes
- Possible API changes (v2 → v3)
- Database schema changes (migration required)

---

## Technical Debt & Maintenance

### v1 → v1.1
- [ ] Add API integration tests (FastAPI test client)
- [ ] Increase test coverage to 90%+
- [ ] Add performance benchmarks
- [ ] Document deployment on ASUS NUC

### v1.1 → v2.0
- [ ] Refactor database layer (prepare for PostgreSQL)
- [ ] Add database migrations (Alembic)
- [ ] Improve error handling (custom exceptions)
- [ ] Add structured logging (JSON)

### v2 → v3
- [ ] Separate services (gateway, audit, policy as microservices)
- [ ] API versioning (v1/, v2/, v3/)
- [ ] Async job processing (Celery/Bull)
- [ ] Event streaming (Kafka?)

---

## Integration Roadmap

### Phase 2: OpenClaw Agent Lab (Weeks 5-8)
- Integrates with v1 Policy Gateway
- Reuses: policy engine, cost calculator, audit logger
- Adds: tool approval workflow, security tests
- Depends on: Policy Gateway v1.0 ✓

### Phase 3: DNS Mesh & Behavior Engine (Weeks 9-12)
- Independent of gateway (but uses same audit patterns)
- Reuses: shared audit service, policy engine
- Adds: edge sensors, central aggregator
- Depends on: Shared components ✓

### Phase 4: Evaluation Harness (Weeks 13+)
- Tests gateway + agent lab
- Reuses: gateway API, audit queries
- Adds: scenario library, regression tracking
- Depends on: Gateway v1.0, Agent Lab v1.0

### Phase 5: Operator Console (Weeks 13+)
- Reads all audit logs (from gateway, agent, sensors)
- Reuses: dashboard components, audit queries
- Adds: unified operator workflows
- Depends on: v1.1 (with dashboard)

---

## Success Metrics

### v1.0
- [ ] Zero critical bugs
- [ ] 80%+ test coverage
- [ ] <100ms policy evaluation latency
- [ ] Ollama + Claude routing working
- [ ] All 5 security tests passing

### v1.1
- [ ] Dashboard operational (cost, users, violations visible)
- [ ] <500KB memory footprint per request
- [ ] <50ms dashboard page load
- [ ] CSV export working

### v2.0
- [ ] Streaming responses tested (E2E)
- [ ] ML model trained on 100+ injections
- [ ] Multi-tenant isolation verified
- [ ] No prompts in plaintext logs

### v3.0
- [ ] Distributed deployment on 3+ nodes
- [ ] 1000+ req/sec throughput
- [ ] <5 second sync across regions
- [ ] Compliance audit passing

---

## Dependencies & Blockers

| Version | Blocker | Impact |
|---------|---------|--------|
| v1.0 | None | SHIPPED ✓ |
| v1.1 | Dashboard styling/UX | Non-blocking (API works without) |
| v2.0 | ML model training data | Can delay, use regex fallback |
| v2.0 | Secrets manager setup | Non-blocking (env var fallback) |
| v3.0 | PostgreSQL setup | Requires DB admin |
| v3.0 | Kubernetes (optional) | Non-blocking (Docker Compose still works) |

---

## Release Schedule

| Version | Planned | Status | Link |
|---------|---------|--------|------|
| v1.0 | March 17, 2026 | ✅ SHIPPED | [Release](https://github.com/.../releases/tag/v1.0.0) |
| v1.1 | May 1, 2026 | 🔮 Planned | - |
| v2.0 | July 1, 2026 | 🔮 Planned | - |
| v3.0 | Oct 1, 2026 | 🔮 Planned | - |

---

## Contributing

Want to help? See [CONTRIBUTING.md](./docs/CONTRIBUTING.md) for:
- How to submit issues
- How to propose features
- How to contribute code
- Code review process

---

**Last Updated**: March 18, 2026
**Maintained By**: Your Team
