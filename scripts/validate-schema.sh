#!/bin/bash
# BudgetFlow Schema Validation Script
# Detects schema drift between models and database

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "🔍 BudgetFlow Schema Validator"
echo "=============================="
echo ""

# Check if services are running
if ! docker ps | grep -q "budget-flow-backend"; then
  echo "❌ Backend container not running. Start with:"
  echo "   docker-compose up -d"
  exit 1
fi

if ! docker ps | grep -q "budget-flow-postgres"; then
  echo "❌ Database container not running. Start with:"
  echo "   docker-compose up -d"
  exit 1
fi

echo "✅ Containers running"
echo ""

# Get current migration version
CURRENT_MIGRATION=$(docker exec budget-flow-backend alembic current 2>&1 | grep -oE '[a-f0-9]{12}' | tail -1)
echo "📍 Current migration: $CURRENT_MIGRATION"

# Check for pending migrations
echo ""
echo "🔎 Checking for schema drift..."
DRIFT=$(docker exec budget-flow-backend alembic revision --autogenerate --dry-run -m "drift_check" 2>&1 || true)

if echo "$DRIFT" | grep -qi "detected\|new column\|new table"; then
  echo ""
  echo "⚠️  SCHEMA DRIFT DETECTED!"
  echo ""
  echo "Models and database schema are out of sync."
  echo ""
  echo "Fix by running:"
  echo "  docker exec budget-flow-backend alembic revision --autogenerate -m 'fix schema drift'"
  echo "  docker exec budget-flow-backend alembic upgrade head"
  echo ""
  echo "Generated migration:"
  echo "$DRIFT"
  exit 1
else
  echo "✅ No schema drift detected"
fi

# List tables
echo ""
echo "📊 Current database tables:"
docker exec budget-flow-postgres psql -U postgres -d budget_flow -c "\dt" 2>&1 | tail -20

echo ""
echo "✅ Schema validation passed!"
echo ""
echo "📝 Migration history:"
docker exec budget-flow-backend alembic history --verbose 2>&1 | tail -10
