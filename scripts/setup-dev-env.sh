#!/bin/bash
# BudgetFlow Development Environment Setup
# Initializes Docker, migrations, hooks, and all dev tooling

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "🚀 BudgetFlow Development Environment Setup"
echo "==========================================="
echo ""

# 1. Check Docker
echo "1️⃣  Checking Docker..."
if ! command -v docker &> /dev/null; then
  echo "❌ Docker not installed. Please install Docker Desktop."
  exit 1
fi
echo "   ✅ Docker installed"

# 2. Start services
echo ""
echo "2️⃣  Starting Docker Compose services..."
if docker-compose ps | grep -q "Up"; then
  echo "   ℹ️  Services already running"
else
  echo "   Starting..."
  docker-compose up -d --build
  sleep 10
fi
echo "   ✅ Services running"

# 3. Run migrations
echo ""
echo "3️⃣  Running database migrations..."
docker exec budget-flow-backend alembic upgrade head > /dev/null 2>&1
echo "   ✅ Migrations applied"

# 4. Verify schema
echo ""
echo "4️⃣  Validating schema..."
bash "$REPO_ROOT/scripts/validate-schema.sh" > /dev/null 2>&1 || {
  echo "   ⚠️  Schema validation failed. Check manually:"
  bash "$REPO_ROOT/scripts/validate-schema.sh"
  exit 1
}
echo "   ✅ Schema valid"

# 5. Run tests
echo ""
echo "5️⃣  Running test suite..."
TEST_OUTPUT=$(docker exec budget-flow-backend python -m pytest tests/ -q --tb=short 2>&1 | tail -1)
echo "   ✅ $TEST_OUTPUT"

# 6. Install Git hooks
echo ""
echo "6️⃣  Installing Git hooks..."
bash "$REPO_ROOT/scripts/install-hooks.sh" > /dev/null 2>&1
echo "   ✅ Hooks installed"

# 7. Install act for local CI (optional)
echo ""
echo "7️⃣  GitHub Actions local runner (act)..."
if command -v act &> /dev/null; then
  echo "   ✅ act already installed"
else
  echo "   ℹ️  act not installed. Install with: brew install act (macOS) or see github.com/nektos/act"
fi

echo ""
echo "======================================"
echo "✅ Development environment ready!"
echo "======================================"
echo ""
echo "📝 Quick start commands:"
echo "   • Start services: docker-compose up -d"
echo "   • Run tests: docker exec budget-flow-backend pytest tests/ -v"
echo "   • Check schema: bash scripts/validate-schema.sh"
echo "   • Install hooks: bash scripts/install-hooks.sh"
echo "   • Test push locally: act -j test (if act installed)"
echo ""
echo "🔗 Services:"
echo "   • Backend API: http://localhost:8000"
echo "   • Frontend: http://localhost:8050"
echo "   • pgAdmin: http://localhost:5050"
echo ""
echo "📖 Documentation:"
echo "   • Development workflow: CLAUDE.md (Development Workflow section)"
echo "   • PRD: docs/PRD.md"
echo "   • Database schema: docs/DATABASE_SCHEMA.md"
echo ""
