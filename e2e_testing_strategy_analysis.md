# BudgetFlow E2E Testing Strategy: Comprehensive Options Analysis

> **Project**: BudgetFlow (FastAPI + Dash, 14 tabs, 220+ requirements)
> **Current State**: 151 backend tests (unit + integration), 4 Playwright E2E tests
> **Date**: April 2026

---

## Executive Summary

You have a well-structured financial application with solid backend test coverage but **minimal E2E automation** (4 Playwright tests covering ~15% of user flows). Given the complexity of BudgetFlow (multi-currency reconciliation, installments, investments, suspended transactions, templates), you need a strategy that maximizes **coverage per dollar** while fitting a solo-developer workflow.

After analyzing 8 approaches across cost, speed, coverage, maintainability, and edge-case discovery, **I recommend a hybrid strategy** combining AI-agent-driven Playwright (Option 3) with LLM mutation testing (Option 8) and Antigravity-built automation (Option 2).

---

## Your Current Testing Landscape

| Layer | Count | Coverage Estimate | Gap |
|-------|-------|-------------------|-----|
| Unit Tests | ~65 | ~60% of CRUD/services | Missing: some edge cases, schema validation |
| Integration Tests | ~86 | ~70% of API endpoints | Missing: complex multi-step workflows |
| E2E (Playwright) | 4 | ~15% of user flows | Missing: installments, investments, templates, analytics, suspended, conversions, categories, settings |
| Frontend Unit | 0 | 0% | No callback logic testing |

### Critical E2E Gaps (by feature)

```
✅ Covered                    ❌ Not Covered
─────────────────────────     ─────────────────────────────────
Auth (login/register/logout)  Installment full lifecycle
Basic budget flow (happy)     Investment account + transfers
Multi-currency setup          Suspended transaction workflows
Deep-link redirection         Template create/apply/reuse
                              Currency conversion E2E
                              Category CRUD (edit/delete)
                              Analytics dashboards
                              Export (CSV/PDF/JSON)
                              Reconciliation edge cases
                              Period unfreezing
                              Account deactivation
                              Settings management
```

---

## Option 1: Hire a Traditional QA Automation Engineer

### What It Is
Hire a freelance or part-time automation engineer (Upwork, Toptal, Arc.dev) to manually write and maintain Playwright test suites.

### How It Works
1. You write requirements / user stories
2. Engineer studies the app, maps flows
3. Engineer writes Page Object Models + test suites
4. Engineer maintains tests as UI evolves
5. You review PRs and integrate into CI

### Cost Analysis

| Model | Rate | Hours/Month | Monthly Cost | Annual Cost |
|-------|------|-------------|-------------|-------------|
| Junior (offshore) | $40-60/hr | 40 | $1,600-2,400 | $19,200-28,800 |
| Mid-level freelancer | $75-125/hr | 30 | $2,250-3,750 | $27,000-45,000 |
| Senior/lead | $125-200/hr | 20 | $2,500-4,000 | $30,000-48,000 |
| **Initial framework build** | — | 80-120 hrs | **$6,000-15,000** | one-time |

### Pros
- Human intuition for edge cases and UX issues
- Can handle complex flows (MFA, visual regression)
- Produces production-grade, maintainable code
- Domain expertise grows over time

### Cons
- **Highest ongoing cost** — requires continuous engagement
- **Slow ramp-up** — 2-4 weeks to learn your Dash app patterns
- **Fragile to UI changes** — Dash callback-driven UI requires constant selector updates
- **Availability risk** — single point of failure if freelancer leaves
- **Communication overhead** — explaining BudgetFlow domain logic

### Time to First Value: 3-6 weeks
### Verdict: ⭐⭐⭐ Good quality, but **cost-prohibitive for a solo project**

---

## Option 2: AI-Built Automation Framework (Built by Me / Antigravity)

### What It Is
I (Antigravity) build a comprehensive, production-grade Playwright test framework directly in your repo, using my deep knowledge of your codebase.

### How It Works
1. I analyze all 14 tabs, callbacks, and component IDs
2. I create a Page Object Model layer for BudgetFlow's Dash UI
3. I write 30-50 E2E test scenarios covering all critical flows
4. I add conftest fixtures, test data factories, and CI integration
5. You run them with `pytest tests/e2e -v`

### What I'd Build

