# Test Strategy & Quality Assurance Implementation Plan

> **Project**: BudgetFlow
> **Author**: QA Lead / Test Strategist
> **Date**: 2026-02-01

---

## Executive Summary

This document provides a comprehensive testing strategy for BudgetFlow, a personal finance management application with a FastAPI backend and Dash frontend. The strategy follows the **testing pyramid** principle: many fast unit tests at the base, fewer integration tests in the middle, and a small set of high-value E2E tests at the top.

---

## 1. System Architecture Analysis

### Backend Architecture
```mermaid
graph TD
    subgraph "API Layer"
        A[FastAPI Router] --> B[Endpoints]
    end
    
    subgraph "Business Logic"
        B --> C[CRUD Modules]
        B --> D[Services]
    end
    
    subgraph "Data Layer"
        C --> E[SQLAlchemy Models]
        D --> E
        E --> F[(PostgreSQL)]
    end
    
    subgraph "Core"
        G[Auth/Security]
        H[Config]
    end
```

### Key Components Identified

| Layer | Modules | Risk Level |
|-------|---------|------------|
| **API Endpoints** | 14 routers (accounts, auth, currencies, expenses, incomes, periods, reconciliation, investments, installments, suspended_expenses, templates, currency_conversions, balance_snapshots, system) | High |
| **CRUD Operations** | 13 modules with DB operations | High |
| **Services** | `reconciliation_service.py` (complex financial calculations) | Critical |
| **Models** | 18 SQLAlchemy models with relationships | Medium |
| **Schemas** | 14 Pydantic validation schemas | Medium |
| **Frontend** | Dash app with 14 tabs, callbacks, and utilities | Medium |

---

## 2. Current Test Coverage Assessment

| Test Type | Files | Tests | Coverage |
|-----------|-------|-------|----------|
| **Unit** | 2 | ~7 | Low (~5%) |
| **Integration** | 4 | ~15 | Moderate (~25%) |
| **E2E** | 1 | 1 | Minimal (1 flow) |

### Gaps Identified

> [!WARNING]
> **Critical gaps requiring immediate attention:**
> - No unit tests for `reconciliation_service.py` (core financial logic)
> - No tests for installments, investments, suspended expenses, templates
> - No tests for currency conversions
> - No negative/edge case tests for most CRUD operations
> - No authentication edge case tests (token expiry, invalid tokens)

---

## 3. Test Strategy Design

### 3.1 Testing Pyramid Distribution

```
          ╱╲
         ╱  ╲       E2E: 3-5 tests (5%)
        ╱────╲      - Full user journeys
       ╱      ╲     - Browser-based (Playwright)
      ╱────────╲    
     ╱          ╲   Integration: 20-30 tests (25%)
    ╱────────────╲  - API + DB workflows
   ╱              ╲ - Multi-component scenarios
  ╱────────────────╲
 ╱                  ╲ Unit: 50-80 tests (70%)
╱────────────────────╲- Isolated functions
                       - Edge cases & validation
```

### 3.2 Test Scope

#### In Scope ✅
- All CRUD operations (create, read, update, delete)
- Business logic in services (reconciliation calculations)
- API endpoint request/response validation
- Authentication and authorization flows
- Data validation (Pydantic schemas)
- Database model relationships and constraints
- Critical user journeys (E2E)

#### Out of Scope ❌ (Non-Goals)
- Visual regression testing for frontend
- Performance/load testing (not needed at current scale)
- Third-party library internals
- Database migration testing (Alembic handles this)

---

## 4. Proposed Test Directory Structure

```
backend/
└── tests/
    ├── conftest.py                    # Shared fixtures (existing, enhanced)
    ├── unit/
    │   ├── __init__.py
    │   ├── test_period_crud.py        # ✓ Exists
    │   ├── test_account_snapshot_crud.py # ✓ Exists
    │   ├── test_reconciliation_service.py # NEW - Critical
    │   ├── test_income_crud.py        # NEW
    │   ├── test_expense_crud.py       # NEW
    │   ├── test_installment_crud.py   # NEW
    │   ├── test_investment_crud.py    # NEW
    │   ├── test_suspended_expense_crud.py # NEW
    │   ├── test_template_crud.py      # NEW
    │   ├── test_currency_conversion_crud.py # NEW
    │   └── test_security.py           # NEW - Auth utilities
    ├── integration/
    │   ├── __init__.py
    │   ├── test_endpoints.py          # ✓ Exists
    │   ├── test_transactions.py       # ✓ Exists
    │   ├── test_categories.py         # ✓ Exists
    │   ├── test_reconciliation.py     # ✓ Exists
    │   ├── test_auth_flow.py          # NEW
    │   ├── test_installment_flow.py   # NEW
    │   ├── test_investment_flow.py    # NEW
    │   ├── test_suspended_expense_flow.py # NEW
    │   ├── test_template_flow.py      # NEW
    │   └── test_currency_conversion_flow.py # NEW
    └── fixtures/
        ├── __init__.py
        ├── sample_data.py             # NEW - Test data factories
        └── factories.py               # NEW - Object factories

tests/
└── e2e/
    ├── conftest.py                    # Playwright fixtures
    ├── test_budget_flow.py            # ✓ Exists (happy path)
    ├── test_auth_flow.py              # NEW - Login/logout edge cases
    └── test_multi_currency_flow.py    # NEW - Multi-currency scenario
```

