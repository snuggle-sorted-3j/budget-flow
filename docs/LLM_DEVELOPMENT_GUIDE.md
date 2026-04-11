# BudgetFlow — LLM Development Guide

**MANDATORY:** Read and follow this guide every time you write, modify, or delete code in this project.  
This document codifies the patterns, conventions, and quality gates that keep the codebase consistent.

---

## 1. Before You Write Any Code

### 1.1 Orientation Checklist

Before implementing anything, gather context:

1. **Read the relevant endpoint file** — understand the current route signatures, status codes, and error patterns.
2. **Read the relevant CRUD module** — understand how DB operations are structured (no raw SQL; SQLAlchemy ORM only).
3. **Read the Pydantic schema** — understand the request/response contract.
4. **Read the existing tests** — understand what is already covered before writing new tests.
5. **Check `docs/TEST_STRATEGY.md`** — understand the test hierarchy and where new tests belong.

### 1.2 Architecture Quick Reference

```
Request → FastAPI Endpoint → CRUD module → SQLAlchemy Model → PostgreSQL
                ↑                  ↑
            Pydantic Schema    Business Logic (services/)
```

- **Endpoints** (`app/api/v1/endpoints/`) — HTTP handling, validation, authorization. NO business logic here.
- **CRUD** (`app/crud/`) — Database operations. One module per model. Returns ORM objects.
- **Services** (`app/services/`) — Complex business logic (reconciliation, analytics). Called by endpoints.
- **Schemas** (`app/schemas/`) — Pydantic models for request/response. Never return SQLAlchemy models directly.
- **Models** (`app/models/`) — SQLAlchemy ORM. UUID primary keys, DECIMAL for money, timestamps on all tables.

---

## 2. Adding a New Feature (Full Checklist)

Follow this exact sequence. Do not skip steps.

### Step 1: Model (if new table needed)

```python
# app/models/new_thing.py
import uuid
from sqlalchemy import Column, String, ForeignKey, DECIMAL, TIMESTAMP, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base

class NewThing(Base):
    __tablename__ = "new_things"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(DECIMAL(15, 2), nullable=False)          # Always DECIMAL for money
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
```

**Rules:**
- UUID primary keys everywhere — no auto-increment integers
- `DECIMAL(15, 2)` for ALL monetary values — never `Float` or `Integer`
- Always add `user_id` FK with index for multi-tenant isolation
- Always include `created_at` and `updated_at` timestamps
- Add `index=True` on columns used in WHERE clauses or JOINs

**After creating a model, immediately generate migration:**
```bash
docker exec budget-flow-backend alembic revision --autogenerate -m "add new_things table"
docker exec budget-flow-backend alembic upgrade head
```

### Step 2: Schema

```python
# app/schemas/new_thing.py
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

class NewThingCreate(BaseModel):
    name: str = Field(..., max_length=255)
    amount: Decimal = Field(..., gt=0)
    currency_id: UUID

class NewThingUpdate(BaseModel):
    name: str | None = None
    amount: Decimal | None = Field(None, gt=0)

class NewThingResponse(BaseModel):
    id: UUID
    name: str
    amount: Decimal
    currency_id: UUID

    model_config = ConfigDict(from_attributes=True)
```

**Rules:**
- Create/Update/Response — always three schemas per resource
- Use `Field(gt=0)` for monetary amounts
- Use `ConfigDict(from_attributes=True)` on response schemas (not `class Config`)
- `Update` schema: all fields Optional (partial update via PATCH)

### Step 3: CRUD

```python
# app/crud/new_thing.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.new_thing import NewThing
from app.schemas.new_thing import NewThingCreate, NewThingUpdate

def create_new_thing(db: Session, user_id: UUID, data: NewThingCreate) -> NewThing:
    db_obj = NewThing(user_id=user_id, **data.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_new_thing(db: Session, thing_id: UUID) -> Optional[NewThing]:
    return db.get(NewThing, thing_id)

def list_new_things(db: Session, user_id: UUID) -> List[NewThing]:
    stmt = select(NewThing).where(NewThing.user_id == user_id)
    return list(db.execute(stmt).scalars().all())

def update_new_thing(db: Session, db_obj: NewThing, data: NewThingUpdate) -> NewThing:
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(db_obj, field, value)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_new_thing(db: Session, db_obj: NewThing) -> None:
    db.delete(db_obj)
    db.commit()
```

