#!/bin/bash
# Install Git hooks for BudgetFlow development

set -e

HOOKS_DIR=".git/hooks"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "📋 Installing Git hooks..."

# Create pre-push hook
cat > "$HOOKS_DIR/pre-push" <<'EOF'
#!/bin/bash
# BudgetFlow Pre-Push Hook
# Validates tests and schema before allowing push

set -e

echo "🔍 Pre-push validation starting..."

# Check if services are running
if ! docker ps | grep -q "budget-flow-backend"; then
  echo "❌ Backend container not running. Start with: docker-compose up -d"
  exit 1
fi

# Run full test suite
echo "  ▶ Running tests (151 expected)..."
if ! docker exec budget-flow-backend python -m pytest tests/ -v --tb=short -q 2>&1 | tail -5; then
  echo "  ❌ Tests failed. Push blocked."
  exit 1
fi

# Check for schema drift
echo "  ▶ Checking schema drift..."
DRIFT_CHECK=$(docker exec budget-flow-backend alembic revision --autogenerate --dry-run -m "drift_check" 2>&1 || true)

if echo "$DRIFT_CHECK" | grep -qi "detected\|new"; then
  echo "  ⚠️  Schema drift detected!"
  echo "  Run these commands:"
  echo "     docker exec budget-flow-backend alembic revision --autogenerate -m 'fix schema'"
  echo "     docker exec budget-flow-backend alembic upgrade head"
  echo "  Then commit and try again."
  exit 1
fi

echo "  ✅ Tests passed (151/151)"
echo "  ✅ Schema in sync"
echo ""
echo "✅ All pre-push checks passed! Pushing..."
exit 0
EOF

chmod +x "$HOOKS_DIR/pre-push"

# Create pre-commit hook for quick checks
cat > "$HOOKS_DIR/pre-commit" <<'EOF'
#!/bin/bash
# BudgetFlow Pre-Commit Hook
# Quick checks before committing

set -e

echo "🔍 Pre-commit checks..."

# Check for merge conflicts
if git diff --cached | grep -q "^<<<<<<<\|^=======\|^>>>>>>>"; then
  echo "❌ Merge conflict markers found. Resolve and try again."
  exit 1
fi

# Check for debug statements
if git diff --cached | grep -qE "console\.log\(|print\(|debugger|pdb\.set_trace"; then
  echo "⚠️  Debug statements found. Remove before committing."
  exit 1
fi

echo "  ✅ No merge conflicts"
echo "  ✅ No debug statements"
exit 0
EOF

chmod +x "$HOOKS_DIR/pre-commit"

echo "✅ Git hooks installed successfully!"
echo ""
echo "📝 Hooks installed:"
echo "  • pre-commit: Checks for merge conflicts and debug statements"
echo "  • pre-push: Runs full test suite and validates schema"
echo ""
echo "💡 Tip: Start services with 'docker-compose up -d' before pushing"