```
tests/e2e/
├── conftest.py                        # Playwright fixtures, auth helpers
├── pages/                             # Page Object Models
│   ├── login_page.py
│   ├── dashboard_page.py
│   ├── period_setup_page.py
│   ├── income_page.py
│   ├── expense_page.py
│   ├── accounts_page.py
│   ├── currencies_page.py
│   ├── categories_page.py
│   ├── investments_page.py
│   ├── installments_page.py
│   ├── suspended_page.py
│   ├── conversions_page.py
│   ├── templates_page.py
│   ├── reconciliation_page.py
│   └── analytics_page.py
├── flows/
│   ├── test_complete_budget_cycle.py   # Full happy path
│   ├── test_multi_currency_recon.py   # Multi-currency balancing
│   ├── test_installment_lifecycle.py  # Create → pay → paid-off
│   ├── test_investment_tracking.py    # Account → transfer → recon
│   ├── test_suspended_workflows.py    # Settle / convert / carry fwd
│   ├── test_template_reuse.py         # Create → apply → verify
│   ├── test_export_flows.py           # CSV, PDF, JSON downloads
│   ├── test_period_management.py      # Finalize, unfreeze, delete
│   └── test_analytics_dashboard.py    # Charts render, data correct
├── edge_cases/
│   ├── test_auth_edge_cases.py        # Token expiry, session hijack
│   ├── test_concurrent_editing.py     # Race conditions
│   ├── test_negative_amounts.py       # Validation boundary tests
│   ├── test_empty_states.py           # No data scenarios
│   ├── test_large_datasets.py         # Performance with 100+ items
│   └── test_category_protection.py    # System category integrity
└── utils/
    ├── helpers.py                     # Wait helpers, retry logic
    └── test_data.py                   # Factories for test entities
```

### Cost Analysis

| Item | Cost | Time |
|------|------|------|
| Framework + 30 tests | $0 (your existing subscription) | 1-2 conversations |
| Expand to 50+ tests | $0 | 1 additional conversation |
| Maintenance per UI change | $0 | Ask me to update |
| **Total Year 1** | **$20/mo (Pro) or $100/mo (Max)** | — |

### Pros
- **Near-zero marginal cost** — part of your existing subscription
- **Instant codebase knowledge** — I already know every callback ID, endpoint, and schema
- **Fast delivery** — framework + 30 tests in one session
- **Maintainable** — I can update tests when UI changes
- **Follows your standards** — POM, type hints, Google docstrings

### Cons
- **Not autonomous** — requires you to trigger me
- **No self-healing** — tests break when selectors change (standard Playwright behavior)
- **Coverage limited by my session knowledge** — I test what I know, may miss runtime quirks
- **No visual regression** built-in

### Time to First Value: **Same day**
### Verdict: ⭐⭐⭐⭐⭐ **Best value-for-money. Start here.**

---

## Option 3: Playwright MCP + AI Agent (Autonomous Test Generation)

### What It Is
Use the Playwright MCP server (`npx @playwright/mcp@latest`) with an AI agent (Claude, Cursor, or Antigravity) to autonomously explore your app and generate/heal tests using the accessibility tree.

### How It Works
1. Start Playwright MCP server pointing at your running Dash app
2. AI agent connects via MCP protocol
3. Agent explores the app using accessibility tree (not screenshots)
4. Agent generates deterministic Playwright test code
5. Agent self-heals broken selectors by re-inspecting the tree
6. Tests are committed to your repo and run in CI

### Architecture
```
┌─────────────────┐     MCP Protocol    ┌──────────────────┐
│   AI Agent      │◄──────────────────►│ Playwright MCP   │
│ (Claude/Cursor) │    (tools, a11y)   │ Server           │
│                 │                     │ (@playwright/mcp)│
└─────────────────┘                     └──────┬───────────┘
                                               │
                                               ▼
                                     ┌──────────────────┐
                                     │  Your Dash App   │
                                     │  localhost:8050   │
                                     └──────────────────┘
```

### Cost Analysis

| Item | Cost |
|------|------|
| Playwright MCP server | Free (open source) |
| AI agent (Claude API) | ~$5-15/run (Sonnet) for full exploration |
| Infrastructure | Your local machine |
| **Monthly estimate** | $20-60 for weekly re-scans |
| **Annual** | $240-720 |