**Rules:**
- One CRUD module per model — no cross-model queries (put those in services/)
- Always use `select()` builder, not `db.query()` (SQLAlchemy 2.0 style)
- Use `joinedload()` for relationships that will be serialized
- Never call `db.commit()` inside service functions — only in CRUD

### Step 4: Endpoint

```python
# app/api/v1/endpoints/new_things.py
from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api import deps
from app.crud import new_thing as crud_new_thing
from app.crud import currency as crud_currency
from app.models.user import User
from app.schemas.new_thing import NewThingCreate, NewThingResponse

router = APIRouter()

@router.post("/", response_model=NewThingResponse, status_code=status.HTTP_201_CREATED)
def create_new_thing(
    *,
    db: Session = Depends(deps.get_db),
    data_in: NewThingCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    # 1. Validate foreign keys
    currency = crud_currency.get_currency_by_id(db=db, user_id=current_user.id, currency_id=data_in.currency_id)
    if not currency:
        raise HTTPException(status_code=400, detail="Currency not found or access denied")

    return crud_new_thing.create_new_thing(db=db, user_id=current_user.id, data=data_in)


@router.get("/", response_model=List[NewThingResponse])
def list_new_things(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    return crud_new_thing.list_new_things(db=db, user_id=current_user.id)


@router.patch("/{thing_id}", response_model=NewThingResponse)
def update_new_thing(
    *,
    db: Session = Depends(deps.get_db),
    thing_id: UUID,
    data_in: NewThingUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    thing = crud_new_thing.get_new_thing(db=db, thing_id=thing_id)
    if not thing:
        raise HTTPException(status_code=404, detail="Not found")
    if thing.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return crud_new_thing.update_new_thing(db=db, db_obj=thing, data=data_in)


@router.delete("/{thing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_new_thing(
    *,
    db: Session = Depends(deps.get_db),
    thing_id: UUID,
    current_user: User = Depends(deps.get_current_user),
) -> None:
    thing = crud_new_thing.get_new_thing(db=db, thing_id=thing_id)
    if not thing:
        raise HTTPException(status_code=404, detail="Not found")
    if thing.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    crud_new_thing.delete_new_thing(db=db, db_obj=thing)
```

**Endpoint Authorization Pattern (CRITICAL):**

Every endpoint that modifies or reads a specific resource MUST:
1. Fetch the resource
2. Check it exists (→ 404 if not)
3. Check it belongs to `current_user` (→ 403 if not)
4. Check business rules (e.g., period not finalized → 400 if finalized)

Standard error response pattern:
```python
# 404 — resource does not exist
if not resource:
    raise HTTPException(status_code=404, detail="Resource not found")

# 403 — exists but belongs to another user
if resource.user_id != current_user.id:
    raise HTTPException(status_code=403, detail="Not authorized")

# 400 — business rule violation
if period.status == "FINALIZED":
    raise HTTPException(status_code=400, detail="Cannot modify a finalized period")

# 400 — invalid FK reference
if not currency:
    raise HTTPException(status_code=400, detail="Currency not found or access denied")
```

### Step 5: Register the Router

```python
# app/api/v1/api.py — add one line
from app.api.v1.endpoints import new_things
api_router.include_router(new_things.router, prefix="/new-things", tags=["New Things"])
```

### Step 6: Write Tests (MANDATORY — do not skip)

See Section 3 below.

---

## 3. Testing Requirements

### 3.1 What Tests to Write

Every endpoint MUST have:

| Test Type | Required? | Example |
|-----------|-----------|---------|
| **Happy path** (create, read, update, delete) | YES | POST valid data → 201 |
| **Not found** (404) | YES | GET non-existent UUID → 404 |
| **Invalid input** (400) | YES | POST with bad FK → 400 |
| **Wrong user** (403) | YES | PATCH resource owned by other user → 403 |
| **Unauthorized** (401) | YES (at least 1 per resource) | GET without auth header → 401 |
| **Finalized period** (400) | IF APPLICABLE | POST to finalized period → 400 |
| **Duplicate** (400) | IF APPLICABLE | POST duplicate name → 400 |

### 3.2 Test File Naming

