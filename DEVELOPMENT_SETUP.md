# BudgetFlow Development Setup Guide

## Quick Start (First Time)

```bash
cd /path/to/budget-flow
bash scripts/setup-dev-env.sh
```

This one command:
- ✅ Starts Docker services
- ✅ Applies all database migrations
- ✅ Validates schema matches models
- ✅ Runs full test suite (151 tests)
- ✅ Installs git pre-commit/pre-push hooks

---

## Key Development Practices

### 🚨 CRITICAL: Schema Synchronization

**After ANY model change**, regenerate migrations immediately:

```bash
# 1. Edit a model file (e.g., app/models/account.py)
# 2. Regenerate migration
docker exec budget-flow-backend alembic revision --autogenerate -m "descriptive message"

# 3. Apply migration
docker exec budget-flow-backend alembic upgrade head

# 4. Verify schema
bash scripts/validate-schema.sh
```

**Common errors that indicate schema drift:**
- ❌ `ProgrammingError: column X does not exist`
- ❌ `UndefinedTable: relation X does not exist`
- ❌ 500 Internal Server Error on API calls

### 🔗 Pre-Push Hook (Automatic)

Before you push, the hook automatically:
1. Runs full test suite (151 tests required to pass)
2. Checks for schema drift (blocks if detected)
3. Shows helpful error messages

**If push is blocked:**
```bash
# Fix tests
docker exec budget-flow-backend python -m pytest tests/ -v

# Fix schema
docker exec budget-flow-backend alembic revision --autogenerate -m "fix schema"
docker exec budget-flow-backend alembic upgrade head
bash scripts/validate-schema.sh

# Try push again
git push
```

---

## Available Scripts

### `setup-dev-env.sh`
**One-time setup for new developers**

```bash
bash scripts/setup-dev-env.sh
```

Includes:
- Docker Compose startup
- Database migrations
- Schema validation
- Full test run
- Git hooks installation

### `install-hooks.sh`
**Setup or update git hooks**

```bash
bash scripts/install-hooks.sh
```

Installs:
- **pre-commit**: Detects merge conflicts and debug statements
- **pre-push**: Runs tests + validates schema before push

### `validate-schema.sh`
**Check if schema matches models**

```bash
bash scripts/validate-schema.sh
```

Shows:
- Current migration revision
- Schema drift detection
- List of all tables
- Migration history

---

## Development Workflow

1. **Create feature branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Write tests first** (TDD)
   ```bash
   # Edit backend/tests/unit/test_my_feature.py
   # Edit backend/tests/integration/test_my_feature.py
   ```

3. **Implement feature**
   ```bash
   # Edit models (if needed)
   docker exec budget-flow-backend alembic revision --autogenerate -m "add X"
   docker exec budget-flow-backend alembic upgrade head
   
   # Implement CRUD/service/endpoint
   ```

4. **Run tests**
   ```bash
   docker exec budget-flow-backend pytest tests/ -v
   ```

5. **Run schema check**
   ```bash
   bash scripts/validate-schema.sh
   ```

6. **Commit**
   ```bash
   git add .
   git commit -m "feat(module): description"
   ```

7. **Push** (pre-push hook will validate)
   ```bash
   git push origin feature/my-feature
   ```

8. **Create PR** on GitHub

---

## Pre-Push Hook Details

The pre-push hook runs these checks before allowing a push:

```
🔍 Pre-push validation starting...
  ▶ Running tests (151 expected)...
  ✅ Tests passed (151/151)
  ▶ Checking schema drift...
  ✅ Schema in sync
✅ All pre-push checks passed! Pushing...
```

### If Tests Fail
```
❌ Tests failed. Push blocked.
→ Fix errors: docker exec budget-flow-backend pytest tests/ -v
→ Commit fix: git add . && git commit -m "fix: ..."
→ Push again: git push
```

