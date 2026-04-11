# BudgetFlow — Gap Priority Report

> **Audit date**: 2026-04-03
> **Total gaps identified**: 173 / 220
> **Release blockers**: 95

This report groups all identified gaps into strategic focus areas, scored by a combination of:
- **Weight** (Critical=10, High=7, Medium=4, Low=1)
- **Release blocker count** (items that must be resolved before go-live)
- **NOT_SUPPORTED count** (complete absence vs. partial implementation)

Items within each group are sorted: blockers first, then weight descending.

---

## 🔴 TIER 1 — Must Fix Before Launch

These groups represent either security violations, data integrity risks, or foundational product capabilities that block a minimum viable release.

---

### 1. 🔐 Security Hardening (Auth + Sessions + Abuse)
**Score: 91 weight pts | 10 blockers | 7 NOT_SUPPORTED**

The authentication layer has the bare minimum (bcrypt passwords + JWT), but every surrounding security control is absent.

| ID | Question | Gap | Priority |
|---|---|---|---|
| S143 | Is MFA available? | No TOTP, no recovery codes | Critical |
| S144 | MFA on high-risk actions? | No step-up auth | Critical |
| S169 | Rate limits on login/register/OTP? | No slowapi or Redis throttling | High |
| S170 | Brute-force / bot protection? | No lockout or CAPTCHA | High |
| S145 | Session token revocation? | JWTs not revocable; no blacklist | High |
| S148 | Refresh token rotation? | No refresh tokens at all | High |
| S147 | View/revoke active sessions? | No session model | Medium |

**Suggested epic:** `SEC-001: Authentication Hardening`
Add MFA (PyOTP), rate limiting (slowapi + Redis), refresh token rotation, and session revocation.

---

### 2. 📋 Audit Logging & Traceability
**Score: 42 weight pts | 4 blockers | 4 NOT_SUPPORTED**

There is zero audit trail anywhere in the system. This is both a GDPR requirement and a forensic necessity.

| ID | Question | Gap | Priority |
|---|---|---|---|
| S162 | Privileged actions logged? | No AuditLog model or middleware | High |
| S163 | Audit logs tamper-evident? | No logging pipeline at all | High |
| S164 | Sensitive values masked in logs? | No log masking formatter | High |
| F012 | Full audit trail for changes? | No before/after event tracking | High |

**Suggested epic:** `SEC-002: Audit Logging`
Implement SQLAlchemy event listeners or middleware to emit immutable audit events. Store actor, target, before/after per mutation.

---

### 3. 🔒 Data Encryption & Privacy
**Score: 49 weight pts | 6 blockers | 5 NOT_SUPPORTED**

Financial and personal data is stored in plaintext. This is a GDPR Article 32 violation for production.

| ID | Question | Gap | Priority |
|---|---|---|---|
| S150 | Sensitive data encrypted at rest? | No field encryption, no KMS | High |
| S153 | Field-level encryption for PII? | email hashed but no other encryption | High |
| S151 | Keys stored separately? | No KMS integration | High |
| S152 | Key rotation? | No key rotation logic | High |
| S182 | Data retention schedule? | Data persists indefinitely | High |
| S183 | Deletion routines verified? | No deletion confirmation tooling | High |

**Suggested epic:** `SEC-003: Encryption & Retention`
Add `sqlalchemy-utils` EncryptedType on sensitive columns, wire AWS KMS, add scheduled data retention jobs.

---

### 4. 📥 Transaction Imports
**Score: 21 weight pts | 3 blockers | 3 NOT_SUPPORTED**

Without import capability, users cannot onboard existing data. This is a day-one usability blocker.

| ID | Question | Gap | Priority |
|---|---|---|---|
| F028 | Import from CSV/XLSX/PDF? | No parsers or upload endpoints | High |
| F029 | Interactive column mapping? | No mapping UI or saved rules | High |
| F030 | Duplicate detection across imports? | No dedup hashes on transactions | High |

**Suggested epic:** `FEAT-001: Statement Import`
Build upload endpoint, CSV/XLSX parser (pandas), interactive column mapping UI, and hash-based dedup on save.

---

### 5. 💳 Transaction Ledger Completeness
**Score: 29 weight pts | 3 blockers | 5 NOT_SUPPORTED**

The current model only handles simple expense/income entries. Core ledger operations are missing.

| ID | Question | Gap | Priority |
|---|---|---|---|
| F026 | Cleared vs. pending transactions? | No status field on entries | High |
| F032 | Internal transfers detected? | No InternalTransfer model | High |
| F033 | Split transactions? | No line-item splits | High |
| F034 | Attach receipts/notes? | No Attachment model | Medium |
| F035 | VAT/tax tags? | No tag or JSONB tag field | Medium |

