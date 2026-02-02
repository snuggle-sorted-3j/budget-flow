
---

# Cursor AI Rules for BudgetFlow

This file provides context and guidelines for Cursor AI when working on the BudgetFlow project.

## Project Overview

BudgetFlow is a personal finance tracking and reconciliation system with:
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL
- **Frontend**: Plotly Dash
- **Database**: PostgreSQL 15+
- **Deployment**: Docker + AWS (ECS Fargate + RDS)

## Core Architecture Principles

1. **Separation of Concerns**: Backend API (FastAPI) separate from frontend UI (Dash)
2. **Modular Design**: Each feature in its own module with clear boundaries
3. **Type Safety**: Use Python type hints everywhere, enforced by mypy
4. **Test-Driven Development (TDD)**: Mandatory. Write unit/integration tests BEFORE implementing logic.
5. **Full Test Validation**: Always run the ENTRE test suite (`pytest backend/tests/ -v`) before assuming a task is complete. Never skip integration tests.
6. **Security-First**: JWT auth, bcrypt passwords, input validation with Pydantic.
7. **Zero-Broken-Frontend**: Ensure all Dash components and callbacks Target existing IDs. Check for ID mismatches after layout changes.

## File Organization

### Backend Structure
```
backend/app/
├── api/v1/endpoints/     # API route handlers
├── core/                 # Config, security, exceptions
├── models/               # SQLAlchemy ORM models
├── schemas/              # Pydantic validation schemas
├── services/             # Business logic layer
├── crud/                 # Database operations
└── main.py               # FastAPI app entry point
```

### Frontend Structure
```
frontend/app/
├── layouts/              # Page layouts
├── tabs/                 # Tab components (tab1_*.py, tab2_*.py, etc.)
├── components/           # Reusable UI components
├── callbacks/            # Dash callback functions
├── utils/                # Helper functions (API client, formatters)
└── main.py               # Dash app entry point
```

## Coding Standards

### Python Style
- **Formatter**: Black (line length: 100)
- **Linter**: Flake8
- **Type Checker**: Mypy
- **Security Scanner**: Bandit
- **Import Sorter**: isort

### Naming Conventions
- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions/Variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private members**: `_leading_underscore`

### Type Hints
Always use type hints for function signatures:
```python
def calculate_reconciliation(
    period_id: UUID,
    currency_id: UUID,
    db: Session
) -> Dict[str, Decimal]:
    ...
```

### Docstrings
Use Google-style docstrings:
```python
def reconcile_period(period_id: UUID, db: Session) -> ReconciliationResult:
    """Calculate reconciliation difference for a calculation period.
    
    Args:
        period_id: UUID of the calculation period
        db: Database session
        
    Returns:
        ReconciliationResult containing difference per currency
        
    Raises:
        PeriodNotFoundError: If period doesn't exist
        PeriodNotFinalizedError: If period already finalized
    """
```

## Database Patterns

### Models
- Use UUID primary keys: `id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)`
- Use DECIMAL for money: `amount = Column(DECIMAL(15, 2), nullable=False)`
- Use timestamps: `created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())`
- Add indexes for foreign keys and frequently queried columns

### Migrations
- Always review auto-generated Alembic migrations
- Test migrations on test database before applying to production
- Always include downgrade logic
- Never edit already-applied migrations

### Queries
- Use SQLAlchemy ORM, not raw SQL (unless performance-critical)
- Use eager loading to prevent N+1 queries: `.options(joinedload(Model.relationship))`
- Add database constraints (CHECK, UNIQUE, NOT NULL) for data integrity

## API Patterns

