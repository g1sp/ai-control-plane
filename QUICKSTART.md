# Quick Start (5 Minutes)

Get the Policy-Aware AI Gateway running locally in 5 minutes.

## Prerequisites

- Docker & Docker Compose
- (Optional) Claude API key for remote mode

## Step 1: Clone & Setup (1 min)

```bash
git clone <repo>
cd policy-ai-gateway

# Copy environment template
cp .env.example .env

# (Optional) Edit .env and add your CLAUDE_API_KEY
# For local-only mode, leave it blank
```

## Step 2: Start Services (2 min)

```bash
docker-compose up -d

# Wait for services to start (~30 seconds)
sleep 30

# Verify all services are running
docker-compose ps
# You should see: gateway, ollama (both healthy)
```

## Step 3: Test the Gateway (1 min)

```bash
# Health check
curl http://localhost:8000/health

# You should see: {"status": "healthy", ...}
```

## Step 4: Send Your First Query (1 min)

```bash
# Send a simple query to the local Ollama model
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is 2+2?",
    "user_id": "demo",
    "model": "auto"
  }'

# You should see:
# {
#   "request_id": "req_...",
#   "response": "4",
#   "model_used": "ollama",
#   "cost_usd": 0.0,
#   "policy_decision": "approved",
#   ...
# }
```

## Step 5: Check Audit Log (Bonus)

```bash
curl "http://localhost:8000/audit?user=demo&hours=1"

# You should see your request logged with all details
```

## Common Issues

### Ollama not available

```bash
# Check if Ollama is running
docker-compose logs ollama

# Restart Ollama
docker-compose restart ollama
```

### Port already in use

```bash
# Change port in docker-compose.yml:
# ports:
#   - "8001:8000"  # Changed from 8000

docker-compose up -d
curl http://localhost:8001/health
```

### Claude API errors

```bash
# Verify your CLAUDE_API_KEY is correct
cat .env

# Or use local-only mode (set GATEWAY_MODE=local)
# Both are already defaults
```

## What's Next?

- Read [README.md](./README.md) for full feature overview
- Check [ARCHITECTURE.md](./ARCHITECTURE.md) for system design
- Review [THREAT_MODEL.md](./THREAT_MODEL.md) for security
- See [API.md](./API.md) for all endpoints

## Stop Everything

```bash
docker-compose down
```

---

**Done!** You now have a working Policy-Aware AI Gateway. 🎉