**Suggested epic:** `FEAT-002: Transaction Ledger Completeness`
Add `status` enum (CLEARED/PENDING), `InternalTransfer` linking model, split-line structure, and S3-backed attachments.

---

### 6. 🔍 Auto-Categorization Engine
**Score: 30 weight pts | 3 blockers | 6 NOT_SUPPORTED**

Users must manually categorize every entry. A rules engine is critical for usability at scale.

| ID | Question | Gap | Priority |
|---|---|---|---|
| F038 | Rule-based auto-categorization? | No rules engine | High |
| F039 | Rule priority and conflict resolution? | No priority model | High |
| F040 | Bulk recategorize from rules? | No background job | High |
| F037 | Polish default categories? | Seed data may lack locale | Medium |
| F041 | Learn from corrections? | No feedback loop / ML | Medium |

**Suggested epic:** `FEAT-003: Categorization Engine`
Implement a `CategorizationRule` model (merchant keyword, amount range, source account), priority field, and a background job to re-process past entries.

---

### 7. 💰 Budgeting Module
**Score: 30 weight pts | 2 blockers | 6 NOT_SUPPORTED**

No budgeting capability exists at all. This is a core product differentiator.

| ID | Question | Gap | Priority |
|---|---|---|---|
| F045 | Monthly/quarterly/annual budgets? | No Budget entity | High |
| F046 | Budget per category/account? | No Budget dimensions | High |
| F048 | Budget threshold alerts? | No alert engine | Medium |
| F049 | Performance in % and absolute? | No reporting widgets | Medium |
| F047 | Rollover budgets? | No rollover logic | Medium |
| F050 | Exclude transactions from budget? | No exclusion flag | Medium |

**Suggested epic:** `FEAT-004: Budgeting`
Add `Budget` and `BudgetPeriod` DB models, per-category allocation, calculation service, and threshold alerting.

---

## 🟠 TIER 2 — High Value, Next Phase Priority

Important product functionality that should follow Tier 1, or can run in parallel with smaller teams.

---

### 8. 🏦 Open Banking & Bank Connectivity
**Score: 70+ weight pts | 6 blockers | 6 NOT_SUPPORTED**

The most complex single feature group. All bank connectivity is absent — no provider adapters, no consent lifecycle, no sync jobs.

| ID | Question | Gap | Priority |
|---|---|---|---|
| F014 | Connect Polish banks via Open Banking? | No PolishAPI/GoCardless integration | High |
| F015 | Refresh balances on demand? | No sync jobs | High |
| F016 | Detect expired consent? | No consent expiry logic | High |
| S177 | Minimal consent scopes shown to user? | No consent screens | High |
| S178 | Revoke bank access? | No revoke flow | High |
| S179 | Consent timestamped, scoped, auditable? | No consent model at all | Critical |

**Suggested epic:** `FEAT-005: Open Banking (PolishAPI / GoCardless)`
This is an XL scope. Requires: Consent entity, provider adapter interface, callback endpoints, sync jobs, and full UI flow. Recommend scoping as its own quarter.

---

### 9. 🏗️ Architecture & Production Reliability
**Score: 84 weight pts | 12 blockers**

The platform lacks infrastructure needed to run reliably in production under real load.

| ID | Gap | Priority |
|---|---|---|
| A199 | No async job queue (Celery) | High |
| A200 | Sync retries create duplicates | High |
| A201 | APIs not idempotent | High |
| A204 | No circuit breakers | High |
| A208 | No APM / structured logging | High |
| A205 | No event bus for notifications | Medium |
| A212 | No feature flags | Medium |

**Suggested epic:** `ARCH-001: Production Readiness`
Add Celery + Redis for async jobs, idempotency keys on mutation endpoints, Prometheus/Datadog APM, and circuit-breaker pattern for external calls.

---

### 10. 📈 Investment Ledger (Manual First)
**Score: 56 weight pts | 3 blockers**

The `Investment` and `InvestmentAccount` models exist but are very thin — tracking only a category name and opening balance.

| ID | Gap | Priority |
|---|---|---|
| F075 | Sync holdings from broker? | No broker integration | High |
| F076 | Track stocks, ETFs, bonds, options? | No asset taxonomy | High |
| F077 | Units, cost basis, fees, dividends? | Only raw decimal balance | High |
| F082 | Market vs. cost vs. unrealized gain? | No portfolio analytics | High |
| F078 | FIFO / average cost basis? | No tax lot engine | High |
| F083 | Allocation by class/sector? | No allocation logic | Medium |

