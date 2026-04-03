> **OBSOLETE** — Tool-specific plan from February 2026; all tasks complete. Current test count: 151. See `TESTING.md` or run `pytest backend/tests/ -v`.

# RALPH_TEST_PLAN.md

> **Project**: BudgetFlow Testing Implementation
> **Style**: Ralph Loop / Antigravity Compatible
> **Last Updated**: 2026-02-01

---

## Overview

This document contains a **task-oriented test implementation plan** designed for incremental execution via Ralph Loop or Antigravity. Each task is:
- **Self-contained**: Can be completed in 1-3 iterations
- **Verifiable**: Has clear acceptance criteria
- **Progressive**: Builds on previous tasks

### Task Summary

| Task | Name | Priority | Estimated Effort |
|------|------|----------|------------------|
| 1 | Unit Tests: Reconciliation Service | 🔴 Critical | 2-3 iterations |
| 2 | Unit Tests: Income & Expense CRUD | 🟡 High | 1-2 iterations |
| 3 | Unit Tests: Account & Period CRUD | 🟡 High | 1 iteration |
| 4 | Unit Tests: Advanced Features | 🟢 Medium | 2 iterations |
| 5 | Integration Tests: Auth Flow | 🟡 High | 1 iteration |
| 6 | Integration Tests: Transaction Workflows | 🟡 High | 1-2 iterations |
| 7 | Integration Tests: Installments & Investments | 🟢 Medium | 2 iterations |
| 8 | Integration Tests: Templates & Conversions | 🟢 Medium | 1-2 iterations |
| 9 | E2E Tests: Multi-Currency Flow | 🟡 High | 1-2 iterations |
| 10 | E2E Tests: Auth Edge Cases | 🟢 Medium | 1 iteration |
| 11 | Test Infrastructure: Fixtures & Factories | 🟡 High | 1 iteration |
| 12 | CI/CD: GitHub Actions Pipeline | 🟡 High | 1 iteration |

---

## Task 1: Unit Tests for Reconciliation Service

**Priority**: 🔴 CRITICAL
**Estimated Effort**: 2-3 iterations

### Description
Create comprehensive unit tests for `app/services/reconciliation_service.py`, which contains the core financial calculation logic. This is the highest-risk module in the codebase.

### File to Create
`backend/tests/unit/test_reconciliation_service.py`

### Tests to Implement

```python
# Test cases to cover:
1. test_reconciliation_balanced_basic
   - Setup: income=1000, expense=200, snapshot=800
   - Assert: is_balanced=True, difference=0

2. test_reconciliation_unbalanced
   - Setup: income=1000, expense=200, snapshot=500
   - Assert: is_balanced=False, difference=300

3. test_reconciliation_first_period_uses_opening_balance
   - Setup: Account with opening_balance=500, no previous period
   - Assert: starting_balance=500

4. test_reconciliation_uses_previous_period_snapshot
   - Setup: Previous period with snapshot=5000
   - Assert: starting_balance=5000

5. test_reconciliation_with_investments
   - Setup: income=1000, investment_transfer=200, snapshot=800
   - Assert: expected_balance correctly subtracts transfers

6. test_reconciliation_with_installment_payments
   - Setup: income=1000, installment_payment=150, snapshot=850
   - Assert: Installments deducted from expected

7. test_reconciliation_suspended_out
   - Setup: Loan given (suspended_out=100)
   - Assert: Subtracts from expected

8. test_reconciliation_suspended_in
   - Setup: Loan repaid (suspended_in=100)
   - Assert: Adds to expected

9. test_reconciliation_currency_conversion_out
   - Setup: Convert 100 USD to EUR
   - Assert: USD expected reduced by 100

10. test_reconciliation_currency_conversion_in
    - Setup: Receive EUR from conversion
    - Assert: EUR expected increased

11. test_reconciliation_multi_currency
    - Setup: USD + EUR transactions
    - Assert: Each currency balanced independently

12. test_reconciliation_period_not_found
    - Setup: Invalid period_id
    - Assert: Returns None
```

### Acceptance Criteria
- [ ] All 12 test cases pass
- [ ] `pytest tests/unit/test_reconciliation_service.py -v` exits with 0
- [ ] Tests use mocked DB session where appropriate
- [ ] Edge cases covered (zero amounts, no transactions)

---

## Task 2: Unit Tests for Income & Expense CRUD