### If Schema Drifts
```
⚠️  Schema drift detected!
Run these commands:
  docker exec budget-flow-backend alembic revision --autogenerate -m 'fix schema'
  docker exec budget-flow-backend alembic upgrade head
Then commit and try again.
```

---

## GitHub Actions (CI/CD)

Workflows run automatically on every push:

### `.github/workflows/test.yml`
- **Unit Tests**: Runs on all branches
- **Integration Tests**: Runs on all branches
- **E2E Tests**: Runs only on `main`/`develop`/`master`
- **Code Quality**: Flake8, Black, isort checks

### Local Testing with `act` (Optional)

Test GitHub Actions locally before pushing:

```bash
# Install act (one-time)
# macOS: brew install act
# Linux: https://github.com/nektos/act

# Run tests locally
act -j test          # Unit + integration tests
act -j lint          # Code quality checks
act                  # All workflows
```

---

## Database Management

### Connect to Database

**pgAdmin** (Web UI):
- URL: http://localhost:5050
- Email: admin@admin.com
- Password: admin

**Command Line**:
```bash
docker exec budget-flow-postgres psql -U postgres -d budget_flow
```

### View Tables
```bash
docker exec budget-flow-postgres psql -U postgres -d budget_flow -c "\dt"
```

### Check Migrations
```bash
docker exec budget-flow-backend alembic current    # Current revision
docker exec budget-flow-backend alembic history    # All revisions
```

### Reset Database (⚠️ Careful!)
```bash
# Stop services
docker-compose down -v

# Start fresh
docker-compose up -d
bash scripts/setup-dev-env.sh
```

---

## Troubleshooting

### "500 Internal Server Error" on API calls
→ Usually indicates schema drift
```bash
bash scripts/validate-schema.sh
docker exec budget-flow-backend alembic revision --autogenerate -m "fix schema"
docker exec budget-flow-backend alembic upgrade head
```

### "Tests fail on CI but pass locally"
→ Usually a timing or Docker networking issue
```bash
# Restart services
docker-compose down -v
docker-compose up -d
bash scripts/setup-dev-env.sh
```

### "Pre-push hook blocks my push"
→ Read the hook output message — it tells you exactly what to fix
```bash
# Run the test suite manually
docker exec budget-flow-backend pytest tests/ -v

# Check schema
bash scripts/validate-schema.sh

# Commit any schema fixes
git add .
git commit -m "fix: schema drift"
```

### "Missing modules or dependencies"
→ Reinstall requirements
```bash
docker-compose down -v
docker-compose up -d --build
docker exec budget-flow-backend pip install -r requirements.txt
bash scripts/setup-dev-env.sh
```

---

## FAQ

**Q: Do I need to install `act`?**  
A: No, it's optional. GitHub Actions will still run on the remote. Use `act` if you want to test locally before pushing.

**Q: Can I disable the pre-push hook?**  
A: Not recommended, but yes: `rm .git/hooks/pre-push`. To reinstall: `bash scripts/install-hooks.sh`

**Q: What if I need to modify a model?**  
A: Always regenerate migrations:
```bash
docker exec budget-flow-backend alembic revision --autogenerate -m "model update"
docker exec budget-flow-backend alembic upgrade head
```

**Q: How many tests should there be?**  
A: 151 tests (as of April 2026). Check with: `docker exec budget-flow-backend pytest tests/ --collect-only | grep "test session" `

**Q: Where are the tests?**  
A: `backend/tests/unit/` and `backend/tests/integration/`

**Q: How do I add a new test?**  
A: See `CLAUDE.md` section "Testing Requirements"

---

## Support

- 📖 **Development Guidelines**: See `CLAUDE.md`
- 📋 **Product Requirements**: See `docs/PRD.md`
- 🗄️ **Database Schema**: See `docs/DATABASE_SCHEMA.md`
- 🚀 **Deployment**: See `docs/`

---

**Last Updated**: April 3, 2026  
**Status**: ✅ All 151 tests passing  
**Hooks**: ✅ Installed and tested