**Suggested epic:** `FEAT-006: Investment Ledger`
Extend `Investment` to hold `units`, `unit_price`, `asset_class` enum. Add `HoldingTransaction` for buys/sells/dividends. Manual entry only (no broker sync) for now.

---

### 11. 💸 Receivables & Personal Loans
**Score: ~50 weight pts | 0 blockers (but critical for completeness)**

The installment model exists but there is no P2P lending/borrowing concept.

| ID | Gap | Priority |
|---|---|---|
| F096 | Lend money as a tracked receivable? | No Receivable entity | High |
| F097 | Borrower, amount, schedule? | No form/model | High |
| F098 | Partial repayments? | No repayment workflow | High |
| F103 | Track money owed to friends? | No Liability type | Medium |

**Suggested epic:** `FEAT-007: Receivables & Personal Loans`
Add `Receivable` model (borrower_name, amount, currency, due_date, status), `Repayment` ledger, and balance calculation service.

---

## 🟡 TIER 3 — Important but Deferrable

Meaningful product features with no release-blocker flags. Can be deferred to a later phase.

| Feature Group | Gap Count | Suggested Epic |
|---|---|---|
| Reporting enhancements (filters, PDF export) | 4 | `FEAT-008: Rich Reporting` |
| Goals & savings targets | 3 | `FEAT-009: Goals` |
| Notifications & alerts (email/push) | 2 | `FEAT-010: Notifications` |
| Forecasting & cash flow calendar | 3 | `FEAT-011: Cash Flow Calendar` |
| Search & saved filter views | 2 | `FEAT-012: Search` |
| Crypto tracking (manual) | 5 | `FEAT-013: Crypto (Manual)` |
| Virtual envelopes / reserves | 3 | `FEAT-014: Envelope Budgeting` |
| Collaboration / RBAC | 2 | `FEAT-015: Multi-user` |
| Multi-workspace / portfolio | 2 | `FEAT-016: Workspaces` |

---

## 🔵 TIER 4 — Future / Advanced

Low-urgency items valuable at scale or for a specific user segment.

| Feature Group | Notes |
|---|---|
| Scenario planning / what-if | Requires forecast engine first |
| Real estate & alternative assets | Niche user segment |
| Corporate actions engine | Only needed with broker sync |
| Multi-tenancy / family office | Growth-stage concern |
| Data residency (EU regions) | Infrastructure concern |
| Feature flags / staged rollout | Nice-to-have once platform stable |
| Vendor abstraction layer | Refactor once providers chosen |

---

## 📋 Recommended Next Phase Roadmap

```
Phase 2A — Foundation (Parallel workstreams, ~6-8 weeks)
├── SEC-001: Authentication Hardening   (MFA, rate limits, token rotation)
├── SEC-002: Audit Logging             (immutable event store)
├── SEC-003: Encryption & Retention    (field encryption, KMS, retention jobs)
└── ARCH-001: Production Readiness     (Celery, idempotency, APM, observability)

Phase 2B — Core Product (~8-10 weeks)
├── FEAT-001: Statement Import         (CSV/XLSX/PDF + dedup)
├── FEAT-002: Transaction Completeness (status, splits, transfers, attachments)
├── FEAT-003: Categorization Engine    (rules engine + bulk apply)
└── FEAT-004: Budgeting               (Budget model + alerts + reporting)

Phase 2C — Growth Features (~Q3)
├── FEAT-005: Open Banking            (full quarter — PolishAPI/GoCardless)
├── FEAT-006: Investment Ledger       (manual entry first, broker sync later)
└── FEAT-007: Receivables & Loans
```

> **CAUTION:** Do not begin Phase 2B before SEC-001 and SEC-002 are in place. Adding features on top of an unaudited, rate-limit-free system with no action traceability is a significant compliance and security liability.

> **IMPORTANT:** Open Banking (FEAT-005) should be treated as its own quarter. Consent lifecycle, PolishAPI/PSD2 compliance, and provider integration are XL scope. Starting it without the SEC foundations in place would also breach PSD2 SCA requirements.

---

## Scoring Reference

| Priority | Weight |
|---|---|
| Critical | 10 |
| High | 7 |
| Medium | 4 |
| Low | 1 |

| Verdict | Meaning |
|---|---|
| NOT_SUPPORTED | Feature completely absent from codebase |
| PARTIALLY_SUPPORTED | Some implementation exists; critical path incomplete |
| UNCLEAR | Depends on infra/ops config not visible in code |