**Priority**: 🟡 HIGH
**Estimated Effort**: 1-2 iterations

### Description
Create unit tests for `app/crud/income.py` and `app/crud/expense.py` to validate CRUD operations.

### Files to Create
- `backend/tests/unit/test_income_crud.py`
- `backend/tests/unit/test_expense_crud.py`

### Tests to Implement

```python
# test_income_crud.py
1. test_create_income_success
2. test_create_income_with_optional_fields
3. test_list_incomes_by_period
4. test_list_incomes_empty_period
5. test_delete_income
6. test_update_income_amount

# test_expense_crud.py
1. test_create_expense_success
2. test_create_expense_with_category
3. test_list_expenses_by_period
4. test_list_expenses_filters_by_user
5. test_delete_expense
6. test_update_expense_category
```

### Acceptance Criteria
- [ ] All tests pass with `pytest tests/unit/test_income_crud.py tests/unit/test_expense_crud.py -v`
- [ ] Tests verify correct foreign key associations (period_id, currency_id)
- [ ] Deletion tests verify record is removed from DB

---

## Task 3: Unit Tests for Account & Period CRUD (Expand Existing)

**Priority**: 🟡 HIGH
**Estimated Effort**: 1 iteration

### Description
Expand existing tests in `test_period_crud.py` and `test_account_snapshot_crud.py` to cover edge cases.

### Tests to Add

```python
# test_period_crud.py (additions)
1. test_create_duplicate_period_name
2. test_finalize_already_finalized_period
3. test_delete_period (if supported)
4. test_period_date_validation

# test_account_snapshot_crud.py (additions)
1. test_snapshot_with_zero_balance
2. test_snapshot_update_replaces_existing
3. test_snapshot_for_inactive_account
```

### Acceptance Criteria
- [ ] Existing tests still pass
- [ ] New edge case tests added and passing
- [ ] `pytest tests/unit/ -v` shows 15+ tests

---

## Task 4: Unit Tests for Advanced Features

**Priority**: 🟢 MEDIUM
**Estimated Effort**: 2 iterations

### Description
Create unit tests for complex CRUD modules: installments, investments, suspended expenses, templates, and currency conversions.

### Files to Create
- `backend/tests/unit/test_installment_crud.py`
- `backend/tests/unit/test_investment_crud.py`
- `backend/tests/unit/test_suspended_expense_crud.py`
- `backend/tests/unit/test_template_crud.py`
- `backend/tests/unit/test_currency_conversion_crud.py`

### Tests per Module

```python
# test_installment_crud.py
1. test_create_installment_item
2. test_create_payment_updates_balance
3. test_paid_off_status_update
4. test_recalculate_after_delete_payment

# test_investment_crud.py
1. test_create_investment_account
2. test_create_investment_with_opening_balance
3. test_create_investment_transfer
4. test_list_transfers_by_period

# test_suspended_expense_crud.py
1. test_create_suspended_expense
2. test_update_status_to_settled
3. test_delete_suspended_expense

# test_template_crud.py
1. test_create_template_from_period
2. test_apply_template_creates_incomes
3. test_apply_template_creates_expenses
4. test_set_default_template

# test_currency_conversion_crud.py
1. test_create_conversion
2. test_list_by_period
3. test_update_conversion
4. test_delete_conversion
```

### Acceptance Criteria
- [ ] All 20+ tests pass
- [ ] Each module has at least 3-4 tests
- [ ] Complex logic (recalculate balance) has dedicated tests

---

## Task 5: Integration Tests for Auth Flow

**Priority**: 🟡 HIGH
**Estimated Effort**: 1 iteration

### Description
Create integration tests for authentication endpoints covering success and error cases.

### File to Create
`backend/tests/integration/test_auth_flow.py`

### Tests to Implement

```python
1. test_register_new_user
   - POST /api/v1/auth/register with valid data
   - Assert: 201, user created

2. test_register_duplicate_email
   - Register twice with same email
   - Assert: 400, appropriate error

3. test_login_success
   - POST /api/v1/auth/token with valid credentials
   - Assert: 200, returns access_token

4. test_login_invalid_password
   - POST /api/v1/auth/token with wrong password
   - Assert: 401

5. test_login_nonexistent_user
   - POST /api/v1/auth/token with unknown email
   - Assert: 401

6. test_protected_endpoint_valid_token
   - GET /api/v1/periods/ with valid Bearer token
   - Assert: 200

7. test_protected_endpoint_no_token
   - GET /api/v1/periods/ without token
   - Assert: 401

8. test_protected_endpoint_invalid_token
   - GET /api/v1/periods/ with malformed token
   - Assert: 401
```