---

## 5. Detailed Test Specifications

### 5.1 Unit Tests (Priority: HIGH)

#### Critical: `test_reconciliation_service.py`

| Test Case | Description | Inputs | Expected Output |
|-----------|-------------|--------|-----------------|
| `test_reconciliation_balanced` | Basic balanced period | income=1000, expense=200, snapshot=800 | `is_balanced=True`, `difference=0` |
| `test_reconciliation_unbalanced` | Mismatched snapshot | income=1000, expense=200, snapshot=500 | `is_balanced=False`, `difference=300` |
| `test_reconciliation_with_investments` | Include investment transfers | +investment transfer | Correctly subtracts from expected |
| `test_reconciliation_with_installments` | Include installment payments | +installment payment | Correctly subtracts from expected |
| `test_reconciliation_suspended_in_out` | Suspended expense flows | susp_out + susp_in | Net effect calculated correctly |
| `test_reconciliation_currency_conversion` | Conversion in/out | from_usd + to_eur | Both currencies balanced |
| `test_reconciliation_multi_currency` | Multiple currencies | 3 currencies | Each currency balanced separately |
| `test_reconciliation_first_period` | No previous period | opening_balance | Uses account opening balance |
| `test_reconciliation_chained_periods` | Previous period exists | prev_snapshot=5000 | starting_balance=5000 |

#### `test_income_crud.py` & `test_expense_crud.py`

| Test Case | Description |
|-----------|-------------|
| `test_create_valid` | Successfully creates entry |
| `test_create_with_notes` | Optional notes field |
| `test_list_by_period` | Filters by period |
| `test_delete_success` | Removes entry |
| `test_update_amount` | Updates amount value |
| `test_zero_amount_rejected` | Validation error for 0 |
| `test_negative_amount_rejected` | Validation error for negative |

#### `test_installment_crud.py`

| Test Case | Description |
|-----------|-------------|
| `test_create_installment_item` | Creates with correct initial balance |
| `test_create_payment` | Payment created, balance updated |
| `test_payment_reduces_balance` | remaining_balance decreases |
| `test_paid_off_status` | Status changes when balance=0 |
| `test_overpayment_capped` | Balance cannot go negative |
| `test_delete_payment_restores_balance` | Balance recalculated on delete |

#### `test_template_crud.py`

| Test Case | Description |
|-----------|-------------|
| `test_create_from_period` | Captures incomes and expenses |
| `test_apply_to_period` | Creates entries in target period |
| `test_set_default` | Only one default at a time |
| `test_delete_template` | Removes template |

### 5.2 Integration Tests (Priority: MEDIUM-HIGH)

#### `test_auth_flow.py`

| Test Case | Description |
|-----------|-------------|
| `test_register_new_user` | Registration success |
| `test_register_duplicate_email` | 400 error |
| `test_login_success` | Returns valid JWT |
| `test_login_wrong_password` | 401 error |
| `test_protected_endpoint_without_token` | 401 error |
| `test_protected_endpoint_expired_token` | 401 error |
| `test_protected_endpoint_malformed_token` | 401 error |

#### `test_installment_flow.py`

| Test Case | Description |
|-----------|-------------|
| `test_full_installment_lifecycle` | Create item → Add payments → Mark paid |
| `test_installment_affects_reconciliation` | Payment shows in reconciliation |
| `test_installment_across_periods` | Multi-period payments |

#### `test_investment_flow.py`

| Test Case | Description |
|-----------|-------------|
| `test_create_investment_account` | Account creation |
| `test_create_investment` | Investment category creation |
| `test_create_transfer` | Transfer from account |
| `test_transfer_affects_reconciliation` | Shows in reconciliation |

#### `test_template_flow.py`

| Test Case | Description |
|-----------|-------------|
| `test_create_template_from_period` | Template captures data |
| `test_apply_template_creates_entries` | Entries created in new period |
| `test_template_preserves_categories` | Category IDs preserved |

### 5.3 E2E Tests (Priority: HIGH for Critical Path)

> [!IMPORTANT]
> E2E tests are expensive to run. Limit to 3-5 critical user journeys.

| Test | Description | User Story |
|------|-------------|------------|
| `test_full_budget_flow` | ✓ Exists | Register → Login → Setup → Add transactions → Reconcile → Finalize |
| `test_auth_flow` | NEW | Login → Session expiry → Re-login |
| `test_multi_currency_flow` | NEW | Add USD + EUR currencies → Add mixed transactions → Reconcile both |
| `test_installment_journey` | Optional | Create installment → Multiple payments → Complete |

---

## 6. Mocking & Stubbing Strategy

### When to Use Real DB (Integration Tests)
- Testing CRUD operations
- Testing API endpoint behavior
- Testing data relationships

