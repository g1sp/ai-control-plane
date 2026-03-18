# Setup Guide: Policy-Aware AI Gateway

## Prerequisites

- Python 3.11+ (check: `python3 --version`)
- Docker & Docker Compose (check: `docker --version`, `docker-compose --version`)
- Git (check: `git --version`)
- Claude API key (optional, for remote mode)

## Quick Setup

### Option 1: Docker (Recommended - 1 command)

```bash
docker-compose up -d
```

Then verify:
```bash
curl http://localhost:8000/health
```

### Option 2: Local Development

```bash
# Install Python dependencies
cd backend
pip install -r requirements.txt

# Initialize database
python -c "from src.database import init_db; init_db()"

# Run development server
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Then open another terminal:
```bash
curl http://localhost:8000/health
```

## First Request

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hello, what is 2+2?",
    "user_id": "demo",
    "model": "auto"
  }'
```

## Running Tests

```bash
cd backend
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=src --cov-report=html
```

## Next Steps

1. Read [README.md](./README.md) - Overview
2. Run [QUICKSTART.md](./QUICKSTART.md) - 5-minute demo
3. Study [ARCHITECTURE.md](./ARCHITECTURE.md) - System design
4. Review [THREAT_MODEL.md](./THREAT_MODEL.md) - Security
5. Check [ROADMAP.md](./ROADMAP.md) - Future plans

## Troubleshooting

### Port already in use

```bash
# Change port in docker-compose.yml or dev server:
python -m uvicorn src.main:app --reload --port 8001
```

### Ollama not responding

```bash
# Restart Ollama container
docker-compose restart ollama

# Or check logs
docker-compose logs ollama
```

### Claude API errors

```bash
# Check .env has CLAUDE_API_KEY
cat .env | grep CLAUDE

# Or use local-only mode (no key needed)
# Already the default: GATEWAY_MODE=local
```

---

**Ready?** Run `docker-compose up -d` and test with the curl command above!