### Acceptance Criteria
- [ ] All 8 tests pass
- [ ] Tests use TestClient and don't require running server
- [ ] Token handling verified end-to-end

---

## Task 6: Integration Tests for Transaction Workflows

**Priority**: 🟡 HIGH
**Estimated Effort**: 1-2 iterations

### Description
Enhance existing transaction tests and add new scenarios for complete workflow coverage.

### File to Update
`backend/tests/integration/test_transactions.py`

### Tests to Add

```python
# New tests to add:
1. test_update_income_amount
   - Create income, PATCH amount, verify change

2. test_update_expense_category
   - Create expense, change category, verify

3. test_transaction_date_validation
   - Add transaction outside period dates
   - Expected behavior (accept or reject?)

4. test_bulk_transaction_creation
   - Add multiple incomes/expenses in sequence
   - Verify all created
```

### Acceptance Criteria
- [ ] Existing tests still pass
- [ ] 4+ new tests added
- [ ] Update operations tested

---

## Task 7: Integration Tests for Installments & Investments

**Priority**: 🟢 MEDIUM
**Estimated Effort**: 2 iterations

### Description
Create integration tests for installment and investment API endpoints.

### Files to Create
- `backend/tests/integration/test_installment_flow.py`
- `backend/tests/integration/test_investment_flow.py`

### Tests to Implement

```python
# test_installment_flow.py
1. test_create_installment_item
2. test_add_payment_to_installment
3. test_payment_updates_remaining_balance
4. test_installment_paid_off_flow
5. test_installment_appears_in_reconciliation
6. test_delete_payment_recalculates

# test_investment_flow.py
1. test_create_investment_account
2. test_create_investment
3. test_create_transfer
4. test_transfer_appears_in_reconciliation
5. test_list_investments_by_user
```

### Acceptance Criteria
- [ ] All tests pass
- [ ] Full lifecycle tested (create → update → complete)
- [ ] Reconciliation integration verified

---

## Task 8: Integration Tests for Templates & Currency Conversions

**Priority**: 🟢 MEDIUM
**Estimated Effort**: 1-2 iterations

### Description
Create integration tests for template and currency conversion workflows.

### Files to Create
- `backend/tests/integration/test_template_flow.py`
- `backend/tests/integration/test_currency_conversion_flow.py`

### Tests to Implement

```python
# test_template_flow.py
1. test_create_template_from_period
2. test_apply_template_to_new_period
3. test_template_preserves_categories
4. test_list_templates
5. test_delete_template

# test_currency_conversion_flow.py
1. test_create_conversion
2. test_conversion_affects_both_currencies
3. test_list_conversions_by_period
4. test_update_conversion
5. test_delete_conversion
```

### Acceptance Criteria
- [ ] All tests pass
- [ ] Template apply creates correct entries
- [ ] Currency conversion math verified

---

## Task 9: E2E Test for Multi-Currency Flow

**Priority**: 🟡 HIGH
**Estimated Effort**: 1-2 iterations

### Description
Create a Playwright E2E test that exercises multi-currency functionality.

### File to Create
`tests/e2e/test_multi_currency_flow.py`

### Test Scenario

```python
def test_multi_currency_budget_flow(page: Page):
    """
    User Story:
    1. User registers and logs in
    2. User adds USD (default) and EUR currencies
    3. User creates an account in each currency
    4. User creates a period
    5. User adds income in USD
    6. User adds expense in EUR
    7. User adds currency conversion (USD → EUR)
    8. User enters snapshots for both accounts
    9. User verifies reconciliation shows both currencies balanced
    10. User finalizes period
    """
```

### Acceptance Criteria
- [ ] Test passes with `pytest tests/e2e/test_multi_currency_flow.py -v`
- [ ] Uses Playwright selectors matching existing IDs
- [ ] Runs in <60 seconds

---

## Task 10: E2E Test for Auth Edge Cases

**Priority**: 🟢 MEDIUM
**Estimated Effort**: 1 iteration

### Description
Create E2E tests for authentication edge cases visible to users.