```
tests/integration/test_{resource}_api.py        — CRUD + happy path tests
tests/integration/test_{resource}_errors.py      — Error path tests (404/400/403)
tests/integration/test_{resource}_flow.py        — Multi-step workflow tests
tests/integration/test_e2e_workflows.py          — Cross-resource E2E scenarios
tests/unit/test_{service_name}.py                — Unit tests for services
```

### 3.3 Test Structure Pattern

```python
"""
Integration tests for /api/v1/new-things endpoints.
Covers: create 201/400, list 200, update 200/404/403, delete 204/404/403.
"""
import uuid
from typing import Dict
from fastapi.testclient import TestClient
from app.models.currency import Currency


def _create_new_thing(client, headers, currency_id, name="Test"):
    """Helper — keeps tests DRY."""
    resp = client.post("/api/v1/new-things/", json={
        "name": name,
        "amount": "100.00",
        "currency_id": str(currency_id)
    }, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestCreateNewThing:

    def test_create_success(self, client: TestClient, auth_headers: Dict, test_currency: Currency):
        """POST valid data returns 201."""
        resp = client.post("/api/v1/new-things/", json={
            "name": "My Thing",
            "amount": "250.00",
            "currency_id": str(test_currency.id)
        }, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "My Thing"
        assert float(data["amount"]) == 250.0
        assert "id" in data

    def test_create_invalid_currency_returns_400(self, client: TestClient, auth_headers: Dict):
        """POST with non-existent currency returns 400."""
        resp = client.post("/api/v1/new-things/", json={
            "name": "Bad Currency",
            "amount": "100.00",
            "currency_id": str(uuid.uuid4())
        }, headers=auth_headers)
        assert resp.status_code == 400
        assert "currency" in resp.json()["detail"].lower()

    def test_create_no_auth_returns_401(self, client: TestClient, test_currency: Currency):
        """POST without auth returns 401."""
        resp = client.post("/api/v1/new-things/", json={
            "name": "No Auth", "amount": "100.00", "currency_id": str(test_currency.id)
        })
        assert resp.status_code == 401


class TestUpdateNewThing:

    def test_update_success(self, client: TestClient, auth_headers: Dict, test_currency: Currency):
        """PATCH valid data returns 200."""
        thing = _create_new_thing(client, auth_headers, test_currency.id)
        resp = client.patch(f"/api/v1/new-things/{thing['id']}", json={
            "name": "Updated"
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated"

    def test_update_not_found_returns_404(self, client: TestClient, auth_headers: Dict):
        """PATCH non-existent thing returns 404."""
        resp = client.patch(f"/api/v1/new-things/{uuid.uuid4()}", json={
            "name": "X"
        }, headers=auth_headers)
        assert resp.status_code == 404

    def test_update_wrong_user_returns_403(
        self, client: TestClient, auth_headers: Dict, test_currency: Currency, db
    ):
        """PATCH thing owned by another user returns 403."""
        thing = _create_new_thing(client, auth_headers, test_currency.id)

        from app.models.user import User
        from app.core.security import get_password_hash, create_access_token
        other = User(
            id=uuid.uuid4(),
            email=f"other-{uuid.uuid4()}@test.com",
            password_hash=get_password_hash("pw"),
            full_name="Other",
            is_active=True
        )
        db.add(other)
        db.commit()
        other_token = create_access_token(data={"sub": str(other.id)})
        other_headers = {"Authorization": f"Bearer {other_token}"}

        resp = client.patch(f"/api/v1/new-things/{thing['id']}", json={
            "name": "Hack"
        }, headers=other_headers)
        assert resp.status_code == 403


class TestDeleteNewThing:

    def test_delete_success(self, client: TestClient, auth_headers: Dict, test_currency: Currency):
        """DELETE returns 204."""
        thing = _create_new_thing(client, auth_headers, test_currency.id)
        resp = client.delete(f"/api/v1/new-things/{thing['id']}", headers=auth_headers)
        assert resp.status_code == 204

    def test_delete_not_found_returns_404(self, client: TestClient, auth_headers: Dict):
        """DELETE non-existent thing returns 404."""
        resp = client.delete(f"/api/v1/new-things/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404
```

### 3.4 Testing "Wrong User" (403 pattern)

This pattern is reused everywhere. Create a second user directly via DB:

