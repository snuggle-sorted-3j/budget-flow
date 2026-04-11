# BudgetFlow User Guide

**Version:** 1.0  
**Last Updated:** 2026-04-11  
**Purpose:** Complete guide for BudgetFlow users — explains every module, available options, typical use cases, and user journey paths.

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Dashboard Overview](#2-dashboard-overview)
3. [Periods](#3-periods)
4. [Income](#4-income)
5. [Expenses](#5-expenses)
6. [Reconciliation](#6-reconciliation)
7. [Accounts](#7-accounts)
8. [Currencies](#8-currencies)
9. [Expense Categories](#9-expense-categories)
10. [Investments](#10-investments)
11. [Suspended Transactions](#11-suspended-transactions)
12. [Installments](#12-installments)
13. [Currency Conversions](#13-currency-conversions)
14. [Templates](#14-templates)
15. [Advanced Analytics](#15-advanced-analytics)
16. [Settings](#16-settings)
17. [User Journey Paths](#17-user-journey-paths)
18. [FAQ & Tips](#18-faq--tips)

---

## 1. Getting Started

### What is BudgetFlow?

BudgetFlow is a personal finance tracking and reconciliation system. It helps you:

- **Track income and expenses** across multiple currencies
- **Reconcile your accounts** — compare what you expected to have vs what you actually have
- **Detect untracked spending** — find where money went that you didn't record
- **Track investments, installments, and loans** alongside regular spending
- **Analyze spending patterns** with dashboards, charts, and anomaly detection

### Core Concept: Period-Based Budgeting

BudgetFlow organizes your finances into **calculation periods** (typically monthly). Each period contains:

- Your income entries
- Your expense entries
- Balance snapshots (actual bank balances at period end)
- A reconciliation check (does everything add up?)

The goal each period: **enter your transactions, snapshot your actual balances, and verify they match.**

### First-Time Setup

1. **Register** — Create your account with email and password
2. **Set up currencies** — Default world currencies are pre-initialized; add custom ones (crypto, etc.) if needed
3. **Create accounts** — Add your bank accounts and cash wallets with opening balances
4. **Create expense categories** — System categories are pre-loaded; customize as needed
5. **Configure settings** — Set default currency, tax system (if applicable), timezone
6. **Create your first period** — Set name, start date, and end date
7. **Start tracking** — Add income and expenses throughout the period

---

## 2. Dashboard Overview

**Navigation:** Home / Dashboard (default page after login)

The Dashboard is your financial summary at a glance. It displays analytics for the **currently selected period** (chosen from the global period selector in the top navigation bar).

### Available Widgets

| Widget | What It Shows |
|--------|--------------|
| **Quick Stats Bar** | Key metrics: total income, total expenses, net balance, savings rate |
| **Income vs Expenses Trend** | Line/bar chart comparing income and expenses over the last 6 periods |
| **Spending Breakdown** | Pie chart showing expense distribution by category |
| **Largest Expenses** | Table of biggest individual expense items this period |
| **Net Worth Over Time** | Line chart tracking total account balances across periods |
| **Category Spending Trend** | Line chart for a specific category (selectable via dropdown) |
| **Period Comparison** | Side-by-side comparison of two periods |

### Actions

- **Refresh Data** — Manual refresh button to reload all dashboard data
- **Category Selector** — Dropdown to choose which category to track in the trend chart
- **Period Selector** — Global dropdown in the header to switch between periods

### Typical Use

Open the dashboard to get a quick health check of your finances. Use the spending breakdown to spot categories consuming too much. Compare periods to track improvement.

---

## 3. Periods

**Navigation:** Sidebar → Periods

Periods are the foundation of BudgetFlow. Each period represents a time range (usually one month) during which you track all financial activity.

### Create a New Period

| Field | Required | Description |
|-------|----------|-------------|
| Period Name | Yes | Descriptive name (e.g., "April 2026", "Q2 2026") |
| Start Date | Yes | First day of the period |
| End Date | Yes | Last day of the period (also used as snapshot date) |
| Apply Template | No | Checkbox to pre-fill period with a saved template |
| Template Selector | Conditional | Dropdown to choose which template to apply |

### Period Lifecycle

```
CREATE (DRAFT) → Add income/expenses → Take snapshots → Reconcile → FINALIZE
```

| Status | What You Can Do |
|--------|----------------|
| **DRAFT** | Add, edit, delete income/expenses/snapshots. Full editing capability. |
| **FINALIZED** | Read-only. No changes allowed. Represents a verified, closed period. |

### Available Actions

- **Create Period** — Start a new tracking period
- **View Periods** — Table showing all your periods with status
- **Delete Period** — Permanently removes period and ALL associated data (income, expenses, snapshots, reconciliation). Requires confirmation.

### Tips

- Use consistent naming (e.g., "2026-04 April") for easy sorting
- Apply a template when creating a period to auto-populate recurring income sources and expense categories
- Don't finalize until you've verified all transactions are entered and the period is balanced

---

## 4. Income

**Navigation:** Sidebar → Income

Track all money coming in during the selected period.

### Add Income Entry

| Field | Required | Description |
|-------|----------|-------------|
| Source Name | Yes | Name of income source (e.g., "Salary", "Freelance Project", "Dividend") |
| Amount | Yes | Income amount (decimal, e.g., 5000.00) |
| Currency | Yes | Currency dropdown |
| Income Date | No | Date income was received |
| Notes | No | Additional details |
| Tax Applicable | No | Check if this income is taxable (used in tax benefits calculation) |
| Recurring Income | No | Check if this is a regular income (e.g., monthly salary) — used for pattern detection |

### Available Actions

- **Add Income** — Create a new income entry
- **View Income** — Table of all income entries for the current period
- **Delete Income** — Remove an entry (confirmation required)

### Live Reconciliation Summary

Above the form, a reconciliation summary shows the current state: how much income is recorded, total expenses, and the current balance difference. This updates as you add/remove entries.

### Typical Use Cases

- **Monthly salary**: Add once per period, mark as recurring and tax-applicable
- **Freelance payments**: Add each payment separately with notes
- **Investment dividends**: Add with specific date and tax-applicable flag
- **Gift/windfall**: One-time income, not marked as recurring

---

## 5. Expenses

**Navigation:** Sidebar → Expenses

Track all money going out during the selected period.

### Add Expense Entry

| Field | Required | Description |
|-------|----------|-------------|
| Category | Yes | Expense category (dropdown, with "Manage" link to categories page) |
| Item Name | Yes | Description (e.g., "Weekly Groceries", "Netflix", "Rent") |
| Amount | Yes | Expense amount (decimal) |
| Currency | Yes | Currency dropdown |
| Expense Date | No | Date of the expense |
| Notes | No | Additional details |
| Recurring Expense | No | Check if this repeats monthly (e.g., rent, subscriptions) — used for pattern detection |

### Available Actions

- **Add Expense** — Create a new expense entry
- **View Expenses** — Table of all expenses for the current period
- **Delete Expense** — Remove an entry (confirmation required)

### Live Reconciliation Summary

Same as Income tab — shows running balance difference as you add expenses.

### Typical Use Cases

- **Fixed costs**: Rent, utilities, subscriptions — mark as recurring
- **Variable costs**: Groceries, dining out, entertainment
- **One-time purchases**: Electronics, gifts, travel
- **Tax-deductible expenses**: Business costs (if B2B tax system is active)

---

## 6. Reconciliation

**Navigation:** Sidebar → Reconciliation

This is the **core feature** of BudgetFlow. Reconciliation verifies that your recorded transactions match your actual bank balances.

### The 3-Step Workflow

#### Step 1: Balance Snapshots

Enter your **actual bank/wallet balances** as of the period's snapshot date (end date).

| Column | Description |
|--------|-------------|
| Account Name | Your bank account or cash wallet |
| Currency | Account's currency |
| Actual Balance | The real balance you see in your bank/wallet right now |

Click **Save Snapshots** to record all balances.

#### Step 2: Reconciliation Summary

After saving snapshots, the system calculates the reconciliation for each currency:

```
Expected Balance = Starting Balance + Income - Expenses
                   - Investment Transfers - Suspended Expenses (out)
                   + Settled Suspended (in) - Installment Payments
                   - Currency Conversions (out) + Currency Conversions (in)

Difference = Expected Balance - Actual Balance
```

| Result | Meaning |
|--------|---------|
| **Difference = 0** | Balanced. Everything adds up. |
| **Difference > 0** | You expected more than you have. Untracked expenses exist. |
| **Difference < 0** | You have more than expected. Untracked income exists. |

**Quick-Balance**: If the difference is positive (untracked expenses), a shortcut button creates an "Untracked Expenses" entry to close the gap automatically. This is useful when you can't identify where the money went.

#### Step 3: Finalize Period

Once all currencies show **Balanced (difference = 0)**:

1. Review tax benefits (if tax system is configured)
2. Click **Finalize Period**
3. Confirm in the modal (warning: finalization is permanent)

After finalization, the period becomes read-only. No income, expenses, or snapshots can be modified.

### Reconciliation Formula Breakdown

| Component | Effect on Expected Balance |
|-----------|---------------------------|
| Starting Balance | + (previous period's snapshot, or opening balance) |
| Total Income | + |
| Total Expenses | − |
| Investment Transfers | − (money moved to investment accounts) |
| Suspended Expenses Out | − (money loaned out or pending return) |
| Settled Suspended In | + (money returned from suspended) |
| Installment Payments | − (payments on installment plans) |
| Currency Conversions Out | − (money converted from this currency) |
| Currency Conversions In | + (money converted into this currency) |

### Typical Use

1. At the end of each month, log into each bank account and note the balance
2. Enter those balances in Step 1
3. Review the summary in Step 2
4. If unbalanced, either find missing transactions or use Quick-Balance
5. Finalize in Step 3

---

## 7. Accounts

**Navigation:** Sidebar → Accounts

Accounts represent your real-world bank accounts and cash wallets. They are **global** (not period-specific).

### Add Account

| Field | Required | Description |
|-------|----------|-------------|
| Account Name | Yes | Descriptive name (e.g., "Chase Checking", "Cash Wallet") |
| Type | Yes | **Bank Account** or **Cash / Wallet** |
| Currency | Yes | The currency this account holds |
| Opening Balance | No | Balance at the time you start using BudgetFlow |
| Opening Date | No | Date of the opening balance |

### Account Types

| Type | Use For |
|------|---------|
| **Bank Account** | Traditional bank accounts, savings accounts, credit unions |
| **Cash / Wallet** | Physical cash, petty cash, cash envelopes |

### Available Actions

- **Add Account** — Create a new account
- **View Accounts** — Table of all accounts
- **Delete Account** — Permanently removes account (confirmation required; affects balance snapshots)

### Tips

- Create one account per real bank account you want to track
- Set accurate opening balances — they're the starting point for your first period's reconciliation
- Each account is tied to one currency. If you have a multi-currency bank account, create separate accounts per currency.

---

## 8. Currencies

**Navigation:** Sidebar → Currencies

Manage the currencies available in your BudgetFlow instance. Major world currencies are pre-initialized automatically.

### Add Custom Currency

| Field | Required | Description |
|-------|----------|-------------|
| Ticker | Yes | Short code (e.g., "BTC", "ETH", "USDT") |
| Name | Yes | Full name (e.g., "Bitcoin", "Ethereum") |
| Default? | No | Set as your default currency |

### Pre-Initialized Currencies

Common currencies (USD, EUR, GBP, PLN, etc.) are created when you first initialize. You only need to add custom ones for:

- Cryptocurrencies (BTC, ETH, SOL, etc.)
- Stablecoins (USDT, USDC)
- Loyalty points or other custom units

### Tips

- Set your most-used currency as default — it will be pre-selected in forms
- You can have one default currency at a time

---

## 9. Expense Categories

**Navigation:** Sidebar → Categories

Organize your expenses into meaningful categories. System categories are pre-loaded; you can add custom ones.

### Add Category

| Field | Required | Description |
|-------|----------|-------------|
| Category Name | Yes | Name (e.g., "Groceries", "Rent", "Subscriptions") |
| Parent Category | No | Optional parent for hierarchy (e.g., "Food" → "Groceries", "Dining Out") |
| Icon | No | Emoji icon for visual identification |

### System Categories

Pre-loaded categories include: Food, Transportation, Utilities, Housing, Healthcare, Entertainment, Subscriptions, and **Untracked Expenses** (system category used by Quick-Balance).

### Hierarchy Support

Categories can be nested:
```
Food & Dining (parent)
├── Groceries (child)
├── Restaurants (child)
└── Coffee Shops (child)
```

### Tips

- Keep categories broad enough to be useful but specific enough for analysis
- Use the hierarchy for detailed tracking without cluttering the main category list
- The "Untracked Expenses" system category is reserved — don't delete it

---

## 10. Investments

**Navigation:** Sidebar → Investments

Track investment portfolio activity separately from regular expenses. Investments are partially global (accounts and categories) and partially period-specific (transfers).

### Three Sections

#### 1. Investment Accounts

Where your investments are held.

| Field | Required | Description |
|-------|----------|-------------|
| Account Name | Yes | Name (e.g., "Interactive Brokers", "Coinbase", "Home Safe") |
| Type | Yes | **Brokerage**, **Crypto Exchange**, or **Physical Wallet/Safe** |
| Notes | No | Additional details |

#### 2. Investment Categories (Holdings)

What you're invested in.

| Field | Required | Description |
|-------|----------|-------------|
| Category Name | Yes | Asset name (e.g., "S&P 500 ETF", "Bitcoin", "Gold Coins") |
| Account | Yes | Which investment account holds this |
| Opening Balance | No | Starting value |
| Currency | No | Currency of the holding |
| Date | No | Date of opening balance |

#### 3. Transfers to Investments (Period-Specific)

Money moved from bank accounts to investments during the current period.

| Field | Required | Description |
|-------|----------|-------------|
| Investment Category | Yes | Which holding you're buying into |
| Amount / Cost | Yes | How much money you're transferring |
| Units Purchased | No | Number of units (shares, coins, etc.) |
| Currency | Yes | Currency of the transfer |
| Source Account | Yes | Bank account the money comes from |
| Transfer Date | No | Date of transfer |
| Notes | No | Additional details |

### How Investments Affect Reconciliation

Investment transfers are **deducted** from your expected balance. When you move $1,000 from your bank to a brokerage, your bank balance drops by $1,000 — the reconciliation accounts for this so it doesn't show as "untracked spending."

### Typical Use Cases

- **Monthly stock purchases**: Record DCA (dollar-cost averaging) transfers
- **Crypto buys**: Track exchange purchases with unit counts
- **Physical gold**: Track purchases stored in a safe

---

## 11. Suspended Transactions

**Navigation:** Sidebar → Suspended Transactions

Track money that is **temporarily out of circulation** — loaned to someone, pending a refund, or otherwise unavailable.

### Add Suspended Transaction

| Field | Required | Description |
|-------|----------|-------------|
| Item Name | Yes | Description (e.g., "Loan to John", "Amazon Return Pending") |
| Amount | Yes | Amount suspended |
| Currency | Yes | Currency |
| Type | Yes | **Loan Out**, **Purchase Return Pending**, or **Other** |
| Notes | No | Additional details |

### Transaction Types

| Type | When to Use |
|------|------------|
| **Loan Out** | You lent money to someone |
| **Purchase Return Pending** | You returned a product and are waiting for a refund |
| **Other** | Any other temporary removal of money from circulation |

### Lifecycle

```
CREATE (PENDING) → Either:
  ├── SETTLE (money returned)
  └── CONVERT TO EXPENSE (money is gone)
```

#### Settling a Transaction

When the money comes back:
1. Click **Settle** on the pending transaction
2. Select the period in which the money was returned
3. Confirm

The amount is added back to your expected balance in the settlement period.

#### Converting to Expense

When you decide the money isn't coming back:
1. Click **Convert to Expense**
2. Select an expense category
3. Confirm

A regular expense entry is created in the current period, and the suspended transaction is closed.

### How It Affects Reconciliation

- **PENDING** suspended transactions are **subtracted** from your expected balance (money is out)
- **SETTLED** transactions are **added back** in the settlement period
- **CONVERTED** transactions become regular expenses

### Typical Use Cases

- **Friend owes you money**: Create loan out → settle when they pay back
- **Product return**: Create pending return → settle when refund arrives
- **Lost deposit**: Create as pending → convert to expense if never recovered

---

## 12. Installments

**Navigation:** Sidebar → Installments

Track items purchased on installment plans (buy now, pay later). Log payments monthly and track remaining balances.

### Add Installment Plan

| Field | Required | Description |
|-------|----------|-------------|
| Item Name | Yes | What you're paying for (e.g., "iPhone 15 Pro", "Furniture Set") |
| Total Price | Yes | Full purchase price |
| Currency | Yes | Currency |
| Start Period | Yes | Period when installment plan began |
| Monthly Payment | No | Expected monthly payment amount |
| Months to Pay | No | Number of installments |
| Notes | No | Additional details |

### Add Payment

When making an installment payment:

| Field | Required | Description |
|-------|----------|-------------|
| Payment Amount | Yes | Amount paid this period |
| Payment Date | Yes | Date of payment |
| Notes | No | Additional details |

### Lifecycle

```
CREATE (ACTIVE) → Add payments over time → Auto-transitions to PAID_OFF when remaining = 0
```

| Status | Meaning |
|--------|---------|
| **Active** | Payments still due. Shows in main section with progress. |
| **Paid Off** | All payments complete. Moves to history section. |

### How It Affects Reconciliation

Installment payments are **deducted** from your expected balance, similar to regular expenses but tracked separately for clarity.

### Typical Use Cases

- **Phone purchased on 12-month plan**: Track monthly payments
- **Furniture on buy-now-pay-later**: Log each installment
- **Car loan payments**: Monthly deductions tracked against total

---

## 13. Currency Conversions

**Navigation:** Sidebar → Currency Conversions

Record when you exchange money between currencies (bank exchanges, ATM withdrawals abroad, crypto trades).

### Record Conversion

| Field | Required | Description |
|-------|----------|-------------|
| From Currency | Yes | Currency you're converting from |
| From Amount | Yes | Amount in source currency |
| To Currency | Yes | Currency you're converting to |
| To Amount | Yes | Amount received in target currency |
| Unit Cost / Rate | Yes | Exchange rate (From ÷ To = rate per 1 unit of target) |
| Conversion Date | Yes | Date of exchange |
| Source Account | No | Bank account involved |
| Notes | No | Additional details |

### How It Affects Reconciliation

Currency conversions affect **both** currencies in reconciliation:
- **From currency**: Amount is subtracted (money leaving)
- **To currency**: Amount is added (money arriving)

This ensures each currency's balance reconciles independently.

### Exchange Rate Trends

The tab includes a **Rate History Chart** where you can select a currency pair and see how exchange rates have changed over time based on your recorded conversions.

### Typical Use Cases

- **Bank currency exchange**: EUR → PLN at the bank
- **ATM withdrawal abroad**: PLN → USD from foreign ATM
- **Crypto trading**: USD → BTC on an exchange
- **Freelance payment**: Received USD, converted to local currency

---

## 14. Templates

**Navigation:** Sidebar → Templates

Save and reuse period structures to avoid repetitive setup each month.

### Create Template

| Field | Required | Description |
|-------|----------|-------------|
| Template Name | Yes | Descriptive name (e.g., "Monthly Standard", "Freelancer Setup") |
| Template Type | Yes | What to capture (see below) |
| Source Period | Yes | Which existing period to copy structure from |
| Set as Default | No | Automatically suggested when creating new periods |

### Template Types

| Type | What's Saved |
|------|-------------|
| **Expense Categories Only** | The expense categories used in the source period |
| **Income Sources Only** | The income source names from the source period |
| **Full Template (Recommended)** | Categories + recurring income sources + recurring expenses |

### Apply Template

Two ways to apply a template:

1. **To an existing period**: Select the template → choose target period → Apply
2. **To a new period**: Select the template → check "Create NEW period" → fill in period details → Apply

Templates are **additive** — applying a template to a period with existing data adds the template data without deleting what's already there.

### Quick Actions

If you have a default template set, a **"Create New Period from Default"** button is available for one-click period creation.

### Typical Use Cases

- **Monthly routine**: Save your standard income/expense structure as a Full template and apply each month
- **Seasonal variation**: Create templates for different months (e.g., "Holiday Season" with gift categories)
- **Multiple income streams**: Template for freelancer months vs employment months

---

## 15. Advanced Analytics

**Navigation:** Sidebar → Advanced Analytics

Deep analysis tools beyond the basic dashboard.

### Available Analyses

| Analysis | Description |
|----------|-------------|
| **Custom Date Range** | Analyze any date range, not just predefined periods. Export results as CSV. |
| **Savings Rate** | Chart showing your savings rate (income − expenses ÷ income) over time |
| **Automated Insights** | AI-generated observations about your spending patterns |
| **Recurring Patterns** | Detects expenses that appear in 3+ periods with similar amounts |
| **Category Deep Dive** | Detailed table breakdown of performance per category |
| **Spending Anomalies** | Flags expenses that are 2.5x higher than your historical average for that category |

### Actions

- **Download Full Report** — Export comprehensive analytics report
- **Export CSV** — Export custom date range analysis data
- **Analyze Range** — Run analysis on selected date range

### Typical Use Cases

- **End-of-quarter review**: Run custom date range for Q1, export to CSV for spreadsheet analysis
- **Budget optimization**: Use recurring patterns to identify subscriptions to cancel
- **Overspend alerts**: Check anomalies to catch unusual charges
- **Savings goals**: Track savings rate trend to monitor progress

---

## 16. Settings

**Navigation:** Sidebar → Settings (or accessible via preferences)

Configure your BudgetFlow preferences.

### Available Settings

| Setting | Options | Description |
|---------|---------|-------------|
| Default Currency | Dropdown | Pre-selected currency in forms |
| Tax System | **None**, **Polish B2B**, **US Annual** | Enables tax tracking features |
| Tax Rate | 0–100% | Your applicable tax rate |
| Date Format | YYYY-MM-DD (default) | How dates are displayed |
| Timezone | Europe/Warsaw (default) | Your local timezone |

### Tax System Options

| System | Features Enabled |
|--------|-----------------|
| **None** | No tax tracking. Tax fields hidden. |
| **Polish B2B** | Polish self-employed taxation. Tax-applicable income and deductible expenses tracked. Tax benefits calculated in reconciliation. |
| **US Annual** | US annual income tax. Similar tracking with US-specific calculation. |

When a tax system is active:
- Income entries show a "Tax Applicable" checkbox
- Expense entries show a "Tax Deductible" checkbox with category
- Reconciliation Step 3 shows a **Tax Benefits** section before finalization

---

## 17. User Journey Paths

### Journey 1: First Month Setup

```
Register → Settings (currency, tax) → Currencies (add custom)
→ Accounts (add banks + opening balances) → Categories (customize)
→ Create First Period → Add Income → Add Expenses
→ Reconcile → Finalize
```

**Time estimate:** 30–60 minutes for initial setup, then 10–15 minutes per period.

### Journey 2: Monthly Routine (Experienced User)

```
Create Period (from template) → Add Income entries → Add Expenses daily/weekly
→ End of month: Enter bank balances → Reconcile
→ Quick-Balance if needed → Finalize → Check Dashboard
```

**Time estimate:** 10–15 minutes per period if using templates and tracking regularly.

### Journey 3: Multi-Currency User

```
Currencies (add needed) → Accounts (one per currency per bank)
→ Period → Income (multi-currency) → Expenses (multi-currency)
→ Currency Conversions (exchanges) → Snapshots (per account)
→ Reconcile (each currency independently) → Finalize
```

### Journey 4: Investor

```
Investment Accounts (create brokerages) → Investment Categories (holdings)
→ Each Period: Record Transfers (DCA, purchases)
→ Reconcile (transfers deducted from bank balance) → Finalize
```

### Journey 5: Installment Tracker

```
Create Installment Plan (phone, furniture, etc.)
→ Each Period: Add Payment → Reconcile (payment deducted)
→ Eventually: Plan auto-completes → Moves to "Paid Off"
```

### Journey 6: Freelancer with Tax Tracking

```
Settings (set Polish B2B or US Annual + tax rate)
→ Each Period: Income (mark tax-applicable) → Expenses (mark deductible)
→ Reconcile → Review Tax Benefits → Finalize
→ End of year: Use tax data for filing
```

### Journey 7: Lending / Refund Tracker

```
Suspended Transaction (Loan Out or Purchase Return)
→ Wait for resolution
→ Either: Settle (money back) or Convert to Expense (money lost)
→ Reconcile (accounts for suspended amounts)
```

---

## 18. FAQ & Tips

### Frequently Asked Questions

**Q: What if I forgot to track an expense and my period doesn't balance?**  
A: Use the **Quick-Balance** feature in Reconciliation. It creates an "Untracked Expenses" entry for the gap amount. Over time, try to minimize untracked spending by recording expenses promptly.

**Q: Can I edit a finalized period?**  
A: No. Finalization is permanent and locks all data. This ensures historical integrity. If you find an error, note it in the next period.

**Q: Do I need to track every single expense?**  
A: Not necessarily. Track what you can, and use Quick-Balance for the rest. The goal is to understand your spending patterns, not achieve perfection from day one.

**Q: How do investment transfers differ from expenses?**  
A: Expenses are money spent (gone). Investment transfers are money moved to another account you own (still yours, just in a different form). They're tracked separately so your spending analytics aren't inflated by investment activity.

**Q: What's the difference between deleting and settling a suspended transaction?**  
A: **Deleting** removes it as if it never existed (affects past reconciliation). **Settling** marks it as resolved and adds the money back in the settlement period. Always prefer settling over deleting.

**Q: Can I use BudgetFlow for business accounting?**  
A: BudgetFlow is designed for personal finance and freelancer tracking. It's not a full business accounting system (no invoicing, accounts payable/receivable, or double-entry bookkeeping). However, the B2B tax tracking is useful for self-employed professionals.

**Q: How are exchange rates calculated?**  
A: BudgetFlow doesn't fetch live rates. You enter the actual rate you received when making a conversion. This gives accurate tracking of your real-world exchanges.

### Power User Tips

1. **Use templates religiously** — Create a "Monthly Standard" template after your first complete period. Apply it every month to save 5+ minutes of setup.

2. **Track as you go** — Enter expenses the same day they happen. Batch entry at month-end leads to forgotten transactions and larger reconciliation gaps.

3. **Reconcile weekly** — Don't wait until month-end. Check your balance snapshots mid-month to catch errors early.

4. **Mark recurring items** — Flag recurring income and expenses. This powers the recurring pattern detection in Advanced Analytics and makes templates more useful.

5. **Use categories wisely** — Don't create too many categories. 10–15 is usually enough. Use parent/child hierarchy for detail without clutter.

6. **Check anomalies monthly** — After finalizing, visit Advanced Analytics → Spending Anomalies. It highlights unusual charges you might want to investigate.

7. **Set a default template** — The "Create New Period from Default" button in Templates is the fastest way to start each month.

8. **Use notes fields** — Add context to unusual transactions. Future you will thank present you when reviewing analytics.

---

## Module Quick Reference

| Module | Global/Period | Primary Purpose |
|--------|--------------|-----------------|
| Dashboard | Period | Financial overview and charts |
| Periods | Global | Create and manage time periods |
| Income | Period | Track money coming in |
| Expenses | Period | Track money going out |
| Reconciliation | Period | Verify balances match reality |
| Accounts | Global | Manage bank accounts and wallets |
| Currencies | Global | Manage available currencies |
| Categories | Global | Organize expense types |
| Investments | Both | Track portfolio activity |
| Suspended | Period | Track temporary money outflows |
| Installments | Both | Track payment plans |
| Conversions | Period | Track currency exchanges |
| Templates | Global | Reuse period structures |
| Advanced Analytics | Both | Deep analysis and reporting |
| Settings | Global | User preferences and tax config |

---

**Document Owner:** Product Team  
**Last Updated:** 2026-04-11  
**Review Cycle:** With each major feature release
