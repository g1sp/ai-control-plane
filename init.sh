#!/bin/bash

# Initialize Policy-Aware AI Gateway
# Usage: bash init.sh

set -e

echo "════════════════════════════════════════════════════════════"
echo "  Policy-Aware AI Gateway — Initialization"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."
echo ""

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker."
    exit 1
fi
echo "✅ Docker found"

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose."
    exit 1
fi
echo "✅ Docker Compose found"

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11+."
    exit 1
fi
echo "✅ Python 3 found"

echo ""
echo "📝 Setting up environment..."
echo ""

# Create .env if not exists
if [ ! -f .env ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo "✅ .env created (edit it to add your CLAUDE_API_KEY if needed)"
else
    echo "✅ .env already exists"
fi

echo ""
echo "🐳 Building Docker images..."
echo ""

docker-compose build

echo ""
echo "✅ Setup complete!"
echo ""
echo "════════════════════════════════════════════════════════════"
echo "  Next Steps"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "1. Start the gateway:"
echo "   docker-compose up -d"
echo ""
echo "2. Verify it's running:"
echo "   curl http://localhost:8000/health"
echo ""
echo "3. Send a test query:"
echo "   curl -X POST http://localhost:8000/query \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"prompt\":\"Hello\",\"user_id\":\"demo\",\"model\":\"auto\"}'"
echo ""
echo "4. Run the interactive demo:"
echo "   bash scripts/demo.sh"
echo ""
echo "5. Read the documentation:"
echo "   • README.md - Overview"
echo "   • QUICKSTART.md - 5-minute setup"
echo "   • ARCHITECTURE.md - System design"
echo ""
echo "════════════════════════════════════════════════════════════"