```python
from app.models.user import User
from app.core.security import get_password_hash, create_access_token

other = User(
    id=uuid.uuid4(),
    email=f"other-{uuid.uuid4()}@test.com",
    password_hash=get_password_hash("pw"),
    full_name="Other",
    is_active=True
)
db.add(other)
db.commit()
other_token = create_access_token(data={"sub": str(other.id)})
other_headers = {"Authorization": f"Bearer {other_token}"}
```

### 3.5 Testing Finalized Period Blocks (400 pattern)

```python
from app.models.calculation_period import CalculationPeriod

p = db.get(CalculationPeriod, period["id"])
p.status = "FINALIZED"
db.commit()

resp = client.post(f"/api/v1/periods/{period['id']}/expenses", json={...}, headers=auth_headers)
assert resp.status_code == 400
assert "finalized" in resp.json()["detail"].lower()
```

### 3.6 Available Fixtures (from conftest.py)

| Fixture | Type | Scope | Provides |
|---------|------|-------|----------|
| `db` | Session | function | Clean DB session (rolled back after each test) |
| `client` | TestClient | function | FastAPI test client using `db` |
| `test_user` | User | function | Authenticated user in DB |
| `test_token` | str | function | Valid JWT for test_user |
| `auth_headers` | dict | function | `{"Authorization": "Bearer <token>"}` |
| `test_currency` | Currency | function | USD currency for test_user |
| `test_category` | ExpenseCategory | function | Test expense category for test_user |

### 3.7 Running Tests

```bash
# Run all tests (must pass before committing)
docker exec budget-flow-backend python -m pytest tests/ -v

# Run single file
docker exec budget-flow-backend python -m pytest tests/integration/test_new_things.py -v

# Run with coverage
docker exec budget-flow-backend python -m pytest tests/ --cov=app --cov-report=term-missing

# Run specific test
docker exec budget-flow-backend python -m pytest tests/integration/test_new_things.py::TestCreateNewThing::test_create_success -v
```

**Coverage Requirements:**
- New endpoint files: aim for 100%
- New service files: aim for 100% line + 80% mutation kill rate
- Overall project: maintain ≥ 95%

---

## 4. Modifying Existing Code

### 4.1 Before Changing an Endpoint

1. Read the current test files for that endpoint
2. Run those tests to confirm they pass BEFORE your change
3. Make the change
4. Run the tests again — if any fail, fix your code (not the tests) unless the test expectation was wrong
5. If you changed a status code or response shape, update the corresponding test

### 4.2 Before Changing a Model

1. Make the model change
2. Generate migration: `docker exec budget-flow-backend alembic revision --autogenerate -m "description"`
3. Review the generated migration file
4. Apply: `docker exec budget-flow-backend alembic upgrade head`
5. Run full test suite to catch breakage

**WARNING:** Forgetting the migration causes `ProgrammingError: column X does not exist` in production.

### 4.3 Before Changing Business Logic (services/)

1. Read the unit tests for that service
2. Run them to confirm green
3. Make your change
4. Run unit tests — they should catch regressions
5. If you added a new code path, add a test for it

---

## 5. Code Style & Conventions

### 5.1 Money Handling

```python
# CORRECT — always use Decimal
from decimal import Decimal
amount = Decimal("100.00")
total = amount + Decimal("50.00")

# WRONG — float causes rounding errors
amount = 100.00
total = amount + 50.00  # could be 149.99999999999997
```

**In models:** `Column(DECIMAL(15, 2))`  
**In schemas:** `amount: Decimal = Field(..., gt=0)`  
**In services:** `Decimal(str(value))` when converting from external sources

### 5.2 UUID Handling

```python
# In test assertions — always compare as strings
assert str(response["currency_id"]) == str(test_currency.id)

# In API requests — always serialize to string
json={"currency_id": str(test_currency.id)}
```

### 5.3 Error Messages

Keep error messages consistent:
```python
"Not found"                              # Generic 404
"Period not found"                       # Specific 404
"Not authorized"                         # 403 wrong user
"Currency not found or access denied"    # 400 bad FK
"Cannot modify a finalized period"       # 400 business rule
"Cannot delete system category"          # 400 protected resource
```

### 5.4 Imports