### Endpoints
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.schemas.period import PeriodCreate, PeriodResponse
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=PeriodResponse)
def create_period(
    period: PeriodCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PeriodResponse:
    # Implementation
    pass
```

### Response Models
- Always use Pydantic schemas for request/response validation
- Never return SQLAlchemy models directly
- Use `response_model` parameter in route decorators

### Error Handling
```python
from app.core.exceptions import PeriodNotFoundError

try:
    period = get_period(period_id, db)
except PeriodNotFoundError:
    raise HTTPException(status_code=404, detail="Period not found")
```

## Frontend Patterns

### Dash Callbacks
```python
from dash import Input, Output, State, callback

@callback(
    Output('expense-total', 'children'),
    Input('expense-items-store', 'data'),
    prevent_initial_call=True
)
def update_expense_total(expense_items: List[Dict]) -> str:
    total = sum(item['amount'] for item in expense_items)
    return f"Total: {total:.2f} PLN"
```

### API Communication
Always use the APIClient utility:
```python
from app.utils.api_client import APIClient

client = APIClient()
periods = client.get("/periods")
```

### State Management
Use `dcc.Store` for shared state across tabs:
```python
dcc.Store(id='user-store', data={}),
dcc.Store(id='period-store', data={}),
```

## Testing Requirements

### Unit Tests
```python
import pytest
from app.services.reconciliation_service import calculate_difference

def test_reconciliation_zero_difference():
    # Test reconciliation with balanced period
    result = calculate_difference(
        starting_balance=1000,
        income=500,
        expenses=500
    )
    assert result == 0
```

### Integration Tests
```python
def test_create_period_api(test_client, test_user, test_token):
    response = test_client.post(
        "/api/v1/periods",
        json={"period_name": "November 2025", "snapshot_date": "2025-11-30"},
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 201
    assert response.json()["period_name"] == "November 2025"
```

### Test Coverage
- Minimum 80% coverage for all modules
- 100% coverage for business logic (reconciliation, calculations)
- Run tests before committing: `pytest tests/ -v --cov=app`

## Security Guidelines

### Authentication
- Use JWT tokens with 24-hour expiration
- Store tokens securely (httpOnly cookies in production)
- Validate tokens on every protected endpoint

### Password Handling
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash passwords
hashed = pwd_context.hash("plain_password")

# Verify passwords
pwd_context.verify("plain_password", hashed)
```

### Input Validation
- Always use Pydantic schemas for API input validation
- Sanitize user input to prevent injection attacks
- Use parameterized queries (SQLAlchemy handles this)

### Environment Variables
Never commit secrets:
```python
# ✅ Correct
JWT_SECRET = os.getenv("JWT_SECRET")

# ❌ Wrong
JWT_SECRET = "hardcoded-secret-key"
```

## Git Workflow

### Branch Naming
- `feature/add-suspended-transactions`
- `fix/reconciliation-rounding-error`
- `test/add-period-integration-tests`
- `refactor/improve-api-response-models`

### Commit Messages
Follow Conventional Commits:
```
feat(periods): add flexible date range support
fix(reconciliation): correct multi-currency calculation
test(expenses): add unit tests for category validation
docs(readme): update deployment instructions
```

### Pull Requests
- One feature per PR
- Include tests
- Update documentation if needed
- Run pre-commit hooks before pushing

## Development Workflow

### Local Setup
```bash
# Start services
docker-compose up -d

# Run migrations
docker-compose exec backend alembic upgrade head

# Run tests
docker-compose exec backend pytest tests/ -v
```

### Adding a New Feature

1. **Create branch**: `git checkout -b feature/investment-tracking`
2. **Write tests first** (TDD approach)
3. **Implement feature**:
   - Add database model (if needed)
   - Create Pydantic schemas
   - Implement CRUD operations
   - Add API endpoints
   - Implement frontend UI
   - Write callbacks
4. **Run tests**: `pytest tests/ -v`
5. **Run quality checks**: `pre-commit run --all-files`
6. **Commit**: `git commit -m "feat(investments): add investment tracking"`
7. **Push and create PR**

### Adding a Database Migration
```bash
# Generate migration
alembic revision --autogenerate -m "add investment accounts table"

# Review generated migration file
cat alembic/versions/xxxx_add_investment_accounts.py

# Apply migration
alembic upgrade head

# Test rollback
alembic downgrade -1
alembic upgrade head
```

## Common Patterns

### Creating a New API Endpoint

1. **Define schema** (`app/schemas/investment.py`):
```python
from pydantic import BaseModel
from uuid import UUID
from decimal import Decimal

class InvestmentCreate(BaseModel):
    category_name: str
    investment_account_id: UUID | None
    opening_balance: Decimal | None

class InvestmentResponse(BaseModel):
    id: UUID
    category_name: str
    total_value: Decimal
    
    class Config:
        from_attributes = True
```

2. **Create CRUD** (`app/crud/investment.py`):
```python
from sqlalchemy.orm import Session
from app.models.investment import Investment

def create_investment(
    db: Session,
    user_id: UUID,
    investment: InvestmentCreate
) -> Investment:
    db_investment = Investment(
        user_id=user_id,
        **investment.model_dump()
    )
    db.add(db_investment)
    db.commit()
    db.refresh(db_investment)
    return db_investment
```

3. **Add endpoint** (`app/api/v1/endpoints/investments.py`):
```python
@router.post("/", response_model=InvestmentResponse)
def create_investment_endpoint(
    investment: InvestmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> InvestmentResponse:
    return create_investment(db, current_user.id, investment)
```

4. **Write tests** (`tests/integration/test_investments.py`)

### Creating a New Dash Tab

1. **Create tab file** (`frontend/app/tabs/tab7_investments.py`):
```python
from dash import html, dcc
import dash_bootstrap_components as dbc

def create_layout():
    return dbc.Container([
        html.H2("Investments"),
        dcc.Store(id='investments-store'),
        # Add components
    ])
```

2. **Add callbacks** (`frontend/app/callbacks/investment_callbacks.py`):
```python
from dash import Input, Output, callback
from app.utils.api_client import APIClient

client = APIClient()

@callback(
    Output('investments-store', 'data'),
    Input('refresh-investments', 'n_clicks')
)
def load_investments(n_clicks):
    if n_clicks:
        return client.get("/investments")
    return []
```

3. **Register in main layout**

## Performance Optimization

### Database
- Use indexes on frequently queried columns
- Use `select_related` and `prefetch_related` to reduce queries
- Implement pagination for large datasets
- Use database connection pooling

### API
- Implement caching for read-heavy endpoints (Redis in Phase 2)
- Use background tasks for heavy computations (Celery in Phase 3)
- Compress responses (gzip middleware)

### Frontend
- Use `dcc.Store` for client-side caching
- Debounce inputs (500ms delay before API calls)
- Lazy load large datasets
- Use `prevent_initial_call=True` to avoid unnecessary callbacks

## Troubleshooting

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose ps

# View logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

### Migration Conflicts
```bash
# Check current revision
alembic current

# View migration history
alembic history

# Rollback to specific revision
alembic downgrade <revision_id>
```

### API Errors
- Check FastAPI logs: `docker-compose logs backend`
- Test endpoints with OpenAPI docs: `http://localhost:8000/docs`
- Validate request body with Pydantic schemas

## Documentation Updates

When adding features, update these files:
- `docs/PRD.md` - If feature changes product requirements
- `docs/DATABASE_SCHEMA.md` - If adding/modifying tables
- `docs/API_SPECIFICATION.md` - If adding/modifying endpoints
- `README.md` - If changing setup/deployment process

## Key Business Logic

### Reconciliation Formula
```python
expected_balance = (
    starting_balance
    + total_income
    - total_expenses
    - total_installment_payments
    - total_investment_transfers
    - net_suspended_transactions
    ± currency_conversion_adjustments
)

difference = expected_balance - actual_balance
# Must be 0 to finalize period
```

### Multi-Currency Rules
- Calculate reconciliation separately per currency
- All currencies must individually balance to 0
- Currency conversions affect both source and target currency pools

### Suspended Transaction States
- `PENDING` → `SETTLED` (money returned)
- `PENDING` → `CONVERTED_TO_EXPENSE` (decided to keep)
- Auto-carry forward PENDING items to next period

### Installment Tracking
- `remaining_balance = total_price - SUM(payments)`
- Auto-update status to `PAID_OFF` when `remaining_balance <= 0`
- Allow flexible payment amounts (not just fixed monthly)

## References

- **PRD**: `docs/PRD.md`
- **Database Schema**: `docs/DATABASE_SCHEMA.md`
- **Project Structure**: `docs/PROJECT_STRUCTURE.md`
- **Git Workflow**: `GIT_WORKFLOW.md`
- **Code Quality**: `CODE_QUALITY.md`
- **Security**: `SECURITY.md`
- **Quickstart**: `QUICKSTART.md`

***