### File to Create
`tests/e2e/test_auth_flow.py`

### Test Scenarios

```python
1. test_login_logout_flow()
   - Login → Navigate → Logout → Verify redirect to login

2. test_session_persistence()
   - Login → Close tab → Reopen → Verify still logged in (if using localStorage)

3. test_login_error_display()
   - Attempt login with wrong password
   - Verify error message displayed to user
```

### Acceptance Criteria
- [ ] All tests pass
- [ ] User-facing error messages verified
- [ ] Logout clears session properly

---

## Task 11: Test Infrastructure - Fixtures & Factories

**Priority**: 🟡 HIGH
**Estimated Effort**: 1 iteration

### Description
Create reusable test fixtures and data factories to reduce duplication.

### Files to Create
- `backend/tests/fixtures/__init__.py`
- `backend/tests/fixtures/factories.py`
- `backend/tests/fixtures/sample_data.py`

### Implementation

```python
# factories.py
class UserFactory:
    @staticmethod
    def create(**overrides) -> dict: ...

class PeriodFactory:
    @staticmethod
    def create(**overrides) -> dict: ...

class IncomeFactory:
    @staticmethod
    def create(**overrides) -> dict: ...

class ExpenseFactory:
    @staticmethod
    def create(**overrides) -> dict: ...

class InstallmentFactory:
    @staticmethod
    def create(**overrides) -> dict: ...

# sample_data.py
SAMPLE_CURRENCIES = [
    {"ticker": "USD", "name": "US Dollar"},
    {"ticker": "EUR", "name": "Euro"},
]

SAMPLE_CATEGORIES = [...]
```

### Acceptance Criteria
- [ ] Factories created for all major entities
- [ ] At least 2 existing tests refactored to use factories
- [ ] Import works: `from tests.fixtures.factories import PeriodFactory`

---

## Task 12: CI/CD - GitHub Actions Pipeline

**Priority**: 🟡 HIGH
**Estimated Effort**: 1 iteration

### Description
Set up GitHub Actions workflow to run tests automatically.

### File to Create
`.github/workflows/test.yml`

### Implementation

```yaml
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
          pip install pytest pytest-cov httpx
      
      - name: Run Tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/budget_flow_test
          JWT_SECRET: test-secret-key-1234567890
          ENVIRONMENT: testing
        run: |
          cd backend
          pytest tests/ -v --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: backend/coverage.xml
```

### Acceptance Criteria
- [ ] Workflow file created at `.github/workflows/test.yml`
- [ ] Push to any branch triggers workflow
- [ ] Tests run against PostgreSQL service
- [ ] Coverage report generated

---

## Progress Tracking

Use this section to track progress during Ralph Loop execution:

```
Task 1: [x] Completed (test_reconciliation_service.py created)
Task 2: [x] Completed (test_income_crud.py and test_expense_crud.py created)
Task 3: [x] Completed (Expanded test_period_crud.py / test_account_snapshot_crud.py)
Task 4: [x] Completed (5 new test modules created)
Task 5: [x] Completed (test_auth_flow.py created)
Task 6: [x] Completed (test_transactions.py updated with update/edge cases)
Task 7: [x] Completed (test_installment_flow.py and test_investment_flow.py created)
Task 8: [x] Completed (test_template_flow.py, test_suspended_expense_flow.py, test_currency_conversion_flow.py created)
Task 9: [x] Completed (test_multi_currency_flow.py created)
Task 10: [x] Completed (test_auth_edge_cases.py created)
Task 11: [x] Completed (factories.py and sample_data.py created)
Task 12: [x] Completed (.github/workflows/test.yml created)
```

---

## Recommended Execution Order

1. **Foundation** (Tasks 11, 3, 1): Fixtures, then expand existing unit tests, then critical reconciliation tests
2. **Core CRUD** (Tasks 2, 4): Income/expense and advanced feature unit tests
3. **Auth** (Tasks 5, 10): Auth integration and E2E
4. **Workflows** (Tasks 6, 7, 8): Transaction and feature integration tests
5. **E2E** (Task 9): Multi-currency flow
6. **CI/CD** (Task 12): Automation

---

## Notes for Ralph Loop Execution

- Update `progress.txt` after each task completion
- Run `pytest` after each task to verify no regressions
- If a test fails, debug before proceeding to next task
- Commit after each completed task with message: `test: complete Task N - <description>`
