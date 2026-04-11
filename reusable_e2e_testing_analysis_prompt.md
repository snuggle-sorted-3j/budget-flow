# Reusable Prompt Template: E2E Testing Strategy Analysis

> **Purpose**: Copy-paste this prompt into any AI coding assistant (Antigravity, Claude, Cursor, etc.) at the start of a new project to get a comprehensive E2E testing strategy analysis — both business and technical.
>
> **How to use**:
> 1. Fill in the `{{PLACEHOLDERS}}` with your project details
> 2. Delete any sections that don't apply
> 3. Paste the entire prompt into your AI assistant with access to the codebase
> 4. The assistant will audit your repo + produce a scored options analysis

---

## The Prompt

```
You are acting as a **Senior QA Strategist, Test Architect, and Business Analyst** for my project.
Your job is to provide a sophisticated, cutting-edge analysis of how to best deliver automated
end-to-end testing — as if designed by a world-class Playwright/Selenium automation engineer
with deep expertise in edge-case discovery and feature-based workflow testing.

────────────────────────────────────────────────────────────
PART 1: PROJECT CONTEXT
────────────────────────────────────────────────────────────

Project Name: {{PROJECT_NAME}}
Repository: @{{REPO_NAME}}   ← (tag your repo if the tool supports it)

Tech Stack:
- Backend: {{BACKEND_FRAMEWORK}} (e.g., FastAPI, Django, Express, Spring Boot)
- Frontend: {{FRONTEND_FRAMEWORK}} (e.g., Plotly Dash, React, Next.js, Vue, Angular)
- Database: {{DATABASE}} (e.g., PostgreSQL, MongoDB, MySQL)
- Auth: {{AUTH_METHOD}} (e.g., JWT + bcrypt, OAuth2, session-based)
- Deployment: {{DEPLOYMENT}} (e.g., Docker + AWS ECS, Vercel, self-hosted)
- Language(s): {{LANGUAGES}} (e.g., Python 3.11, TypeScript 5.x)

App Type & Domain:
- {{APP_TYPE}} (e.g., SaaS, internal tool, personal project, B2B platform)
- Domain: {{DOMAIN}} (e.g., fintech, e-commerce, healthcare, developer tools)
- Domain risk level: {{RISK_LEVEL}} (low / medium / high / critical)
  (High = financial calculations, medical data, security-sensitive)

Team & Scale:
- Team size: {{TEAM_SIZE}} (e.g., solo developer, 3-person team, 20+ engineers)
- Budget tier: {{BUDGET}} (e.g., bootstrapped/minimal, moderate, well-funded)
- Deployment frequency: {{DEPLOY_FREQ}} (e.g., daily, weekly, monthly)
- Target users: {{USER_COUNT}} (e.g., just me, <100 users, 10K+ users)

────────────────────────────────────────────────────────────
PART 2: CURRENT TESTING STATE
────────────────────────────────────────────────────────────

Existing test infrastructure (fill in what applies, delete the rest):

- Unit tests: {{UNIT_TEST_COUNT}} tests in {{UNIT_TEST_FRAMEWORK}}
  Coverage: ~{{UNIT_COVERAGE}}%

- Integration tests: {{INT_TEST_COUNT}} tests
  Coverage: ~{{INT_COVERAGE}}%

- E2E tests: {{E2E_TEST_COUNT}} tests using {{E2E_FRAMEWORK}}
  Coverage: ~{{E2E_COVERAGE}}% of user flows

- CI/CD: {{CI_STATUS}} (e.g., "GitHub Actions running unit+int", "none", "Jenkins")

- Known testing gaps:
  {{GAP_1}}
  {{GAP_2}}
  {{GAP_3}}

────────────────────────────────────────────────────────────
PART 3: FEATURE MAP (for E2E scoping)
────────────────────────────────────────────────────────────

List the major features / user flows that need E2E coverage:

Critical flows (must test):
1. {{CRITICAL_FLOW_1}} (e.g., "User registration → login → session management")
2. {{CRITICAL_FLOW_2}} (e.g., "Create order → payment → confirmation")
3. {{CRITICAL_FLOW_3}} (e.g., "Multi-currency reconciliation → finalization")

Important flows (should test):
4. {{IMPORTANT_FLOW_1}}
5. {{IMPORTANT_FLOW_2}}
6. {{IMPORTANT_FLOW_3}}

Nice-to-have flows:
7. {{NICE_FLOW_1}}
8. {{NICE_FLOW_2}}

Edge cases I'm worried about:
- {{EDGE_CASE_1}} (e.g., "race conditions on concurrent edits")
- {{EDGE_CASE_2}} (e.g., "zero-amount transactions")
- {{EDGE_CASE_3}} (e.g., "session expiry mid-workflow")

────────────────────────────────────────────────────────────
PART 4: ANALYSIS REQUEST
────────────────────────────────────────────────────────────

Please perform a FULL analysis covering both BUSINESS and TECHNICAL dimensions:

### A. CODEBASE AUDIT (Technical)

1. **Explore my repository** — read the project structure, existing tests, config
   files, CI/CD setup, and key application modules.

2. **Map the current test coverage** — identify exactly what IS and ISN'T tested
   at each layer (unit, integration, E2E, frontend).

3. **Identify critical gaps** — which features, edge cases, and business rules
   have zero or insufficient test coverage?

4. **Assess testability** — are there architectural issues that make testing hard?
   (e.g., tightly coupled code, missing IDs on UI elements, no test fixtures)

### B. OPTIONS ANALYSIS (Business + Technical)

Evaluate ALL of the following approaches (and any others you think are relevant):

1. **Hire a traditional QA automation engineer** (freelance or part-time)
   - Cost analysis (junior vs senior, hourly rates, ramp-up time)
   - Pros/cons for my team size and budget

2. **AI-built automation framework** (you / the AI assistant build it)
   - What would you build? (POM structure, test count, fixtures)
   - Cost = my existing subscription
   - Delivery timeline

3. **Playwright MCP + AI Agent** (autonomous test generation via MCP protocol)
   - How it works with accessibility tree
   - Self-healing capabilities
   - Cost per run

4. **Claude Computer Use / Perplexity Computer** (OS-level computer control)
   - True user simulation via screenshots
   - When this makes sense vs when it's overkill
   - Infrastructure requirements

5. **Cloud TaaS platforms** (TestMu AI / BrowserStack / Sauce Labs)
   - Cross-browser value for my use case
   - Pricing tiers
   - AI features (auto-healing, test generation)

6. **Managed QA services** (QA Wolf or similar)
   - Fully outsourced testing
   - Pricing and minimum engagement
   - When this makes sense

7. **Stagehand + BrowserBase** (intent-based browser automation)
   - Natural language testing
   - Infrastructure costs
   - Language ecosystem fit

8. **LLM-enhanced mutation testing** (mutmut / mutpy + LLM analysis)
   - How mutation testing measures test QUALITY not just coverage
   - LLM workflow for analyzing survivors and generating kill-tests
   - Cost and compute requirements

9. **Any other approaches** you think are relevant for my specific stack and scale

### C. SCORING MATRIX

Create a weighted comparison matrix with these criteria:
- **Cost** (25%) — total cost of ownership (setup + ongoing)
- **Time to value** (20%) — how fast can I get meaningful coverage
- **Coverage depth** (15%) — how much of my app gets tested
- **Edge-case discovery** (15%) — ability to find non-obvious bugs
- **Maintainability** (10%) — how much effort to keep tests green
- **Self-healing** (5%) — can tests auto-repair when UI changes
- **CI/CD integration** (5%) — how well it fits automated pipelines
- **Stack fit** (5%) — compatibility with my language/framework

Score each option 1-5 and compute weighted totals.

### D. RECOMMENDATION

Based on the scoring, recommend a **hybrid strategy** that:
1. Maximizes coverage per dollar spent
2. Prioritizes fastest ROI
3. Fits my team size and budget
4. Includes a phased rollout plan (Phase 1 / 2 / 3)
5. Specifies concrete quality metrics to track:
   - Line coverage targets
   - Branch coverage targets
   - Mutation score targets (if applicable)
   - E2E flow coverage percentage
   - Test suite runtime budgets

### E. QUALITY METRICS FRAMEWORK

For whichever approach you recommend, define:
- Which metrics to track (coverage, mutation score, flakiness rate, etc.)
- Target values for each metric
- Tools and commands to measure them
- How often to run each measurement
- How to integrate metrics into CI/CD gates

### F. OPEN QUESTIONS

List 3-5 questions you need me to answer before you can start implementation.

────────────────────────────────────────────────────────────
PART 5: OUTPUT FORMAT
────────────────────────────────────────────────────────────

Deliver the analysis as a well-structured artifact/document with:
- Executive summary (TL;DR)
- Current state assessment (with tables)
- Detailed option-by-option analysis (cost tables, pros/cons, architecture diagrams)
- Weighted scoring matrix (table format)
- Recommended hybrid strategy with phased roadmap
- Annual cost comparison table (recommended vs alternatives)
- Quality metrics framework
- Open questions for me

Use tables, mermaid diagrams, and code blocks where appropriate.
```