### Pros
- **Self-healing** — adapts to UI changes via accessibility tree, not brittle CSS
- **Exploratory** — discovers flows you didn't think to test
- **Generates deterministic code** — output is standard Playwright, runs in CI
- **Works with Dash** — accessibility tree handles Dash components well
- **Composable** — use it alongside hand-written tests

### Cons
- **Still maturing** — MCP + agent quality varies with model
- **Requires running app** — needs `docker-compose up` for each session
- **Token costs** — complex flows with many screenshots burn tokens fast
- **Not a replacement for strategic test design** — good at mechanics, weaker at business logic edge cases
- **Dash app accessibility** — some Dash components may have poor a11y strings

### Time to First Value: **1-2 days setup + exploration**
### Verdict: ⭐⭐⭐⭐ **Excellent complement to Option 2. Best for ongoing maintenance + self-healing.**

---

## Option 4: Claude Computer Use / Perplexity Computer

### What It Is
Use an AI agent with **full OS-level computer control** (mouse, keyboard, screen reading) to interact with your app as a real user would.

### How It Works

#### Claude Computer Use
1. Set up a VPS or Mac Mini with your app running
2. Claude connects via Computer Use API
3. Claude takes screenshots, moves mouse, types — just like a human
4. You describe test scenarios in natural language
5. Claude executes them, reports results

