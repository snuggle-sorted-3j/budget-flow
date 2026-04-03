> **PARTIALLY OUTDATED** — Last updated 2026-01-04. Current test count is 151 across unit and integration suites. Module list below covers Phase 1-2 only; Phase 3 additions (tax_benefits, recon_ui_polish, template_period_flow, export, analytics, setup_wizard) are not reflected here.

# BudgetFlow Backend Testing Documentation

This document tracks the implemented tests for the BudgetFlow backend. The test suite is designed to ensure robust business logic, data integrity, and API reliability.

## 🚀 Running Tests

To run the full test suite with coverage within the Docker environment:

```bash
docker-compose exec backend pytest --cov=app tests/ -v
```

## 📊 Test Categories

### 1. System & Health
Ensures the API is alive and reports correct versioning/environment information.
- **File**: `tests/integration/test_endpoints.py`
- **Tests**:
  - `test_health_check`: Verifies `/health` returns 200 OK.
  - `test_version_check`: Verifies `/version` returns current app version and environment.

### 2. Authentication & Security
Verifies JWT token validation and scoped data access.
- **File**: `tests/integration/test_endpoints.py`
- **Tests**:
  - `test_unauthenticated_access`: Ensures protected routes return 401 Unauthorized without a valid token.
  - `test_token_fixture`: (Internal) Ensures the `test_token` fixture generates valid JWTs.

### 3. Calculation Periods
Validates the lifecycle of budgeting periods and date consistency.
- **Files**: `tests/unit/test_period_crud.py`, `tests/integration/test_endpoints.py`
- **Tests**:
  - `test_create_period`: CRUD level validation of period creation.
  - `test_create_period_api`: Verifies API endpoint for period creation.
  - `test_create_period_invalid_date`: **Data Integrity** - Ensures `snapshot_date` must equal `end_date`.
  - `test_update_period_status`: Verifies status transitions (DRAFT -> FINALIZED).

### 4. Accounts & Currencies
Covers account management and multi-currency support.
- **Files**: `tests/unit/test_account_snapshot_crud.py`, `tests/integration/test_endpoints.py`
- **Tests**:
  - `test_create_account`: Verifies account creation linked to a user and currency.
  - `test_account_currency_validation`: (Implemented in API) Ensures accounts cannot be linked to non-existent or unauthorized currencies.

### 5. Balance Snapshots
Ensures accurate recording of account balances at the end of a period.
- **Files**: `tests/unit/test_account_snapshot_crud.py`, `tests/integration/test_endpoints.py`
- **Tests**:
  - `test_upsert_snapshot`: **Critical Logic** - Verifies that posting a snapshot replaces an existing one for the same account/period (Upsert).
  - `test_list_snapshots_for_period`: Verifies bulk retrieval of snapshots.

### 6. Transactions (Incomes & Expenses)
Validates the core financial tracking logic and referential integrity.
- **File**: `tests/integration/test_transactions.py`
- **Tests**:
  - `test_create_income_success`: Verifies income creation with full metadata.
  - `test_create_expense_success`: Verifies expense creation linked to a category.
  - `test_create_income_invalid_currency`: **Validation** - Ensures currency existence check.
  - `test_create_expense_invalid_category`: **Validation** - Ensures category existence check.
  - `test_create_transaction_negative_amount`: **Schema Validation** - Prevents negative values via Pydantic.
  - `test_delete_income_success`: Verifies deletion and cascading visibility.
  - `test_delete_expense_success`: Verifies deletion.

### 7. Expense Categories
Hierarchical management and protection of system-critical data.
- **File**: `tests/integration/test_categories.py`
- **Tests**:
  - `test_initialize_categories`: Verifies the seeding of default system categories.
  - `test_create_hierarchical_category`: Verifies parent-child linking.
  - `test_cannot_delete_system_category`: **Security** - Ensures "Untracked Expenses" cannot be deleted.
  - `test_soft_delete_flow`: Verifies categories are hidden by default but retrievable via `include_inactive`.
  - `test_cannot_delete_category_with_expenses`: **Data Integrity** - Prevents deactivating a category that has active transactions.

### 8. Reconciliation
Critical logic for ensuring financial data balances across periods.
- **File**: `tests/integration/test_reconciliation.py`
- **Tests**:
  - `test_reconciliation_zero_start`: Verifies base-case reconciliation with no previous period.
  - `test_reconciliation_with_previous_period`: Verifies that `starting_balance` is correctly carried over from the preceding period's snapshots.
  - `test_finalize_fails_if_unbalanced`: **Safety Check** - Ensures a period cannot be finalized unless all currencies are balanced.

---
*Last Updated: 2026-01-04*