---

## Quick-Start Examples

### Example 1: React SaaS App

```
Project Name: InvoiceHero
Tech Stack:
- Backend: Node.js + Express
- Frontend: React 18 + Vite
- Database: PostgreSQL + Prisma ORM
- Auth: Clerk (third-party)
- Deployment: Vercel + Railway

App Type: B2B SaaS — invoice generation and payment tracking
Domain risk: Medium-High (financial calculations)
Team: 2 developers, moderate budget
Users: ~500 active

Existing tests: 40 Jest unit tests (~30% coverage), 0 E2E
CI: GitHub Actions runs Jest on PR

Critical flows:
1. Signup → create org → invite team
2. Create invoice → send → track payment → mark paid
3. Recurring invoice setup → auto-generation → notification

Edge cases: currency rounding, overdue payment state transitions, PDF rendering
```

### Example 2: Django Internal Tool

```
Project Name: WarehouseOps
Tech Stack:
- Backend: Django 5.1 + DRF
- Frontend: Django templates + HTMX + Alpine.js
- Database: PostgreSQL 16
- Auth: Django built-in + 2FA (django-otp)
- Deployment: Docker + on-prem Linux server

App Type: Internal warehouse management tool
Domain risk: Medium (inventory accuracy matters)
Team: Solo developer, minimal budget
Users: 15 warehouse staff

Existing tests: 80 pytest unit tests (~50% coverage), 5 Selenium E2E
CI: None (manual pytest before deploy)

Critical flows:
1. Login with 2FA → dashboard access
2. Receive shipment → scan barcodes → update inventory
3. Pick order → verify qty → ship → update status

Edge cases: barcode scan failures, negative inventory, concurrent picks
```