#### Perplexity Computer
1. Cloud-based agent accesses your app URL
2. Define objectives (\"ensure checkout flow works\")
3. Agent orchestrates multiple models for exploration
4. Custom Skills allow teaching domain-specific workflows
5. Integrates with GitHub for code push

### Cost Analysis

| Platform | Pricing | Monthly Estimate |
|----------|---------|-----------------|
| **Claude Computer Use (API)** | Standard token pricing + vision | $30-100/mo for regular runs |
| **Claude Max sub** | $100-200/mo | Includes computer use |
| **Perplexity Computer** | ~$200/mo Pro plan | Includes agent compute |
| **Dedicated Mac Mini** | ~$600 one-time + electricity | One-time hardware |
| **VPS alternative** | $5-20/mo | Recommended over Mac Mini |

### Pros
- **True user simulation** — interacts exactly like a human
- **No selector dependency** — uses visual/semantic understanding
- **Discovers UX issues** — notices things like confusing labels, broken layouts
- **Natural language test definition** — \"create a period, add income, reconcile\"
- **Can test anything** — even third-party integrations, CAPTCHA workarounds

### Cons
- **Slow** — screenshot-based interaction is 5-10x slower than Playwright
- **Expensive at scale** — vision tokens are costly per interaction
- **Non-deterministic** — same test can take different paths, hard to reproduce failures
- **No test code output** — results are reports, not reusable test scripts
- **Overkill for most E2E** — Playwright + MCP handles 90% of cases faster/cheaper
- **Infrastructure overhead** — need a running environment 24/7

### Time to First Value: **2-3 days**
### Verdict: ⭐⭐⭐ **Interesting for exploration and UX auditing, but too expensive and slow for regression testing**

---

## Option 5: Cloud TaaS Platforms (TestMu AI / BrowserStack)

### What It Is
Use a Testing-as-a-Service platform that provides cloud browser infrastructure, AI test generation (KaneAI), cross-browser testing, and auto-healing.

### Key Players

| Platform | Key Feature | Starting Price |
|----------|-------------|---------------|
| **TestMu AI** (ex-LambdaTest) | KaneAI test gen, 10K+ devices | Free tier + $15-39/mo |
| **BrowserStack** | Real device cloud, Percy visual | $29/mo |
| **Sauce Labs** | Cross-browser, analytics | Custom pricing |
| **Playwright cloud** (MS) | Native cloud hosting | Coming soon |

### How It Works
1. Write Playwright/Selenium tests locally
2. Point test execution at cloud infrastructure
3. Tests run on thousands of browser/OS combos
4. AI features detect flaky tests and suggest fixes
5. Dashboard shows results, screenshots, videos

### Cost Analysis

| Tier | Monthly | What You Get |
|------|---------|-------------|
| Free | $0 | Basic live testing, limited sessions |
| Starter | $15-39/mo | Automation, few parallel sessions |
| Pro | $79-149/mo | More parallels, integrations, analytics |
| Enterprise | $300+/mo | Unlimited, SSO, dedicated support |

### Pros
- **Cross-browser coverage** — test on Safari, Firefox, mobile browsers
- **No infra management** — cloud handles browsers
- **AI auto-healing** — KaneAI adapts to UI changes
- **Integrates with CI/CD** — GitHub Actions, Jenkins, etc.
- **Professional dashboards** — test analytics, flaky test detection

### Cons
- **Your tests still need writing** — platform runs tests, doesn't create them
- **Overkill for single-user Dash app** — you're not shipping to 10 browsers
- **Latency** — remote execution is slower than local
- **Pricing scales with parallelism** — costs grow with test suite
- **Dash-specific quirks** — may need custom waits for callback-driven UI

### Time to First Value: **1-2 days** (pointing existing tests at cloud)
### Verdict: ⭐⭐ **Not worth it yet. Your app is single-user, single-browser. Revisit when deploying publicly.**

---

## Option 6: Managed QA Service (QA Wolf)

### What It Is
A fully managed testing service where QA Wolf's team writes, maintains, and runs your E2E tests. You get 80% coverage guarantee and human-verified bug reports.

### How It Works
1. You onboard with QA Wolf, share access to staging environment
2. Their engineers (using Playwright) build your entire test suite
3. Tests run on every deploy / PR
4. When tests fail, a human verifies if it's a real bug
5. You own the test code

### Cost Analysis

| Metric | Value |
|--------|-------|
| Annual contract | **$60,000 - $250,000+** |
| Per-test estimate | ~$40-44/test/month |
| Minimum engagement | Typically $5,000-8,000/mo |

### Pros
- **Highest quality** — professional QA engineers with deep expertise
- **80% coverage guarantee** — contractual commitment
- **Zero maintenance burden** — they handle all test updates
- **Human-verified failures** — no false positives
- **You own the code** — can walk away with the test suite

### Cons
- **Massively expensive** — $60K+/year is insane for a solo project
- **Designed for funded startups/enterprises** — complete mismatch for your scale
- **Over-engineering** — you don't need 24/7 QA team for a personal finance app
- **Vendor lock-in risk** — despite code ownership, institutional knowledge walks away

### Time to First Value: **2-4 weeks**
### Verdict: ⭐ **Immediately disqualified by cost. Revisit only at Series A.**

---

## Option 7: Stagehand + BrowserBase (AI Browser Automation Framework)

### What It Is
Stagehand is an open-source framework built on Playwright that adds natural language capabilities (`act()`, `extract()`, `observe()`). BrowserBase provides cloud browser infrastructure.

### How It Works
```javascript
// Instead of rigid selectors:
await page.click('#add-income-btn')

// You write intent-based code:
await stagehand.act('Click the Add Income button')
await stagehand.extract('Get the total income amount displayed')
```

### Cost Analysis

| Component | Cost |
|-----------|------|
| Stagehand framework | Free (open source) |
| BrowserBase infra | $0-49/mo (dev tier) |
| LLM API (for `act`/`extract`) | $10-30/mo |
| **Total** | **$10-79/mo** |

### Pros
- **Intent-based testing** — resilient to selector changes
- **Natural language** — easier to write and maintain than raw selectors
- **Open source** — no vendor lock-in on the framework
- **Works with existing Playwright** — incremental adoption

### Cons
- **JavaScript/TypeScript only** — doesn't fit your Python testing stack
- **LLM dependency** — every test action requires an API call (cost + latency)
- **Non-deterministic** — LLM interpretation can vary between runs
- **Still requires test writing** — you author the intent, not the framework
- **BrowserBase cost** — adds up for frequent runs in CI
- **Dash compatibility uncertain** — designed for typical web apps, not Dash's SPA model

### Time to First Value: **3-5 days** (rewrite existing tests in JS)
### Verdict: ⭐⭐ **Interesting concept but wrong language ecosystem for BudgetFlow. Python Playwright + MCP achieves the same.**

---

## Option 8: LLM-Enhanced Mutation Testing (mutmut + AI Analysis)

### What It Is
Use mutation testing (mutmut) to find gaps in your test suite, then use an LLM to analyze surviving mutants and generate the missing tests. This isn't E2E per se, but dramatically improves **test quality confidence**.

### How It Works
```
┌───────────────┐     ┌──────────────────┐     ┌────────────────┐
│   Your Code   │────►│  mutmut          │────►│ Surviving      │
│   (CRUD,      │     │  (mutates code)  │     │ Mutants Report │
│   services)   │     └──────────────────┘     └───────┬────────┘
└───────────────┘                                      │
                                                       ▼
                                              ┌────────────────┐
                                              │  LLM Analysis  │
                                              │  (Claude/GPT)  │
                                              │                │
                                              │  • Prioritize  │
                                              │  • Generate    │
                                              │    kill tests  │
                                              │  • Filter      │
                                              │    equivalents │
                                              └────────────────┘
```

### Cost Analysis

| Item | Cost |
|------|------|
| mutmut | Free (open source) |
| LLM analysis (Claude API) | $2-10 per analysis run |
| Compute (mutation runs) | Your CI / local machine |
| **Monthly** | **$5-30** |
| **Annual** | **$60-360** |

### What It Tells You

Instead of just checking "does my test pass?", mutation testing asks **"would my test catch a real bug?"**

```python
# Original code:
if remaining_balance <= 0:
    status = "PAID_OFF"

# Mutant (mutmut changes <= to <):
if remaining_balance < 0:    # ← Would your tests catch this?
    status = "PAID_OFF"

# If no test fails → your tests are WEAK for this logic
```

### Pros
- **Deepest quality metric** — measures test effectiveness, not just coverage
- **Dirt cheap** — open source tools + minimal LLM usage
- **Perfect for financial logic** — catches subtle arithmetic/boundary bugs in reconciliation
- **LLM superpower** — AI excels at analyzing mutation reports and generating targeted tests
- **Composable** — works alongside any other testing approach
- **Catches what E2E can't** — logical correctness at the unit level

### Cons
- **Not E2E** — doesn't test the UI or user flows
- **CPU intensive** — mutation runs can take 10-60 minutes on large codebases
- **Requires existing tests** — mutmut only measures tests you already have
- **False positives** — some mutants are "equivalent" (functionally identical)
- **LLM-generated tests need review** — occasional hallucinations

### Time to First Value: **2-3 hours**
### Verdict: ⭐⭐⭐⭐⭐ **Cheapest way to dramatically improve test quality. Essential for financial logic.**

---

## Comparison Matrix

Scored 1-5 (5 = best) with weights reflecting solo developer priorities.

| Criterion (Weight) | Option 1: Hire QA | Option 2: Antigravity Built | Option 3: Playwright MCP | Option 4: Computer Use | Option 5: Cloud TaaS | Option 6: QA Wolf | Option 7: Stagehand | Option 8: Mutation + LLM |
|---|---|---|---|---|---|---|---|---|
| **Cost** (25%) | 1 | 5 | 4 | 3 | 3 | 1 | 3 | 5 |
| **Time to Value** (20%) | 2 | 5 | 4 | 3 | 3 | 2 | 2 | 5 |
| **Coverage Depth** (15%) | 5 | 4 | 3 | 3 | 3 | 5 | 3 | 4 |
| **Edge-Case Discovery** (15%) | 4 | 3 | 4 | 5 | 2 | 5 | 3 | 5 |
| **Maintainability** (10%) | 3 | 4 | 5 | 2 | 4 | 5 | 3 | 4 |
| **Self-Healing** (5%) | 1 | 1 | 5 | 4 | 4 | 5 | 5 | 1 |
| **CI/CD Integration** (5%) | 5 | 5 | 4 | 2 | 5 | 5 | 3 | 5 |
| **Fits Your Stack** (5%) | 4 | 5 | 5 | 3 | 3 | 4 | 1 | 5 |
| **Weighted Score** | **2.65** | **4.30** | **3.95** | **3.15** | **3.00** | **3.05** | **2.70** | **4.65** |

---

## 🏆 Recommended Hybrid Strategy

### The "Maximum Coverage, Minimum Investment" Stack

```
┌──────────────────────────────────────────────────────────────────┐
│                     YOUR TESTING PYRAMID                         │
│                                                                  │
│            ╱╲         E2E: Playwright MCP Agent (Option 3)      │
│           ╱  ╲        Self-healing, exploratory, 5-10 flows     │
│          ╱────╲                                                  │
│         ╱      ╲      E2E: Antigravity-Built (Option 2)         │
│        ╱────────╲     30-50 deterministic tests, POM framework  │
│       ╱          ╲                                               │
│      ╱────────────╲   Quality: Mutation Testing (Option 8)      │
│     ╱              ╲  Verify test effectiveness, kill mutants   │
│    ╱────────────────╲                                            │
│   ╱                  ╲ Existing: 151 Unit + Integration Tests   │
│  ╱────────────────────╲                                          │
└──────────────────────────────────────────────────────────────────┘
```

### Phase 1: Foundation (This Week) — **Cost: $0**
> **Options: 2 + 8**

1. **I build the E2E framework** with Page Object Models for all 14 tabs
2. **I write 30+ deterministic E2E tests** covering all critical flows
3. **I set up mutmut** on `reconciliation_service.py` and all CRUD modules
4. **I feed mutation report to LLM** to generate targeted kill-tests
5. **I integrate everything into GitHub Actions**

**Deliverables:**
- `tests/e2e/pages/` — Page Object Models
- `tests/e2e/flows/` — 20+ flow tests
- `tests/e2e/edge_cases/` — 10+ edge case tests
- `mutmut` configured for backend services
- Updated CI pipeline

### Phase 2: Self-Healing Layer (Next Month) — **Cost: ~$30/mo**
> **Option: 3**

1. **Add Playwright MCP server** to your dev workflow
2. **AI agent periodically re-scans** the app for new/changed flows
3. **Auto-generate heal patches** when selectors break
4. **Exploratory testing** — agent navigates freely, reports anomalies

### Phase 3: Continuous Improvement (Ongoing) — **Cost: ~$10/mo**
> **Options: 2 + 8**

1. **Monthly mutation testing runs** on new code paths
2. **LLM analysis of surviving mutants** → generate new tests
3. **Ask me to update tests** when UI changes significantly
4. **Track mutation score trend** as your primary quality metric

### Total Annual Investment

| Component | Monthly | Annual |
|-----------|---------|--------|
| Antigravity subscription (you already have) | $20-100 | $240-1,200 |
| Claude API for MCP agent | ~$20-30 | $240-360 |
| LLM for mutation analysis | ~$5-10 | $60-120 |
| **Total** | **$45-140** | **$540-1,680** |

### vs. Traditional QA Hire

| Metric | Hybrid Strategy | QA Engineer |
|--------|----------------|-------------|
| **Annual cost** | $540-1,680 | $30,000-48,000 |
| **Time to 80% coverage** | 1-2 weeks | 6-12 weeks |
| **Ongoing maintenance** | Near-zero marginal cost | $2,000-4,000/mo |
| **Edge case discovery** | High (mutation + exploration) | High (human intuition) |
| **Self-healing** | Yes (MCP layer) | Manual updates |
| **ROI** | **~20-50x better** | Baseline |

---

## Quality Metrics to Track

### Coverage KPIs

| Metric | Tool | Target | Current |
|--------|------|--------|---------|
| Line coverage | `pytest --cov` | 80% | ~60% est. |
| Branch coverage | `pytest --cov --cov-branch` | 70% | Unknown |
| Mutation score | `mutmut` | 75%+ | Not measured |
| E2E flow coverage | Manual tracking | 90% of critical paths | ~15% |
| Test suite runtime | `pytest` | <5 min (unit+int), <10 min (E2E) | Unknown |

### Mutation Score: The Gold Standard

> [!IMPORTANT]
> **Mutation score is the single most meaningful quality metric** for financial software. Line coverage of 80% can still miss critical bugs. A mutation score of 75%+ means your tests would catch 75%+ of real bugs in your reconciliation logic.

```bash
# Run mutation testing on critical module
mutmut run --paths-to-mutate=app/services/reconciliation_service.py

# Analyze results
mutmut results

# Feed surviving mutants to LLM for kill-test generation
mutmut show <id> | claude "Generate a pytest that would catch this mutation"
```

---

## Open Questions for You

> [!WARNING]
> **Before I proceed with implementation, please confirm:**

1. **Priority**: Should I start with Phase 1 (building the E2E framework + mutation testing) immediately, or do you want to discuss the approach further?

2. **Scope**: Do you want all 14 tabs covered in the initial E2E build, or should I prioritize the financial-critical flows first (reconciliation, installments, investments, suspended)?

3. **CI/CD**: Your GitHub Actions workflow was planned in the RALPH_TEST_PLAN but marked complete — is it actually running? Should I verify and enhance it?

4. **Environment**: For Playwright MCP (Phase 2), are you comfortable running `docker-compose up` + MCP server locally, or would you prefer a containerized solution?

5. **Mutation Testing Scope**: Should I run mutmut on the **entire backend** or start with just `reconciliation_service.py` and CRUD modules?