```python
# Standard library
import uuid
from typing import Any, List
from uuid import UUID

# Third party
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Local
from app.api import deps
from app.crud import thing as crud_thing
from app.models.user import User
from app.schemas.thing import ThingCreate, ThingResponse
```

---

## 6. Common Pitfalls

### 6.1 Forgetting Multi-Tenant Isolation

Every query MUST filter by `user_id`. Never return data from other users.

```python
# CORRECT
stmt = select(Account).where(Account.user_id == user_id)

# WRONG — returns ALL users' accounts
stmt = select(Account)
```

### 6.2 Forgetting Period Status Checks

Any endpoint that modifies period data must check:
```python
if period.status == "FINALIZED":
    raise HTTPException(status_code=400, detail="Cannot modify a finalized period")
```

### 6.3 Not Validating Foreign Keys

Before creating a resource with a FK, always verify the FK target exists AND belongs to the current user:
```python
currency = crud_currency.get_currency_by_id(db=db, user_id=current_user.id, currency_id=data.currency_id)
if not currency:
    raise HTTPException(status_code=400, detail="Currency not found or access denied")
```

### 6.4 Using Float for Money

Never use `float` for financial calculations. The `Decimal` type preserves precision:
```python
# CORRECT
Decimal(str(cat["total"])) / total_expenses * 100

# WRONG — produces float rounding errors
float(cat["total"]) / float(total_expenses) * 100
```

### 6.5 Forgetting to Write Tests

If you add a new endpoint and do NOT write tests, you break the project quality contract. The minimum test set is:
- 1 happy path test
- 1 not-found test (404)
- 1 unauthorized test (401)

That is 3 tests. Anything less is unacceptable.

---

## 7. Quick Reference: Endpoint → Test Mapping

When you create or modify an endpoint, use this checklist:

```
POST /resource/          → test_create_success (201)
                         → test_create_invalid_fk (400)
                         → test_create_no_auth (401)

GET /resource/           → test_list_success (200)
                         → test_list_no_auth (401)

GET /resource/{id}       → test_get_success (200)
                         → test_get_not_found (404)

PATCH /resource/{id}     → test_update_success (200)
                         → test_update_not_found (404)
                         → test_update_wrong_user (403)
                         → test_update_finalized_period (400) [if period-scoped]

DELETE /resource/{id}    → test_delete_success (200/204)
                         → test_delete_not_found (404)
                         → test_delete_wrong_user (403)
```

---

## 8. Quality Metrics & Mutation Testing

### 8.1 Coverage Metrics Explained

We track three types of coverage. Understanding the difference matters.

**Line Coverage** — measures which lines of code execute during tests.
- Current: **98%** (2585 statements, 39 missed)
- Target for new code: **100%** for endpoints and CRUD, **95%+** for services
- Limitation: a line can execute without the test actually verifying its behavior

**Branch Coverage** — measures which conditional branches (if/else, ternary, short-circuit) execute.
- Current: **97%** (444 branches, 34 missed)
- More rigorous than line coverage because it catches untested conditional paths
- Example: `if user.is_active` — line coverage says "covered" if the `True` branch runs; branch coverage requires BOTH `True` and `False` branches to run

```bash
# Run with branch coverage
docker exec budget-flow-backend python -m pytest tests/ --cov=app --cov-branch --cov-report=term-missing
```

Output columns: `Stmts   Miss  Branch  BrPart  Cover  Missing`
- `Stmts` — total executable statements
- `Miss` — statements never executed
- `Branch` — total conditional branches
- `BrPart` — branches only partially covered (one arm tested, not the other)
- `Cover` — combined line + branch percentage

**Mutation Kill Rate** — measures whether tests actually detect logic errors, not just exercise code.
- Current: **77.2%** (analytics), **92.3%** (reconciliation)
- The strongest quality metric: proves tests catch real bugs

### 8.2 What Mutation Testing Is and Why We Use It

**Problem:** A test can achieve 100% line and branch coverage without actually asserting anything useful. Example:

```python
def test_calculate_total():
    result = calculate_total(items)
    # 100% coverage — but no assertion! Bug goes undetected.
```

**Solution:** Mutation testing (via `mutmut`) systematically injects small bugs into the source code and checks if the test suite catches them.