### Example 3: Mobile-First Next.js App

```
Project Name: FitTrack
Tech Stack:
- Backend: Next.js API routes + tRPC
- Frontend: Next.js 14 + Tailwind + shadcn/ui
- Database: Supabase (PostgreSQL)
- Auth: Supabase Auth (magic link + Google OAuth)
- Deployment: Vercel

App Type: Consumer fitness tracking app
Domain risk: Low-Medium (personal data, no financial)
Team: Solo developer, bootstrapped
Users: ~2,000 (growing)

Existing tests: 20 Vitest unit tests, 0 E2E
CI: Vercel preview deploys only

Critical flows:
1. Magic link signup → onboarding wizard → first workout log
2. Log workout → view progress chart → share achievement
3. Subscription upgrade → Stripe checkout → premium features unlock

Edge cases: offline mode sync, timezone issues across travel, Stripe webhook failures
```

---

## Customization Tips

### Adjust Weights for Your Context

If you're a **funded startup with paying customers**, shift weights:
```
Cost: 15% (less important)
Coverage depth: 25% (more important)
CI/CD integration: 10% (critical for team velocity)
```

If you're a **solo developer on a budget**, keep defaults:
```
Cost: 25%
Time to value: 20%
```

If you're building **mission-critical software** (medical, aviation, finance):
```
Edge-case discovery: 25%
Coverage depth: 20%
Cost: 10%
```

### Add Domain-Specific Sections

For **fintech/payments**: Add a section on:
- Decimal precision testing (rounding, floating point)
- Idempotency verification
- Concurrency/race condition tests
- Regulatory compliance checks

For **healthcare**: Add:
- HIPAA compliance testing
- PHI data exposure checks
- Audit trail verification
- Access control boundary tests

For **e-commerce**: Add:
- Cart state management
- Payment gateway integration tests
- Inventory consistency under load
- Discount/coupon edge cases

### Add Emerging Tools as They Appear

The AI testing landscape evolves fast. Add new options as they emerge:
```
10. **{{NEW_TOOL_NAME}}** ({{brief description}})
    - How it works
    - Cost model
    - Fit for my project
```

---

## Prompt Maintenance Log

| Date | Change | Reason |
|------|--------|--------|
| 2026-04-07 | Initial version | Created from BudgetFlow analysis |
| | | |
| | | |

---

## Notes

- This prompt works best when the AI assistant has **direct access to your codebase**
  (via repo tagging, file browsing, or a code index).
- If the assistant can't access your code, paste your `project structure tree`,
  `package.json`/`requirements.txt`, and a sample test file into the prompt.
- The prompt is designed to be **model-agnostic** — works with Claude, GPT, Gemini,
  or any agent-capable LLM.
- For best results, run this at the **start of a project** (before writing tests)
  or at a **quality milestone** (before launch, after major refactor).
