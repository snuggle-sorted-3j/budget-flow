Perfect! I'll regenerate `PRD.md` in the correct pure markdown format (like your existing files).

**📄 COPY INSTRUCTIONS:** 
- Copy everything starting from the line "# BudgetFlow - Product Requirements Document (PRD)" below
- Stop copying at "END OF PRD.md"
- Paste into a new file named `PRD.md`
- All markdown formatting, tables, and code blocks will render correctly

---

# BudgetFlow - Product Requirements Document (PRD)

**Version:** 1.0  
**Last Updated:** November 9, 2025  
**Project Name:** BudgetFlow  
**Repository Name:** budget-flow  
**Status:** Approved for Development

***

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Core Features](#2-core-features)
3. [Reconciliation Logic](#3-reconciliation-logic-core-feature)
4. [User Interface](#4-user-interface-plotly-dash)
5. [Data Validation & Business Rules](#5-data-validation--business-rules)
6. [Initial Setup Wizard](#6-initial-setup-wizard)
7. [Technical Requirements](#7-technical-requirements)
8. [Deployment Architecture](#8-deployment-architecture)
9. [Development Phases](#9-development-phases-cursor-implementation)
10. [Success Metrics](#10-success-metrics)
11. [Future Enhancements](#11-future-enhancements-post-phase-3)
12. [Documentation Deliverables](#12-documentation-deliverables)
13. [Design Decisions](#13-design-decisions-confirmed)
14. [Risk Assessment](#14-risk-assessment)
15. [Appendices](#15-appendices)

***

## 1. Executive Summary

### 1.1 Project Overview

**BudgetFlow** is a comprehensive personal finance tracking and reconciliation system designed for **paycheck-based calculation periods** with multi-currency support, investment tracking, and sophisticated expense categorization. Built with FastAPI (backend), PostgreSQL (database), and Plotly Dash (frontend), containerized with Docker for local development and AWS deployment.

**Project Names:**
- **Display Name:** BudgetFlow
- **Repository:** budget-flow
- **Database:** budget_flow

### 1.2 Core Philosophy

**Reconciliation-first approach**: Users enter actual bank balances at period end, system identifies discrepancies, and users balance with "Untracked Expenses" category—mirroring professional accounting practices.

### 1.3 Target Users

- **Primary**: Individuals tracking personal finances on paycheck cycles (not calendar months)
- **Secondary**: B2B contractors/freelancers needing tax-deductible expense tracking (Polish/European model)
- **Tertiary**: Multi-currency users (frequent travelers, international contractors)

### 1.4 Success Criteria

- User completes first period setup in <10 minutes
- Zero-sum balance verification forces data accuracy (difference = 0)
- Auto-save all inputs to prevent data loss
- Support 100+ calculation periods with <200ms query times
- Phase 1 deployment to AWS within 7 weeks

***

## 2. Core Features

### 2.1 User Authentication & Multi-User Support

#### 2.1.1 Authentication Requirements

- **JWT-based authentication** with bcrypt password hashing
- Email/password registration and login
- Secure session management with token refresh
- **Phase 1**: Single-user per instance (multi-tenancy in Phase 2)

#### 2.1.2 User Settings

```python
USER_SETTINGS:
- user_id (PK)
- default_currency_id (FK to CURRENCIES)
- tax_system (ENUM: "POLISH_B2B", "US_ANNUAL", "NONE")
- tax_rate (DECIMAL - e.g., 19% for Polish B2B)
- preferred_date_format (VARCHAR)
- timezone (VARCHAR)
```

### 2.2 Calculation Periods (Core Abstraction)

#### 2.2.1 Flexible Period Definition

**User-controlled dates** (not fixed monthly intervals):

- **Start Date**: Day after previous period's snapshot date
- **End Date/Snapshot Date**: User-specified (typically day before salary payment)
- **Period Name**: User-defined (e.g., "February 2025", "Nov 5 - Dec 4")
- **Duration**: Automatically calculated (can be 28-35 days, weekly, bi-weekly, etc.)

**Example:**
```
Salary paid: November 5th
Snapshot date: November 4th (balance checked on this day)
Period: October 5 - November 4 (31 days)
```

#### 2.2.2 Period States

```python
CALCULATION_PERIOD_STATUS:
- DRAFT: Period created, data entry in progress
- FINALIZED: Balanced (difference = 0), locked for editing
- ARCHIVED: Historical record, read-only
```

**Business Rules:**
- Cannot create overlapping periods (validation warning)
- Cannot finalize unless reconciliation difference = 0
- Finalized periods can be "unfrozen" for corrections

#### 2.2.3 Period Data Structure

```python
CALCULATION_PERIODS:
├── id (UUID, PK)
├── user_id (FK to USERS)
├── period_name (VARCHAR - "November 2025")
├── start_date (DATE - auto-calculated or user-override)
├── end_date (DATE - same as snapshot_date)
├── snapshot_date (DATE - user enters balances for this day)
├── status (ENUM - DRAFT, FINALIZED, ARCHIVED)
├── finalized_at (TIMESTAMP, nullable)
├── created_at (TIMESTAMP)
├── updated_at (TIMESTAMP)
```

### 2.3 Account Management

#### 2.3.1 Bank Accounts & Cash

**Multiple accounts in multiple currencies**:
- Unlimited bank accounts (Millennium Bank PLN, PKO Bank PLN, Revolut EUR)
- Cash accounts per currency
- Account activation/deactivation (soft-delete pattern)

```python
ACCOUNTS:
├── id (UUID, PK)
├── user_id (FK)
├── account_name (VARCHAR - "Millennium Bank PLN")
├── account_type (ENUM - "BANK", "CASH")
├── currency_id (FK to CURRENCIES)
├── is_active (BOOLEAN, default True)
├── created_at (TIMESTAMP)
├── updated_at (TIMESTAMP)

BALANCE_SNAPSHOTS:
├── id (UUID, PK)
├── calculation_period_id (FK)
├── account_id (FK)
├── balance (DECIMAL(15,2))
├── snapshot_date (DATE - must match period.snapshot_date)
├── created_at (TIMESTAMP)
```

**Business Rules:**
- Account names must include currency for clarity
- Soft-delete: `is_active=False` instead of deletion (preserves history)
- Balance snapshots immutable once period finalized

#### 2.3.2 Multi-Currency Support

**User-defined currencies** (not hardcoded enum):

```python
CURRENCIES:
├── id (UUID, PK)
├── ticker (VARCHAR - "PLN", "EUR", "USD", "BTC", "GBP")
├── name (VARCHAR - "Polish Zloty", "Euro")
├── is_default (BOOLEAN - one per user)
├── user_id (FK)
├── created_at (TIMESTAMP)
```

**System pre-populates**: PLN, EUR, USD, GBP on first setup. User can add any ticker (crypto, commodities, etc.).

### 2.4 Income Tracking

#### 2.4.1 Income Entry

```python
INCOME_ENTRIES:
├── id (UUID, PK)
├── calculation_period_id (FK)
├── source_name (VARCHAR - "Salary", "Freelance", "Gift")
├── amount (DECIMAL(15,2))
├── currency_id (FK)
├── income_date (DATE, optional - for tracking when received)
├── tax_applicable (BOOLEAN, default False)
├── notes (TEXT)
├── created_at (TIMESTAMP)
├── updated_at (TIMESTAMP)
```

**Features:**
- Multi-currency income (e.g., freelance in EUR, salary in PLN)
- Template reuse from previous periods
- Recurring income detection (suggests auto-add for next period)

#### 2.4.2 Income Templates

Users can save common income patterns:

```python
INCOME_TEMPLATES:
├── id (UUID, PK)
├── user_id (FK)
├── template_name (VARCHAR)
├── income_entries_json (JSONB - list of income source patterns)
├── is_default (BOOLEAN)
├── created_at (TIMESTAMP)
```

### 2.5 Expense Management

#### 2.5.1 Hierarchical Category System

**Two-level hierarchy**: Category > Sub-items

```python
EXPENSE_CATEGORIES:
├── id (UUID, PK)
├── user_id (FK)
├── category_name (VARCHAR - "Food", "Housing", "Transport")
├── parent_category_id (FK, nullable - NULL for top-level)
├── is_system_category (BOOLEAN - cannot delete if True)
├── icon (VARCHAR, optional - emoji or icon name)
├── sort_order (INT - for UI display)
├── is_active (BOOLEAN, default True)
├── created_at (TIMESTAMP)
├── updated_at (TIMESTAMP)
```

**Default Categories** (system-created on first setup):

1. **General Life Expenses**
   - Mobile network payment
   - Bank fees
   - Subscriptions
   - Flowers
   - Barber
   - Other

2. **Food**
   - Groceries
   - Dining out
   - Other

3. **Housing**
   - Apartment rent
   - Storage rent
   - Internet
   - Other

4. **Entertainment**
   - Cinema
   - Music practice room
   - Other

5. **Car & Transportation**
   - Fuel
   - Public transport
   - Car wash
   - Other

6. **Other Expenses**
   - (User-defined sub-items)

7. **⚖️ Untracked Expenses** *(System category)*
   - For reconciliation adjustments
   - **Cannot be deleted**
   - Prominently displayed in summary

**Business Rules:**
- Users can add custom categories/sub-items
- Users can customize default categories before first use
- System category "Untracked Expenses" auto-created

#### 2.5.2 Expense Items

```python
EXPENSE_ITEMS:
├── id (UUID, PK)
├── calculation_period_id (FK)
├── category_id (FK to EXPENSE_CATEGORIES)
├── item_name (VARCHAR - "Groceries - Biedronka")
├── amount (DECIMAL(15,2))
├── currency_id (FK)
├── expense_date (DATE, optional)
├── expense_type (ENUM - "REGULAR", "INSTALLMENT_PAYMENT")
├── is_tax_deductible (BOOLEAN, default False)
├── tax_category (VARCHAR, nullable - "Business", "Medical")
├── notes (TEXT)
├── created_at (TIMESTAMP)
├── updated_at (TIMESTAMP)
```

**Custom Expense Types** (user-extensible):

```python
CUSTOM_EXPENSE_TYPES:
├── id (UUID, PK)
├── user_id (FK)
├── type_name (VARCHAR - "Reimbursable", "Business", "Gift")
├── description (TEXT)
├── is_active (BOOLEAN)
```

#### 2.5.3 Tax-Deductible Expenses (B2B/Contract)

**Polish B2B Model** (monthly tax benefit calculation):

- Mark expenses as business/tax-deductible
- System calculates **monthly tax savings** (not annual)
- Shows "Real Cost" = Expense - Immediate Tax Benefit

**Example:**
```
Laptop Purchase: 3,500 PLN
Tax Deductible: ✓ (19% rate)
Tax Benefit This Month: 665 PLN
Real Cost: 2,835 PLN
```

**Monthly Summary:**
```
Gross Income: 10,000 PLN
- Tax-Deductible Costs: 3,500 PLN
─────────────────────────
Taxable Income: 6,500 PLN
Tax (19%): 1,235 PLN

💰 Tax Savings: 665 PLN
Net After Tax: 8,765 PLN
```

### 2.6 Suspended Transactions

#### 2.6.1 Concept

**Money temporarily out of circulation:**
- Money lent to friends (expecting return)
- Online purchases pending return/refund
- Security deposits (expecting refund)

**Lifecycle:**
1. **New Suspended** (created this period)
2. **Old Suspended** (carried over from previous periods)
3. **Settled** (money returned) or **Converted to Expense** (decided to keep)

#### 2.6.2 Data Structure

```python
SUSPENDED_EXPENSES:
├── id (UUID, PK)
├── user_id (FK)
├── item_name (VARCHAR - "Money lent to John")
├── amount (DECIMAL(15,2))
├── currency_id (FK)
├── transaction_type (ENUM - "LOAN_OUT", "PURCHASE_RETURN", "OTHER")
├── status (ENUM - "PENDING", "SETTLED", "CONVERTED_TO_EXPENSE")
├── created_period_id (FK - period where created)
├── settled_period_id (FK, nullable - period where resolved)
├── notes (TEXT)
├── created_at (TIMESTAMP)
├── updated_at (TIMESTAMP)
```

#### 2.6.3 User Actions

**Three options per suspended item:**

1. **💰 Settle - Money Returned**
   - Adds amount back to income for current period
   - Status → `SETTLED`
   - Records `settled_period_id`
   - **Tooltip**: "Money has been returned to you (loan repaid, refund received)"

2. **✓ Convert to Expense - Decided to Keep**
   - Creates new entry in `EXPENSE_ITEMS`
   - User selects expense category
   - Status → `CONVERTED_TO_EXPENSE`
   - Original suspended record preserved for audit
   - **Tooltip**: "You decided to keep the item/not get money back"

3. **⏸️ Keep Suspended - Still Pending**
   - Automatically carries forward to next period
   - Appears in "Old Suspended" section
   - No user action required (default)
   - **Tooltip**: "Transaction still pending - will appear in next period"

### 2.7 Installment Tracking

#### 2.7.1 Concept

**Items purchased with payment plans** (gaming console, laptop, etc.):
- Record total price and payment schedule
- Track remaining balance
- Record monthly payments

#### 2.7.2 Data Structure

```python
INSTALLMENT_ITEMS:
├── id (UUID, PK)
├── user_id (FK)
├── item_name (VARCHAR - "Gaming Console")
├── total_price (DECIMAL(15,2))
├── currency_id (FK)
├── initial_period_id (FK - when purchased)
├── remaining_balance (DECIMAL(15,2) - computed)
├── monthly_payment_amount (DECIMAL(15,2), optional)
├── months_to_pay (INT, optional)
├── status (ENUM - "ACTIVE", "PAID_OFF")
├── notes (TEXT)
├── created_at (TIMESTAMP)
├── updated_at (TIMESTAMP)

INSTALLMENT_PAYMENTS:
├── id (UUID, PK)
├── installment_item_id (FK)
├── calculation_period_id (FK)
├── payment_amount (DECIMAL(15,2))
├── payment_date (DATE)
├── notes (TEXT)
├── created_at (TIMESTAMP)
```

**Business Logic:**
```python
remaining_balance = total_price - SUM(payments.payment_amount)
if remaining_balance <= 0:
    status = "PAID_OFF"
```

**Monthly Payment Flexibility:**
- User can pay fixed amount or custom amount
- User can pay extra to finish early
- System tracks remaining balance dynamically

### 2.8 Currency Conversions

#### 2.8.1 Concept

**Moving money between currency pools**:
- Exchange 1000 PLN → 200 EUR (rate 5.0)
- **PLN pool**: -1000
- **EUR pool**: +200
- No "gain/loss" calculation—just movement

#### 2.8.2 Data Structure

```python
CURRENCY_CONVERSIONS:
├── id (UUID, PK)
├── calculation_period_id (FK)
├── from_currency_id (FK)
├── to_currency_id (FK)
├── from_amount (DECIMAL(15,2))
├── to_amount (DECIMAL(15,2))
├── rate (DECIMAL(10,6) - computed or user-entered)
├── conversion_date (DATE)
├── source_account_id (FK, optional - which account)
├── notes (TEXT - "Bank fee included", etc.)
├── created_at (TIMESTAMP)
```

**Rate Calculation:**
```python
# User can:
# 1. Enter from/to amounts → system calculates rate
rate = to_amount / from_amount

# 2. Enter rate manually → system validates amounts
```

### 2.9 Investment Tracking

#### 2.9.1 Concept

**Long-term money allocation** outside daily finances:
- Stocks, crypto, gold, real estate
- Track cumulative investments by category
- Track which broker/account holds investments

#### 2.9.2 Data Structure

```python
INVESTMENT_ACCOUNTS:
├── id (UUID, PK)
├── user_id (FK)
├── account_name (VARCHAR - "Interactive Brokers", "Coinbase")
├── account_type (ENUM - "BROKERAGE", "CRYPTO_EXCHANGE", "PHYSICAL")
├── notes (TEXT - account number, login info)
├── is_active (BOOLEAN)
├── created_at (TIMESTAMP)

INVESTMENTS:
├── id (UUID, PK)
├── user_id (FK)
├── category_name (VARCHAR - "Stocks", "Crypto", "Gold")
├── investment_account_id (FK, nullable)
├── opening_balance (DECIMAL(15,2), nullable - for initial setup)
├── opening_balance_date (DATE, nullable)
├── opening_balance_currency_id (FK, nullable)
├── created_at (TIMESTAMP)

INVESTMENT_TRANSFERS:
├── id (UUID, PK)
├── investment_id (FK)
├── calculation_period_id (FK)
├── amount_transferred (DECIMAL(15,2))
├── currency_id (FK)
├── source_account_id (FK - which bank account funded this)
├── transfer_date (DATE)
├── is_opening_balance (BOOLEAN - marks initial setup)
├── notes (TEXT - "Bought Apple shares", etc.)
├── created_at (TIMESTAMP)
```

**Dashboard Display:**
```
Total Crypto Investment (Coinbase):
Opening (June 2024): 5,000 PLN
+ Jan 2025 transfer: 500 PLN
+ Feb 2025 transfer: 300 PLN
─────────────────────────────
Total: 5,800 PLN
```

### 2.10 Templates System

#### 2.10.1 User Templates

**Save common patterns** for reuse:
- Default expense categories
- Common income sources
- Typical investment categories

```python
TEMPLATES:
├── id (UUID, PK)
├── user_id (FK)
├── template_name (VARCHAR - "My Default Monthly Template")
├── template_type (ENUM - "EXPENSE_CATEGORIES", "INCOME_SOURCES", "FULL")
├── template_data (JSONB - flexible structure)
├── is_default (BOOLEAN - one default per user)
├── created_at (TIMESTAMP)
├── updated_at (TIMESTAMP)
```

**Template Reuse Workflow:**
1. User creates first period, customizes categories
2. User clicks "Save as Template" (in Tab 3 or Settings)
3. Next period: "Reuse template?" → Pre-populates categories
4. User adds amounts, makes adjustments

**Template Data Example** (JSONB):
```json
{
  "expense_categories": [
    {"name": "Food", "sub_items": ["Groceries", "Dining Out"]},
    {"name": "Housing", "sub_items": ["Rent", "Internet"]}
  ],
  "income_sources": ["Salary", "Freelance"],
  "investment_categories": ["Crypto", "Stocks"]
}
```

***

## 3. Reconciliation Logic (Core Feature)

### 3.1 Zero-Sum Principle

**Every calculation period must balance**:

```
Starting Total Balance 
+ Total Income 
- Total Regular Expenses 
- Total Installment Payments 
- Total Investment Transfers 
- Net Suspended Transactions (new + old)
± Currency Conversion Adjustments
─────────────────────────────
= Expected Ending Balance

Expected Ending Balance = Actual Bank Balances (user-entered)
Difference = Expected - Actual
```

**If Difference ≠ 0**: User must reconcile by adding to "Untracked Expenses" category.

### 3.2 Multi-Currency Reconciliation

**Calculate separately per currency**:

```python
# Example: User has PLN and EUR accounts
for currency in user_currencies:
    starting_balance = get_starting_balance(currency)
    income = sum_income(currency)
    expenses = sum_expenses(currency)
    transfers_out = sum_currency_conversions_from(currency)
    transfers_in = sum_currency_conversions_to(currency)
    
    expected = starting_balance + income - expenses - transfers_out + transfers_in
    actual = sum_account_balances(currency, snapshot_date)
    
    difference[currency] = expected - actual
```

**All currencies must individually balance to 0**.

### 3.3 Reconciliation UI Flow (Tab 8)

**Step 1: User Enters Actual Balances**
```
Snapshot Date: November 4, 2025

Enter bank balances for this day:
┌────────────────────────────────────────┐
│ Millennium Bank PLN: [ 1,245.67 ]     │
│ PKO Bank PLN:        [ 2,103.50 ]     │
│ Cash PLN:            [   832.00 ]     │
│ Revolut EUR:         [   145.30 ]     │
└────────────────────────────────────────┘
```

**Step 2: System Calculates Expected Balance**
```
Expected PLN Balance:
  Starting: 3,800.00
  + Income: 5,000.00
  - Expenses: 4,200.00
  - Installments: 200.00
  - Investments: 500.00
  = 3,900.00 PLN expected
```

**Step 3: Show Discrepancy**
```
┌─────────────────────────────────────────────────────────┐
│ ⚠️ RECONCILIATION STATUS - PLN                          │
│                                                          │
│ Expected PLN: 3,900.00                                  │
│ Actual PLN:   4,181.17                                  │
│ ─────────────────────────────────────                   │
│ Difference:   +281.17 PLN ❌                            │
│                                                          │
│ 💡 What this means:                                     │
│ You have 281.17 PLN MORE than recorded.                 │
│                                                          │
│ Possible reasons:                                       │
│ • Forgot to record an income source                     │
│ • Over-recorded an expense                              │
│ • Found extra cash                                      │
│                                                          │
│ [Add Income] [Review Expenses] [Add Balancing Expense] │
└─────────────────────────────────────────────────────────┘
```

**If negative difference:**
```
┌─────────────────────────────────────────────────────────┐
│ Difference:   -281.17 PLN ❌                            │
│                                                          │
│ 💡 What this means:                                     │
│ You have 281.17 PLN LESS than recorded.                 │
│                                                          │
│ Possible reasons:                                       │
│ • Small cash purchases without receipts                 │
│ • ATM withdrawals spent but not tracked                 │
│ • Forgot to log some expenses                           │
│                                                          │
│ ✅ Action: Add untracked expenses to balance           │
│ [Add to "Untracked Expenses"] [Review Expenses]        │
└─────────────────────────────────────────────────────────┘
```

**Step 4: User Adds Balancing Expense**
```
Add to "Untracked Expenses":
┌────────────────────────────────────────┐
│ Amount: [ 281.17 ] PLN                 │
│ Notes: [Small cash purchases, lost     │
│         receipts, ATM withdrawals]     │
│ [Add to Expenses]                      │
└────────────────────────────────────────┘

After adding:
✅ Difference: 0.00 PLN ✓
[✅ Finalize Period] ← Now enabled
```

**Finalize Button Logic:**
```python
if all(difference[currency] == 0 for currency in user_currencies):
    enable_finalize_button()
else:
    disable_finalize_button()
    show_tooltip("All currencies must balance to 0")
```

***

## 4. User Interface (Plotly Dash)

### 4.1 Application Layout

**Navigation Structure:**
```
├── Header (App Title + User Info)
├── Sidebar Navigation
│   ├── New Calculation Period
│   ├── View Previous Periods
│   └── Settings
│
└── Main Content Area (Tabbed Interface)
    ├── Tab 1: Period Setup
    ├── Tab 2: Income Entry
    ├── Tab 3: Expense Entry (with sub-tabs per category)
    ├── Tab 4: Suspended Transactions
    ├── Tab 5: Installments
    ├── Tab 6: Currency Conversions
    ├── Tab 7: Investments
    ├── Tab 8: Reconciliation & Summary
    ├── Tab 9: Dashboards & Trends
    └── Tab 10: Settings & Templates
```

### 4.2 Key Tab Features

#### Tab 1: Period Setup
Initialize new calculation period with snapshot date and period name.

#### Tab 2: Income Entry
Record income for period with template reuse option.

#### Tab 3: Expense Entry
Record expenses organized by category with "Save as Template" button.

#### Tab 4: Suspended Transactions
Track pending transactions (loans, returns) with three action buttons per item.

#### Tab 5: Installments
Track payment plans with flexible payment amounts.

#### Tab 6: Currency Conversions
Record currency exchanges with auto-calculated or manual rates.

#### Tab 7: Investments
Track investment transfers to brokerage/crypto accounts.

#### Tab 8: Reconciliation & Summary
**Core feature**: User enters actual balances, system calculates difference, finalize when balanced.

#### Tab 9: Dashboards & Trends
**Phase 1**: Static charts (income/expenses, category breakdown, trends)  
**Phase 2**: Interactive filters and drill-downs

#### Tab 10: Settings & Templates
Manage currencies, templates, investment accounts, and export data.

### 4.3 Auto-Save Implementation

**Every field auto-saves after 500ms debounce:**

```python
@app.callback(
    Output('save-status', 'children'),
    Input('amount-input', 'value'),
    prevent_initial_call=True
)
def auto_save_amount(amount):
    time.sleep(0.5)  # Debounce
    update_database(current_item_id, {'amount': amount})
    return "✓ Saved 2s ago"
```

**Visual Feedback:**
```
Amount: [250.50] ✓ Saved 2s ago
```

### 4.4 Help System

**Question mark icons with hover tooltips:**
- Transaction types (Loan Out, Purchase Return)
- Suspended action buttons
- Currency conversion logic
- Installment payment options
- Tax-deductible expense benefits

***

## 5. Data Validation & Business Rules

### 5.1 Period Validation
- Snapshot date must be after previous period's snapshot date
- Period name required (suggest default based on dates)
- Warn if periods overlap (allow with confirmation)

### 5.2 Account Validation
- Account name must include currency for clarity
- Cannot delete account with existing balance snapshots
- Soft-delete only (`is_active=False`)

### 5.3 Expense Validation
- Amount must be positive
- Category required
- Currency required
- System categories cannot be deleted ("Untracked Expenses")

### 5.4 Suspended Transaction Validation
- Cannot settle for more than original amount
- Cannot convert to expense twice
- Status transitions enforced (PENDING → SETTLED or CONVERTED)

### 5.5 Installment Validation
- Payment amount cannot exceed remaining balance
- Remaining balance auto-calculated
- Status auto-updated to "PAID_OFF" when remaining = 0

### 5.6 Currency Conversion Validation
- From and to currencies must differ
- Rate must be positive
- If from_amount and to_amount provided, rate must match

### 5.7 Reconciliation Validation
- All currencies must balance to 0 before finalizing
- Cannot finalize with discrepancies
- Finalized periods are read-only (can unfinalize with warning)

### 5.8 Database Constraints

```sql
-- PostgreSQL constraints to enforce data integrity
ALTER TABLE balance_snapshots
  ADD CONSTRAINT unique_account_period
  UNIQUE (account_id, calculation_period_id);

ALTER TABLE calculation_periods
  ADD CONSTRAINT valid_date_range
  CHECK (end_date >= start_date);

ALTER TABLE expense_items
  ADD CONSTRAINT positive_amount
  CHECK (amount >= 0);

ALTER TABLE currencies
  ADD CONSTRAINT unique_ticker_per_user
  UNIQUE (user_id, ticker);
```

***

## 6. Initial Setup Wizard

**First-time user onboarding (5-10 minutes):**

### Step 1: Welcome & Default Currency
Select primary currency (PLN, EUR, USD, etc.)

### Step 2: Bank Accounts
Add bank accounts and cash with current balances.

### Step 3: Additional Currencies
Select or add custom currencies.

### Step 4: Expense Categories
Customize pre-populated default categories or use as-is.

### Step 5: Existing Investments (Optional)
Record current investment holdings with opening balances.

### Step 6: Active Installments (Optional)
Add items being paid in installments with remaining balances.

### Step 7: First Period
Create first calculation period with snapshot date.

***

## 7. Technical Requirements

### 7.1 Technology Stack

**Backend:**
- FastAPI 0.104+ (async Python web framework)
- SQLAlchemy 2.0+ (ORM)
- Alembic (database migrations)
- PostgreSQL 15+ (database)
- Pydantic v2 (validation)
- Python 3.11+ (type hints, performance)

**Frontend:**
- Plotly Dash 2.14+ (Python-based dashboard framework)
- Dash Bootstrap Components (UI styling)
- Plotly 5.17+ (charts and visualizations)

**DevOps:**
- Docker & Docker Compose (containerization)
- AWS (deployment target - free tier)
  - EC2 or ECS Fargate (compute)
  - RDS PostgreSQL (database)
  - ECR (Docker image registry)
- GitHub Actions (CI/CD)

**Testing:**
- pytest 7.4+ (unit and integration tests)
- pytest-cov (coverage reporting)
- Great Expectations (data validation)

**Code Quality:**
- Black (formatting)
- Flake8 (linting)
- Mypy (type checking)
- Bandit (security scanning)
- Pre-commit hooks

### 7.2 Performance Requirements

| Metric | Target |
|--------|--------|
| Simple queries | <100ms |
| Period creation | <200ms |
| Reconciliation calculation | <500ms |
| Dashboard rendering | <1s |
| Scalability | 100+ periods, 10,000+ expenses |

**Database Indexes** (PostgreSQL):
```sql
CREATE INDEX idx_expense_items_period ON expense_items(calculation_period_id);
CREATE INDEX idx_expense_items_category ON expense_items(category_id);
CREATE INDEX idx_balance_snapshots_period ON balance_snapshots(calculation_period_id);
CREATE INDEX idx_suspended_status ON suspended_expenses(status, created_period_id);
CREATE INDEX idx_investment_transfers_period ON investment_transfers(calculation_period_id);
CREATE INDEX idx_periods_user_date ON calculation_periods(user_id, snapshot_date);
```

### 7.3 Security Requirements

**Authentication:**
- JWT tokens with 24h expiration
- Refresh token mechanism
- Password hashing with bcrypt (cost factor 12)
- HTTPS enforced in production

**API Security:**
- Rate limiting (100 requests/minute per user)
- CORS configured for frontend domain only
- SQL injection prevention (parameterized queries)
- Input validation with Pydantic

**Data Protection:**
- Environment variables for secrets
- `.env` file in `.gitignore`
- Database backups (daily snapshots in AWS)

**Security Scanning:**
- Bandit on every commit
- Dependency vulnerability checks (Safety)
- Pre-commit hooks enforce security checks

### 7.4 Testing Requirements

**Coverage Targets:**
- Unit tests: >80% coverage
- Integration tests: Critical paths covered
- E2E tests: Key user workflows

**Test Categories:**

1. **Unit Tests** (`tests/unit/`)
   - Business logic functions
   - Validation logic
   - Calculation functions

2. **Integration Tests** (`tests/integration/`)
   - Database schema validation
   - Foreign key relationships
   - Query performance (<100ms benchmarks)
   - Data integrity constraints

3. **API Tests** (`tests/api/`)
   - FastAPI endpoint tests
   - Authentication flows
   - Error handling

4. **Data Validation Tests** (`tests/validation/`)
   - Great Expectations suite
   - Balance reconciliation accuracy
   - Multi-currency calculations

**Test Execution:**
```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=app --cov-report=html

# Specific category
pytest tests/integration/test_reconciliation.py -v
```

**CI/CD Integration** (GitHub Actions):
- Run on every push to `main`/`develop`
- Test on Python 3.11, 3.12
- Coverage uploaded to Codecov

***

## 8. Deployment Architecture

### 8.1 Local Development (Docker Compose)

```yaml
# docker-compose.yml
version: '3.8'
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: budget_flow
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:${DB_PASSWORD}@postgres:5432/budget_flow
      JWT_SECRET: ${JWT_SECRET}
    depends_on:
      - postgres

  frontend:
    build: ./frontend
    ports:
      - "8050:8050"
    environment:
      API_URL: http://backend:8000
    depends_on:
      - backend

volumes:
  postgres_data:
```

**Development Workflow:**
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Run migrations
docker-compose exec backend alembic upgrade head

# Run tests
docker-compose exec backend pytest tests/ -v

# Stop services
docker-compose down
```

### 8.2 AWS Deployment (Free Tier)

**Target Architecture:**
```
User Browser
    ↓
AWS Route 53 (DNS)
    ↓
AWS ALB (Load Balancer)
    ↓
├── ECS Fargate (Dash Frontend)
└── ECS Fargate (FastAPI Backend)
        ↓
    AWS RDS PostgreSQL (Free Tier)
        ↓
    AWS S3 (Backups, Exports)
```

**AWS Resources (Free Tier):**
- EC2 t2.micro or t3.micro (750 hours/month free)
- RDS PostgreSQL db.t3.micro (750 hours/month free, 20GB storage)
- ECR (500MB storage free)
- S3 (5GB storage free)
- CloudWatch (Basic monitoring free)

**Cost Estimate** (within free tier for first 12 months):
- Compute: $0 (t2.micro free tier)
- Database: $0 (db.t3.micro free tier)
- Storage: $0 (within 20GB free tier)
- **Total**: ~$0/month for 12 months, then ~$15-20/month

### 8.3 Database Migrations (Alembic)

**Migration Workflow:**
```bash
# Generate migration after model changes
alembic revision --autogenerate -m "add investment accounts table"

# Review generated migration
cat alembic/versions/xxxx_add_investment_accounts.py

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

**Migration Best Practices:**
- Never edit applied migrations
- Test migrations on staging first
- Always add downgrade logic
- Back up database before major migrations

---

## 9. Development Phases (Cursor Implementation)

### Phase 1: Core Accounting (Weeks 1-2)

**Features:**
- User authentication (JWT)
- Account management (CRUD)
- Currency management
- Calculation period creation
- Income entries
- Expense categories and items
- Balance snapshots
- Basic reconciliation logic

**Deliverables:**
- Working API endpoints
- Database migrations
- Unit tests (>80% coverage)
- Docker Compose setup
- Basic Dash UI (Tabs 1-3)

**Success Criteria:**
- User can create period, add income/expenses, enter balances
- Reconciliation difference calculated correctly
- All tests pass

### Phase 2: Advanced Features (Weeks 3-4)

**Features:**
- Suspended transactions (all 3 actions)
- Installment tracking
- Currency conversions
- Investment tracking with accounts
- Templates system
- Tax-deductible expenses (Polish B2B)

**Deliverables:**
- Complete API endpoints
- Dash UI Tabs 4-7
- Integration tests
- Reconciliation UI (Tab 8)

**Success Criteria:**
- Full workflow testable end-to-end
- All business logic validated with tests

### Phase 3: Polish & Deployment (Weeks 5-7)

**Features:**
- Dashboards and trends (Tab 9 - static charts)
- Settings and template management (Tab 10)
- Initial setup wizard
- Export to CSV
- Pre-commit hooks and CI/CD
- AWS deployment

**Deliverables:**
- Production-ready application
- Comprehensive documentation
- CI/CD pipeline
- Deployed to AWS

**Success Criteria:**
- App accessible via public URL
- All features working in production
- Performance benchmarks met

***

## 10. Success Metrics

### 10.1 User Success Metrics
- Setup completion rate: >90%
- Period finalization: >80%
- Template usage: >60%
- Multi-currency adoption: >30%

### 10.2 Technical Metrics
- Test coverage: >80%
- Query performance: 95% <100ms
- Uptime: >99%
- Error rate: <1%

### 10.3 Code Quality Metrics
- Linting: 0 errors
- Type coverage: >90%
- Security: 0 critical vulnerabilities
- Documentation: All functions documented

---

## 11. Future Enhancements (Post-Phase 3)

### 11.1 Automation
- Bank CSV import (semi-automation)
- Receipt OCR
- Recurring expense auto-detection

### 11.2 Advanced Analytics
- Budget goals (per category limits)
- Predictive trends
- Category insights
- Interactive dashboards (Phase 2 enhancement)

### 11.3 Multi-User
- Household mode (shared periods)
- Expense splitting
- Role-based access
- Real-time updates (WebSocket)

### 11.4 Integration
- Open Banking APIs
- Tax software export (Polish PIT, CIT formats)
- Mobile app

***

## 12. Documentation Deliverables

### 12.1 Technical Documentation
- Complete PRD (this document)
- Database schema with ERD
- API endpoint specifications (OpenAPI/Swagger)
- SQLAlchemy models
- Dash component architecture

### 12.2 Development Documentation
- `.cursorrules` file (Cursor AI instructions)
- `PROJECT_STRUCTURE.md` (folder organization)
- `PHASES.md` (detailed Cursor prompts)
- `QUICKSTART.md` (developer onboarding)

### 12.3 Quality Documentation
- `GIT_WORKFLOW.md` (commit conventions)
- `CODE_QUALITY.md` (testing, linting)
- `SECURITY.md` (security practices)
- `CI_CD_WORKFLOW.md` (automation)
- `SQL_TESTING_GUIDE.md` (database testing)

### 12.4 User Documentation
- User manual (after Phase 3)
- Setup wizard instructions
- FAQ and troubleshooting

***

## 13. Design Decisions (Confirmed)

### 13.1 Project Naming ✅

- **Repository/Folder**: `budget-flow`
- **Application Display**: `BudgetFlow`
- **Database**: `budget_flow`
- **Docker Containers**: `budget-flow-backend`, `budget-flow-frontend`

### 13.2 Dashboard Complexity ✅

**Decision**: Start with static charts (Phase 1), add interactivity in Phase 2.

**Rationale**: Faster development, meets core requirements. Interactive filters (date ranges, category selection) added in Phase 2 once core logic validated.

**Phase 1 Charts:**
- Income vs Expenses pie chart (static)
- Category breakdown bar chart (static)
- Trend line charts (last 6 periods, static)
- Key metrics cards

**Phase 2 Enhancements:**
- Date range selector
- Category multi-select filters
- Click-through to detailed views
- Drill-down capabilities

### 13.3 Dashboard Refresh Strategy ✅

**Decision**: Refresh on page load (Phase 1), add real-time in Phase 3.

**Rationale**: Simpler architecture, matches user workflow (periodic reviews, not continuous monitoring).

**Phase 1 Implementation:**
- Dashboard queries run when user navigates to Tab 9
- Manual refresh button available
- Auto-refresh every 5 minutes (optional setting)

**Phase 3 Enhancement:**
- WebSocket for real-time updates during multi-user sessions
- Push notifications for collaborative editing

---

## 14. Risk Assessment

### 14.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Multi-currency rounding errors | Medium | High | Use DECIMAL(15,2), comprehensive tests |
| Cursor context loss in large codebase | High | Medium | Phased development, reference docs |
| AWS free tier exceeded | Low | Medium | Monitor usage, set billing alerts |
| Database migration failures | Medium | High | Test migrations on staging, backups |
| Reconciliation logic bugs | Medium | Critical | Extensive unit tests, manual QA |

### 14.2 Development Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Scope creep | High | High | Strict phase boundaries, PRD as contract |
| Incomplete requirements | Medium | High | This PRD addresses comprehensively |
| Testing gaps | Medium | High | Follow test patterns from previous project |
| Deployment complexity | Medium | Medium | Docker standardization, detailed docs |

---

## 15. Appendices

### Appendix A: Glossary

- **Calculation Period**: Time span for financial tracking (typically paycheck to paycheck)
- **Snapshot Date**: Specific day when bank balances are checked
- **Reconciliation**: Process of matching expected vs actual balances
- **Zero-Sum**: Principle that all money must be accounted for (difference = 0)
- **Suspended Transaction**: Money temporarily out of circulation (loan, pending return)
- **Installment**: Payment plan for item purchased on credit
- **Untracked Expenses**: System category for balancing discrepancies
- **Finalization**: Locking period after balancing (difference = 0)

### Appendix B: Database Schema Summary

**Tables Count**: 18 core tables

**Key Relationships:**
- `CALCULATION_PERIODS` ← FK ← `INCOME_ENTRIES`, `EXPENSE_ITEMS`, etc.
- `USERS` ← FK ← All user-specific entities
- `CURRENCIES` ← FK ← All financial amount tables
- `EXPENSE_CATEGORIES` ← FK ← `EXPENSE_ITEMS`
- `ACCOUNTS` ← FK ← `BALANCE_SNAPSHOTS`

**Critical Indexes**: 10+ performance indexes

### Appendix C: API Endpoint Summary

| Category | Endpoints |
|----------|-----------|
| Authentication | POST `/register`, `/login`, `/refresh-token` |
| Periods | GET, POST, PUT `/periods`, POST `/periods/{id}/finalize` |
| Accounts | GET, POST, PUT, DELETE `/accounts` |
| Income | GET, POST, PUT, DELETE `/income` |
| Expenses | GET, POST, PUT, DELETE `/expenses` |
| Categories | GET, POST, PUT, DELETE `/categories` |
| Suspended | GET, POST `/suspended`, POST `/suspended/{id}/settle`, `/suspended/{id}/convert-to-expense` |
| Installments | GET, POST `/installments`, POST `/installments/{id}/payment` |
| Conversions | POST, GET `/conversions` |
| Investments | GET, POST `/investments/account`, POST `/investments/transfer` |
| Reconciliation | GET `/reconciliation/period/{id}/calculate`, POST `/reconciliation/period/{id}/finalize` |
| Templates | GET, POST, PUT, DELETE `/templates` |

### Appendix D: Environment Variables

```bash
# .env file (not in git)
DATABASE_URL=postgresql://postgres:password@localhost:5432/budget_flow
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
ENVIRONMENT=development  # or production
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
```

***

**END OF PRD.md**

**Document Status**: ✅ Complete and Approved  
**Version**: 1.0  
**Last Updated**: November 9, 2025  
**Next Document**: `DATABASE_SCHEMA.md`