### When to Mock/Stub (Unit Tests)
- **Database sessions**: Use `unittest.mock.Mock()` for `Session`
- **External services**: If added later (e.g., email, notifications)
- **Time-dependent functions**: Use `freezegun` for date-based logic

```python
# Example: Mocking DB session for unit tests
from unittest.mock import MagicMock, patch

def test_reconciliation_calculation():
    mock_db = MagicMock(spec=Session)
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_period
    
    result = calculate_reconciliation(mock_db, user_id, period_id)
    assert result.overall_balanced == True
```

---

## 7. CI/CD Recommendation

> [!IMPORTANT]
> **Recommendation: Set up CI/CD NOW**

### Justification

| Factor | Assessment | Recommendation |
|--------|------------|----------------|
| **Project Complexity** | Medium-High (14 endpoints, financial calculations) | CI needed |
| **Risk Level** | High (financial data, reconciliation logic) | CI critical |
| **Change Velocity** | Active development with Antigravity/Ralph Loop | CI improves feedback |
| **Team Size** | Solo/small team | CI provides safety net |
| **Test Suite Size** | Growing (will be 80+ tests) | Automated runs essential |

### Proposed GitHub Actions Pipeline

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: budget_flow_test
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
          pip install pytest pytest-cov httpx
      
      - name: Run Unit Tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/budget_flow_test
          JWT_SECRET: test-secret-key-1234567890
          ENVIRONMENT: testing
        run: |
          cd backend
          pytest tests/unit -v --cov=app --cov-report=xml
      
      - name: Run Integration Tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/budget_flow_test
          JWT_SECRET: test-secret-key-1234567890
          ENVIRONMENT: testing
        run: |
          cd backend
          pytest tests/integration -v

  e2e:
    runs-on: ubuntu-latest
    needs: test  # Only run E2E if unit/integration pass
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Start services
        run: docker-compose up -d
      
      - name: Install Playwright
        run: |
          pip install pytest-playwright pytest
          playwright install chromium
      
      - name: Wait for services
        run: sleep 30
      
      - name: Run E2E Tests
        run: pytest tests/e2e -v
      
      - name: Stop services
        run: docker-compose down
```

### Alternative: Local pytest Workflow (If CI Deferred)

If you choose to defer CI setup, use this workflow:

```bash
# Run frequently during development
pytest backend/tests/unit -v --tb=short

# Run before commits
pytest backend/tests/unit backend/tests/integration -v

# Run before major releases
docker-compose up -d
pytest tests/e2e -v --headed
docker-compose down
```

---

## 8. Test Data Strategy

### Fixtures Approach
- **Use pytest fixtures** for reusable test data
- **Transaction rollback** per test (already implemented in `conftest.py`)
- **Factory pattern** for complex object creation

### Sample Data Factories

```python
# backend/tests/fixtures/factories.py
import uuid
from decimal import Decimal
from datetime import date

class PeriodFactory:
    @staticmethod
    def create(name="Test Period", start_date=None, end_date=None):
        start_date = start_date or date(2026, 1, 1)
        end_date = end_date or date(2026, 1, 31)
        return {
            "period_name": name,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "snapshot_date": str(end_date)
        }

class IncomeFactory:
    @staticmethod
    def create(source="Test Income", amount=1000, currency_id=None):
        return {
            "source_name": source,
            "amount": amount,
            "currency_id": str(currency_id) if currency_id else None
        }
```

---

## 9. Coverage Targets

| Test Type | Current | Target (Phase 1) | Target (Phase 2) |
|-----------|---------|------------------|------------------|
| Unit | ~5% | 50% | 70% |
| Integration | ~25% | 60% | 80% |
| E2E | 1 flow | 3 flows | 5 flows |

### Coverage Focus Areas (Priority Order)

1. **Critical**: `reconciliation_service.py` (100% coverage)
2. **High**: All CRUD modules (80% coverage)
3. **Medium**: API endpoints (validation, error handling)
4. **Lower**: Schemas (Pydantic handles most validation)

---

## 10. Test Execution Commands

```bash
# All tests
cd backend && pytest

# Unit tests only (fast, run frequently)
pytest tests/unit -v

# Integration tests (requires DB)
pytest tests/integration -v

# Specific module
pytest tests/unit/test_reconciliation_service.py -v

# With coverage
pytest --cov=app --cov-report=html tests/

# E2E tests (requires docker-compose up)
pytest ../tests/e2e -v --headed

# Parallel execution (faster)
pytest -n auto tests/
```

---

## User Review Required

> [!IMPORTANT]
> Please confirm the following before proceeding to implementation:
> 1. **CI/CD**: Do you want to set up GitHub Actions now, or defer?
> 2. **E2E Scope**: Are 3-5 E2E tests sufficient, or do you need more coverage?
> 3. **Priority**: Should we start with reconciliation service tests (critical path) or complete coverage of simpler CRUD modules first?

---

## Next Steps

After approval, proceed to `RALPH_TEST_PLAN.md` for task-by-task implementation.