**How it works:**
1. mutmut creates "mutants" — copies of the code with one change each:
   - `+` → `-` (arithmetic)
   - `>=` → `>` (boundary)
   - `True` → `False` (logic)
   - `"FINALIZED"` → `"XXFINALIZEDXX"` (string)
   - `return result` → `return None` (return value)
2. For each mutant, it runs the test suite
3. If any test fails → mutant is **killed** (test caught the bug) ✅
4. If all tests pass → mutant **survived** (test missed the bug) ❌

**Kill Rate = killed / total mutants**

| Kill Rate | Quality |
|-----------|---------|
| > 90% | Excellent — tests catch almost all logic errors |
| 70-90% | Strong — some edge cases missed, acceptable for most services |
| 50-70% | Weak — significant gaps, needs more targeted tests |
| < 50% | Poor — tests exercise code but don't verify behavior |

### 8.3 Running Mutation Tests

**When to run:** After writing a new service or significantly changing business logic. Not required for simple CRUD endpoints.

```bash
# Safe pattern — always restores file on exit (even on crash/OOM)
docker exec budget-flow-backend bash -c "
cd /app
cp app/services/my_service.py /tmp/my_service_backup.py
mutmut run \
  --paths-to-mutate app/services/my_service.py \
  --runner 'python -m pytest tests/unit/test_my_service.py -q --tb=no -k \"not Kill\"' \
  --no-progress 2>&1
cp /tmp/my_service_backup.py app/services/my_service.py
echo 'File restored'
"
```

**CRITICAL SAFETY RULE:** mutmut modifies the source file directly. If the process crashes (OOM, signal kill), the source file is left in a mutated state. ALWAYS:
1. Back up the file before running
2. Restore from backup after running
3. Verify with `git diff` that the file is clean

**Checking results:**
```bash
# Summary
docker exec budget-flow-backend bash -c "cd /app && python -m mutmut results"

# Show what a specific surviving mutant changed
docker exec budget-flow-backend bash -c "cd /app && python -m mutmut show <id>"
```

**Analyzing survivors:**
- **Crash-type survivors** (string mutations like `"XXtotalXX"`, `None` assignments) — acceptable; they cause TypeError/KeyError, not wrong results
- **Logic survivors** (operator changes like `>` → `>=`, `+` → `-`) — these are real gaps; write a test that catches them
- **Boundary survivors** (`<` → `<=`) — often acceptable if the boundary is arbitrary, but review case-by-case

### 8.4 Current Metrics Baseline (2026-04-11)

| Metric | Value | Notes |
|--------|-------|-------|
| **Total Tests** | 481 | 116 unit + 360 integration + 5 E2E |
| **Line Coverage** | 98% | 2585 stmts, 39 missed |
| **Branch Coverage** | 97% | 444 branches, 34 missed (partially covered) |
| **Combined (line+branch)** | 97% | pytest-cov `--cov-branch` combined metric |
| **Mutation Kill Rate (analytics)** | 77.2% | 233 killed / 69 survived / 302 total |
| **Mutation Kill Rate (reconciliation)** | 92.3% | 143 killed / 12 survived / 155 total |
| **Test Execution Time** | ~90s | Full suite including DB setup |
| **Endpoint Coverage** | 95% | 12/18 endpoints at 100% |

**Do not let these metrics drop.** If you add code and coverage goes down, add tests before committing.

---

## 9. Final Validation Before Committing

```bash
# 1. Run full test suite
docker exec budget-flow-backend python -m pytest tests/ -v --tb=short

# 2. Check coverage (line + branch) didn't drop
docker exec budget-flow-backend python -m pytest tests/ --cov=app --cov-branch --cov-report=term-missing

# 3. Check for schema drift (if model changed)
docker exec budget-flow-backend alembic current

# 4. Verify new code doesn't introduce security issues
docker exec budget-flow-backend bandit -r app/ -ll 2>/dev/null || true
```

If any of these fail, fix before committing. Do not bypass.

---

## 10. Document Maintenance

When you add a new endpoint or change test structure:
- Update `docs/TEST_STRATEGY.md` with new test counts and coverage numbers
- If you add a new model, update `docs/DATABASE_SCHEMA.md`
- Keep this guide's examples current with real code patterns

---

**This guide is the source of truth for development conventions.**  
**Follow it. Every time. No exceptions.**
