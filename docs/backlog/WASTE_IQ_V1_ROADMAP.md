# Waste-IQ V1.0 Roadmap Backlog

> Working backlog for the **Waste-IQ v1.0 Production Release**.
> Owner: Technical PM / Architecture. Status: `DRAFT — pending review` (rev. 2).

This backlog splits the remaining work for the v1.0 release into five
milestones:

1. **Milestone 0 — Engineering Productivity** (AI engineering agents + project governance)
2. **Milestone 1 — Production Readiness** (security, observability, deployment hardening)
3. **Milestone 2 — Public Beta** (launch platform: staging, domain, SSL, beta feedback)
4. **Milestone 3 — Real-Time Features** (WebSocket delivery, tracking, live marketplace)
5. **Milestone 4 — AI Platform** (Computer Vision, AI Intelligence, MLOps)

Completed functionality is tracked separately in
[Completed Features](#completed-features) and is **not** re-planned here.

---

## Legend

| Field | Values |
| --- | --- |
| Priority | `Critical` / `High` / `Medium` / `Low` |
| Complexity | `XS` / `S` / `M` / `L` / `XL` |
| Effort | Estimated working days (0.5–3 per issue) |
| Status | `Not started` / `In progress` / `Done` / `Exists — audit only` |

### Labels

`backend` · `frontend` · `infrastructure` · `devops` · `auth` · `security` ·
`ai` · `analytics` · `mlops` · `enhancement` · `testing` · `documentation` ·
`high priority` · `good first issue`

### Dependencies

Each issue lists prerequisite issue IDs. `WIQ-V1-###` is the canonical ID to
be used as the GitHub issue number when created.

---

## Implementation Order (priority sequence)

**Milestone 0 — Engineering Productivity**

1.  WIQ-V1-001 GitHub AI Engineering Agent
2.  WIQ-V1-002 AI PR Review Agent
3.  WIQ-V1-003 AI Issue Generator
4.  WIQ-V1-004 AI Documentation Agent
5.  WIQ-V1-005 AI Test Generation Agent
6.  WIQ-V1-006 GitHub Project Board
7.  WIQ-V1-007 Issue Templates (refine existing)
8.  WIQ-V1-008 Pull Request Templates (refine existing)
9.  WIQ-V1-009 CODEOWNERS (refine existing)
10. WIQ-V1-010 Branch Protection Rules
11. WIQ-V1-011 Semantic Versioning
12. WIQ-V1-012 Release Automation

**Milestone 1 — Production Readiness**

13. WIQ-V1-013 Refresh Token Authentication
14. WIQ-V1-014 Email Verification (email delivery foundation)
15. WIQ-V1-015 Forgot & Reset Password
16. WIQ-V1-016 Password Change
17. WIQ-V1-017 Rate Limiting & Account Lockout
18. WIQ-V1-018 Audit Logging
19. WIQ-V1-019 Login History
20. WIQ-V1-022 Docker Production Deployment
21. WIQ-V1-023 Monitoring & Logging
22. WIQ-V1-021 Background Jobs
23. WIQ-V1-020 Cloud Storage Hardening

**Milestone 2 — Public Beta**

24. WIQ-V1-024 Staging Environment & Deploy Pipeline
25. WIQ-V1-025 Custom Domain & SSL
26. WIQ-V1-026 Production Go-Live
27. WIQ-V1-027 Beta Feedback & Triage Workflow
28. WIQ-V1-028 Beta Program Instrumentation

**Milestone 3 — Real-Time Features**

29. WIQ-V1-029 Real-Time Notification Delivery
30. WIQ-V1-030 Live Collector Tracking & Presence
31. WIQ-V1-031 Live Marketplace Updates

**Milestone 4 — AI Platform**

32. WIQ-V1-032 Waste Image Classification (real inference)
33. WIQ-V1-033 Waste Quality Assessment
34. WIQ-V1-039 MLflow Experiment Tracking
35. WIQ-V1-034 Plastic Price Prediction
36. WIQ-V1-035 Dealer Demand Forecasting
37. WIQ-V1-040 Model Registry
38. WIQ-V1-042 Model Retraining Pipeline
39. WIQ-V1-041 Model Monitoring
40. WIQ-V1-036 Real Route Optimization
41. WIQ-V1-038 AI Analytics Dashboard
42. WIQ-V1-037 AI Assistant

---

## Completed Features

The following are implemented, in production, and **excluded** from this
backlog unless the issue text explicitly calls out an improvement.

### Authentication & Access
- Login / Registration / JWT auth / role-based authorization (`require_roles`)
- Admin bootstrap from environment variables

### Citizen Portal
- Dashboard, pickup request submission (multipart + image), pickup timeline,
  pickup images (`image_url`), pickup status lifecycle & events

### Collector Portal
- Assigned pickups, full lifecycle (accept → start → collect → complete with
  weight), live collector map, GPS location upload + history

### Dealer Portal
- Dealer profile, business verification, GST/license upload, approval workflow,
  inventory management (admin + dealer side)

### Marketplace
- Inventory browsing, search, filters, 24h reservation, purchase flow, orders,
  transactions, reservation expiry handling (lazy), `InventoryLotEvent` audit

### Notifications
- In-app notification engine, notification center, mark read/delete,
  broadcast notifications (`NotificationDispatcher` / `Broadcaster`)

### Admin Portal
- Dashboard, analytics KPIs, user management, dealer review queue

### Cross-Cutting (already present)
- Backend pytest suite, frontend Vitest + MSW suite, CI passing
  (`backend-ci.yml`, `frontend-ci.yml`), README / CHANGELOG / API spec /
  architecture docs, Cloudinary image upload with dev fallback, greedy
  nearest-neighbour multi-stop route optimizer (`services/routing.py`),
  AI classifier interface wired (stub returns `Unknown`/`0.0`)
- GitHub issue templates (bug/feature/task), PR template, CODEOWNERS
  (exist — refined in WIQ-V1-007/008/009)

---

## Milestone 0 — Engineering Productivity

**Goal:** Stand up AI engineering agents on GitHub Actions and the project
governance rails (board, templates, protection, releases) so all later
milestones flow through repeatable, agent-assisted process.

### Epic 0.1 — AI Engineering Agents

> Uses the opencode GitHub integration (`anomalyco/opencode/github@latest`).
> Requires installing the opencode GitHub App on this repository and storing
> the LLM provider API key in Actions secrets. Each agent ships its own
> `.github/workflows/opencode-*.yml` workflow.

#### WIQ-V1-001 — GitHub AI Engineering Agent

- **Labels:** `ai`, `devops`, `infrastructure`, `high priority`
- **Priority:** High  ·  **Complexity:** M  ·  **Effort:** 2d
- **Status:** Not started
- **Dependencies:** None

**Description**
The repo currently has no way to execute development tasks from GitHub — no
`/opencode` or `/oc` handling, no opencode workflow, no GitHub App installed.
The Engineering Agent is the foundation for the other four agents in this
epic: it lets the team delegate implementation tasks (fix, refactor, feature)
from issues and PR comments, running on GitHub Actions runners and opening
branches/PRs itself.

**Acceptance Criteria**
- [ ] opencode GitHub App installed on the repository
- [ ] LLM provider API key stored as a repo/org Actions secret
- [ ] `.github/workflows/opencode.yml` — `issue_comment` + `pull_request_review_comment` triggers on `/opencode` or `/oc`
- [ ] Agent can create a branch, implement a change, and open a PR from an issue comment
- [ ] Agent can review specific code lines from PR Files-tab comments
- [ ] Working demo documented: `/opencode fix <issue>` flow verified end-to-end
- [ ] `AGENTS.md` project guide committed so the agent follows repo conventions

**Technical Notes**
- Modules: `.github/workflows/opencode.yml`, repo Settings → GitHub Apps, Actions secrets; project `AGENTS.md`
- Triggered via issue/PR comments; uses `issue_comment` and `pull_request_review_comment` events
- Docs: `CONTRIBUTING.md` + `docs/SYSTEM_ARCHITECTURE.md` (agent usage section)
- Testing: manual E2E on a test issue; no unit tests needed

#### WIQ-V1-002 — AI PR Review Agent

- **Labels:** `ai`, `devops`, `infrastructure`, `enhancement`
- **Priority:** High  ·  **Complexity:** S  ·  **Effort:** 1d
- **Status:** Not started
- **Dependencies:** WIQ-V1-001

**Description**
No automated code review exists today; PR review depends entirely on human
reviewers. An agent that automatically reviews opened/updated PRs (bugs,
security, style per project conventions) increases review throughput.

**Acceptance Criteria**
- [ ] `.github/workflows/opencode-review.yml` — `pull_request` trigger (`opened`, `synchronize`, `reopened`, `ready_for_review`)
- [ ] Review prompt: code quality, potential bugs, security, alignment with `AGENTS.md`/`CONVENTIONS.md`
- [ ] Review posted as a PR comment; `GITHUB_TOKEN` used for read scope (no write permissions)
- [ ] Model overridable via workflow input/env
- [ ] Works with Dependabot PRs (skip or review based on policy)
- [ ] Verified on a test PR; findings documented in README

**Technical Notes**
- Modules: `.github/workflows/opencode-review.yml`
- Uses `pull_request` events; permissions: `contents: read`, `pull-requests: read`, `issues: read`
- Docs: `CONTRIBUTING.md`
- Testing: manual on sample PR; JSON/prompt smoke check

#### WIQ-V1-003 — AI Issue Generator

- **Labels:** `ai`, `devops`, `enhancement`
- **Priority:** Medium  ·  **Complexity:** S  ·  **Effort:** 1d
- **Status:** Not started
- **Dependencies:** WIQ-V1-001

**Description**
Backlog items and operational feedback currently require manual issue writing.
An agent that drafts structured GitHub issues from the roadmap document, TODO
scans, or triage notes keeps the board populated with consistent formatting
(acceptance criteria, labels, priorities).

**Acceptance Criteria**
- [ ] Workflow (`workflow_dispatch` + optional `schedule`) runs the agent against `docs/backlog/WASTE_IQ_V1_ROADMAP.md` and TODO markers
- [ ] Generated issues use the repo issue templates (fields: title, description, acceptance criteria, labels, priority)
- [ ] Dry-run mode prints issues to workflow logs instead of creating (safety gate)
- [ ] Dedupes against existing open issues (title matching)
- [ ] `issues: write` permission scoped to this workflow only

**Technical Notes**
- Modules: `.github/workflows/opencode-issue-generator.yml`; prompt referencing `docs/backlog/`, `.github/ISSUE_TEMPLATE/`
- Docs: `CONTRIBUTING.md`
- Testing: manual dispatch with dry-run, then a real issue on the backlog

#### WIQ-V1-004 — AI Documentation Agent

- **Labels:** `ai`, `devops`, `documentation`
- **Priority:** Medium  ·  **Complexity:** S  ·  **Effort:** 1d
- **Status:** Not started
- **Dependencies:** WIQ-V1-001

**Description**
`docs/` (API spec, architecture, database schema) drifts as code changes; the
README/CHANGELOG are updated manually. An agent that regenerates and diffs
documentation keeps them current without a dedicated docs sprint.

**Acceptance Criteria**
- [ ] Workflow (dispatch + schedule) runs the agent to review `backend/app`, `frontend/src`, migrations against `docs/`
- [ ] Agent opens a PR with doc updates (API endpoints, models, env vars, CHANGELOG entries)
- [ ] CHANGELOG entries follow the existing style (`CHANGELOG.md`)
- [ ] Skip-on-no-changes behavior (no empty PRs)
- [ ] `contents: write` scoped to this workflow

**Technical Notes**
- Modules: `.github/workflows/opencode-docs.yml`; sources: `docs/API_SPECIFICATION.md`, `docs/DATABASE_SCHEMA.md`, `docs/SYSTEM_ARCHITECTURE.md`, `CHANGELOG.md`
- Testing: manual dispatch; diff review

#### WIQ-V1-005 — AI Test Generation Agent

- **Labels:** `ai`, `testing`, `devops`, `enhancement`
- **Priority:** Medium  ·  **Complexity:** S  ·  **Effort:** 1d
- **Status:** Not started
- **Dependencies:** WIQ-V1-001

**Description**
Backend coverage exists (pytest) but new code often ships without tests;
frontend test patterns (`Vitest` + `MSW`) need consistent application. An
agent that generates tests for changed code — in the existing repo style —
raises coverage as features land.

**Acceptance Criteria**
- [ ] Workflow runs on PR (or dispatch) with a prompt that analyzes the diff and existing test conventions
- [ ] Generated tests follow repo patterns (`backend/tests/conftest.py` fixtures, `frontend/src/test/` MSW setup)
- [ ] Agent opens a PR with the tests; CI (`backend-ci.yml`, `frontend-ci.yml`) must pass
- [ ] Skip when diff is test-only
- [ ] Coverage delta reported in the PR comment

**Technical Notes**
- Modules: `.github/workflows/opencode-tests.yml`
- Testing: manual on a sample PR with a deliberate missing-test gap

### Epic 0.2 — Project Management & Governance

> Issue templates, PR template, and CODEOWNERS already exist
> (`.github/ISSUE_TEMPLATE/*`, `.github/PULL_REQUEST_TEMPLATE.md`,
> `.github/CODEOWNERS`) — those issues are **refine/audit only**, not
> greenfield. The genuinely new items are the project board, branch
> protection, semantic versioning, and release automation.

#### WIQ-V1-006 — GitHub Project Board

- **Labels:** `devops`, `documentation`
- **Priority:** Medium  ·  **Complexity:** M  ·  **Effort:** 2d
- **Status:** Not started
- **Dependencies:** None

**Description**
There is no GitHub Project board tracking work; the backlog lives only in
`docs/backlog/`. A project board with milestone views (Engineering
Productivity, Production Readiness, Public Beta, Real-Time, AI Platform)
makes status visible and supports the milestone-by-milestone issue creation
plan.

**Acceptance Criteria**
- [ ] Project (v2) board created with columns: Backlog, To Do, In Progress, In Review, Done
- [ ] Milestone views (or group-by-milestone) for the five v1.0 milestones
- [ ] Automation: newly opened v1.0 issues land in Backlog; PR merged → move to Done
- [ ] Board link documented in README/roadmap
- [ ] Labels used by issues (priority, area) reflected in board grouping

**Technical Notes**
- Modules: GitHub Project settings; optional `.github/workflows/project-automation.yml`
- Docs: `docs/backlog/WASTE_IQ_V1_ROADMAP.md` (board link)
- Testing: manual board walkthrough

#### WIQ-V1-007 — Refine GitHub Issue Templates

- **Labels:** `documentation`, `good first issue`
- **Priority:** Medium  ·  **Complexity:** XS  ·  **Effort:** 0.5d
- **Status:** Exists — audit only
- **Dependencies:** WIQ-V1-006

**Description**
Templates exist (`bug_report.md`, `feature_request.md`, `task.md`) but are
not aligned with the backlog's standard fields (labels, priority, complexity,
acceptance criteria). Align them so the AI Issue Generator (WIQ-V1-003) and
humans produce consistent issues.

**Acceptance Criteria**
- [ ] Templates include sections: Description, Acceptance Criteria, Technical Notes, Dependencies, Labels, Priority, Complexity
- [ ] Bug/feature/task templates updated; `config.yml` chooser reviewed
- [ ] Verified that WIQ-V1-003 output matches template shape

**Technical Notes**
- Modules: `.github/ISSUE_TEMPLATE/*.md`
- Testing: manual template walkthrough

#### WIQ-V1-008 — Refine Pull Request Template

- **Labels:** `documentation`, `good first issue`
- **Priority:** Medium  ·  **Complexity:** XS  ·  **Effort:** 0.5d
- **Status:** Exists — audit only
- **Dependencies:** WIQ-V1-010

**Description**
The PR template exists but should require linked issue, testing notes, and
migration/database change notes so reviewers (human and agent WIQ-V1-002)
get consistent context.

**Acceptance Criteria**
- [ ] Template fields: linked issue, description, testing performed, migrations, screenshots (UI)
- [ ] Matches the AI PR Review Agent's expectations (WIQ-V1-002)

**Technical Notes**
- Modules: `.github/PULL_REQUEST_TEMPLATE.md`
- Testing: manual

#### WIQ-V1-009 — Refine CODEOWNERS

- **Labels:** `documentation`, `good first issue`
- **Priority:** Low  ·  **Complexity:** XS  ·  **Effort:** 0.5d
- **Status:** Exists — audit only
- **Dependencies:** WIQ-V1-008

**Description**
CODEOWNERS exists but its coverage of `backend/`, `frontend/`, `docs/`, and
`.github/` should be verified so branch protection can require reviews from
the right people/teams.

**Acceptance Criteria**
- [ ] CODEOWNERS maps owners for `backend/`, `frontend/`, `docs/`, `.github/`
- [ ] Verified against the current team's GitHub usernames/teams

**Technical Notes**
- Modules: `.github/CODEOWNERS`
- Testing: manual

#### WIQ-V1-010 — Branch Protection Rules

- **Labels:** `devops`, `security`
- **Priority:** High  ·  **Complexity:** S  ·  **Effort:** 1d
- **Status:** Not started
- **Dependencies:** WIQ-V1-009 (CODEOWNERS) and existing CI

**Description**
`main`/`develop` currently allow direct pushes; nothing enforces review or CI
passing. Enforce branch protection so agents and humans land changes safely.

**Acceptance Criteria**
- [ ] Protection on `main` (and `develop`): require PR, require ≥1 review (or CODEOWNERS), require CI checks to pass (`backend-ci`, `frontend-ci`)
- [ ] No direct pushes to `main`; admins opt in
- [ ] Dependabot/agent PRs exempted from human review where appropriate
- [ ] Documented in `CONTRIBUTING.md`

**Technical Notes**
- Modules: repo Settings → Branch protection rules (or `.github` config via GitHub API/terraform if used)
- Testing: manual push-attempt verification

#### WIQ-V1-011 — Semantic Versioning

- **Labels:** `devops`, `documentation`
- **Priority:** Medium  ·  **Complexity:** S  ·  **Effort:** 1d
- **Status:** Not started
- **Dependencies:** WIQ-V1-010

**Description**
The repo uses ad-hoc versions (`1.0.0` in `package.json`/FastAPI title, and
the recent `v0.2.0` milestone tag) without a documented bump policy. Adopt
SemVer across backend/frontend so releases and `CHANGELOG.md` stay aligned.

**Acceptance Criteria**
- [ ] SemVer policy documented (major/minor/patch rules for this project)
- [ ] Version bumped consistently in `frontend/package.json` and FastAPI app version
- [ ] CHANGELOG uses the existing style with `Unreleased` → release version promotion
- [ ] Tag format `vX.Y.Z` documented and used

**Technical Notes**
- Modules: `frontend/package.json`, `backend/app/main.py` (app version), `CHANGELOG.md`, docs
- Docs: `CONTRIBUTING.md` (release process)
- Testing: manual tag/bump run

#### WIQ-V1-012 — Release Automation

- **Labels:** `devops`, `infrastructure`, `testing`
- **Priority:** High  ·  **Complexity:** M  ·  **Effort:** 2d
- **Status:** Not started
- **Dependencies:** WIQ-V1-011

**Description**
Releases are manual (tag + GitHub Release notes by hand). Automate tag-driven
release creation: changelog extraction, GitHub Release, and (later) deploy
hooks into Milestone 2.

**Acceptance Criteria**
- [ ] Workflow on `v*` tag: validates version consistency, runs full CI (backend + frontend), creates GitHub Release from `CHANGELOG.md`
- [ ] Release notes include the changelog section for that version
- [ ] Rollback/documentation notes in `CONTRIBUTING.md`
- [ ] Dry-run mode for validation

**Technical Notes**
- Modules: `.github/workflows/release.yml`; uses `softprops/action-gh-release` or `gh` CLI
- Docs: `CONTRIBUTING.md`, `docs/DEPLOYMENT_GUIDE.md`
- Testing: tag on a branch + release created in dry-run first

---

## Milestone 1 — Production Readiness

**Goal:** Secure the auth lifecycle, add operational visibility, and harden
deployment so the marketplace can be operated safely in production.

### Epic 1.1 — Authentication & Account Security

#### WIQ-V1-013 — Implement Refresh Token Authentication

- **Labels:** `auth`, `security`, `backend`, `frontend`, `high priority`
- **Priority:** Critical  ·  **Complexity:** L  ·  **Effort:** 3d
- **Status:** Not started
- **Dependencies:** None

**Description**
The backend issues a single JWT access token with a 24-hour expiry
(`app/core/security.py:create_access_token`,
`config.py:access_token_expire_minutes`) and no mechanism to obtain a new one,
forcing re-login. The frontend already ships refresh-token plumbing
(`frontend/src/api/client.ts`: `REFRESH_TOKEN_STORAGE_KEY`,
`configureRefreshHandler`, inflight-refresh dedupe, 401 retry) but no handler
is registered and there is no backend refresh endpoint. Short-lived access
tokens with rotating refresh tokens are required before v1.0, and support
"log out all devices."

**Acceptance Criteria**
- [ ] `RefreshToken` model (opaque token hash, user, device/UA, expires_at, revoked_at, replaced_by) with Alembic migration
- [ ] `POST /auth/refresh` — validates refresh token, rotates it (revoke old, issue new), returns fresh access + refresh token
- [ ] Reuse detection: a rotated/replayed token is rejected and revokes the token family
- [ ] `POST /auth/logout` (current session) and `POST /auth/logout-all` (revoke every session)
- [ ] Shorten `access_token_expire_minutes` (15–30 min); add `refresh_token_expire_days` setting
- [ ] Register refresh handler in `AuthProvider` (`AuthContext.tsx`); login/register return `refresh_token`
- [ ] Skip auth on `/auth/refresh`; concurrency race-guard already in client preserved
- [ ] Backend unit tests (rotation, reuse detection, expiry, logout variants) + frontend tests extending `src/test/axios.test.ts`

**Technical Notes**
- Modules: `app/core/security.py`, `app/services/auth.py`, `app/api/routes/auth.py`, `app/schemas/auth.py`, new `RefreshToken` model; `frontend/src/context/AuthContext.tsx`, `frontend/src/api/client.ts`, `frontend/src/api/auth.ts`
- **DB migration required** (new `refresh_tokens` table)
- Frontend pages: none (session persistence + interceptor)
- Docs: `docs/API_SPECIFICATION.md`
- Testing: pytest service/route; Vitest + MSW handler for `/auth/refresh`

#### WIQ-V1-014 — Implement Email Verification

- **Labels:** `auth`, `backend`, `frontend`, `security`, `infrastructure`, `high priority`
- **Priority:** High  ·  **Complexity:** L  ·  **Effort:** 3d
- **Status:** Not started
- **Dependencies:** None

**Description**
Accounts are usable immediately after registration with no proof the email is
real — an abuse vector pre-launch and a marketplace-trust gap. This issue also
establishes the shared email delivery service (SMTP provider + HTML
templating) that WIQ-V1-015 reuses.

**Acceptance Criteria**
- [ ] `app/services/email.py` with an SMTP provider, dev no-op/console backend, and settings (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_FROM`, `EMAIL_FROM_NAME`)
- [ ] `users.email_verified_at` (nullable) + `email_verified` property
- [ ] `POST /auth/verify-email` — signed one-time token (`purpose="email_verify"`), sets `email_verified_at`
- [ ] `POST /auth/resend-verification` — rate-limited, resends token
- [ ] Registration emails a verification link; `GET /auth/me` exposes `email_verified`
- [ ] Optional gate: verified email required before dealer `reserve`/`purchase` (`app/services/inventory_marketplace.py`)
- [ ] Frontend: verification banner + `VerifyEmailPage` + resend action
- [ ] Backend unit tests + frontend tests

**Technical Notes**
- Modules: new `app/services/email.py`, `app/services/templates/` (add `jinja2`); `app/models/user.py`, `app/schemas/user.py`, `app/services/auth.py`, `app/core/config.py`
- **DB migration required** (new column)
- Templates for verification, reset, notification emails
- Docs: README env vars + `API_SPECIFICATION.md`
- Testing: pytest (token lifecycle, idempotent re-verify, gating) + Vitest

#### WIQ-V1-015 — Implement Forgot & Reset Password

- **Labels:** `auth`, `security`, `backend`, `frontend`, `high priority`
- **Priority:** High  ·  **Complexity:** M  ·  **Effort:** 2d
- **Status:** Not started
- **Dependencies:** WIQ-V1-014 (email delivery foundation)

**Description**
No password recovery path exists, and there is no email-sending infrastructure
anywhere in the project. Adds a tokenized forgot/reset flow built on the email
delivery module introduced by WIQ-V1-014.

**Acceptance Criteria**
- [ ] `POST /auth/forgot-password` — always 200 (no account enumeration); emails a one-time reset link/token when the address exists
- [ ] `POST /auth/reset-password` — validates token, enforces the 8–64 char rule, updates hash, revokes all sessions
- [ ] Reset tokens single-use, ≤30 min expiry, invalidated on use
- [ ] Invalid/expired token returns a generic 400
- [ ] Frontend: `ForgotPasswordPage` + `ResetPasswordPage` (React Hook Form + Zod), public routes
- [ ] Backend + frontend tests (MSW handlers)

**Technical Notes**
- Modules: `app/core/security.py`, `app/services/auth.py`, `app/schemas/auth.py`, email module (from WIQ-V1-014); frontend routes `/forgot-password`, `/reset-password`
- No new table (signed JWT with `purpose="password_reset"`); session revocation via WIQ-V1-013
- Rate-limit endpoints (WIQ-V1-017)
- Docs: README security notes + `API_SPECIFICATION.md`
- Testing: pytest (expiry, reuse, enumeration-safe) + Vitest

#### WIQ-V1-016 — Implement Password Change

- **Labels:** `auth`, `backend`, `frontend`
- **Priority:** Medium  ·  **Complexity:** XS  ·  **Effort:** 1d
- **Status:** Not started
- **Dependencies:** WIQ-V1-013

**Description**
Authenticated users cannot rotate their password from settings; only the
out-of-band forgot/reset path (WIQ-V1-015) exists.

**Acceptance Criteria**
- [ ] `POST /auth/change-password` (`current_password`, `new_password`) — verifies current, validates 8–64 rule, hashes, revokes all other sessions, keeps current
- [ ] Optional `notify_system` security notification
- [ ] Frontend: password section in `RoleSettingsPage`
- [ ] Backend + frontend tests

**Technical Notes**
- Modules: `app/services/auth.py`, `app/api/routes/auth.py`, `app/schemas/auth.py`, `frontend/src/pages/dashboard/RoleSettingsPage.tsx`
- No DB change
- Docs: `API_SPECIFICATION.md`
- Testing: pytest + Vitest

#### WIQ-V1-017 — Implement Rate Limiting & Account Lockout

- **Labels:** `security`, `backend`, `auth`, `infrastructure`, `high priority`
- **Priority:** High  ·  **Complexity:** M  ·  **Effort:** 2d
- **Status:** Not started
- **Dependencies:** WIQ-V1-018

**Description**
Auth and public endpoints accept unlimited requests — login/register/forgot/
resend are open to brute force and abuse; there is no lockout protection.

**Acceptance Criteria**
- [ ] Rate limiting on auth endpoints (login, register, forgot-password, resend-verification) — per-IP and per-account, `429` + `Retry-After`
- [ ] Account lockout: 5 failed logins → lock with cooldown; `users.locked_until` recorded; counter resets on success
- [ ] Auth limiter does not break `/auth/refresh` or CORS preflight
- [ ] Frontend surfaces 429 errors (extend `lib/api-error.ts`)
- [ ] Tune via settings; backend tests (429, lockout window, reset on success, IP × account)

**Technical Notes**
- Modules: `app/core/config.py`, `app/api/routes/auth.py`, `app/services/auth.py`, `app/models/user.py`, new `app/core/ratelimit.py` (slowapi or in-memory sliding window; note multi-instance limitation, optional Redis)
- **DB migration required** (`users.locked_until`, `users.failed_login_count`)
- Docs: README settings + `API_SPECIFICATION.md` (429 contract)
- Testing: pytest

#### WIQ-V1-018 — Implement Audit Logging

- **Labels:** `infrastructure`, `security`, `backend`, `high priority`
- **Priority:** High  ·  **Complexity:** M  ·  **Effort:** 2d
- **Status:** Not started
- **Dependencies:** None

**Description**
Domain event tables exist (`pickup_request_events`, `inventory_lot_events`,
`dealer_profile_events`) but there is no general, append-only audit trail for
security-relevant and admin actions (admin mutations, approval decisions, auth
events, sensitive reads).

**Acceptance Criteria**
- [ ] `audit_logs` table (actor_user_id, action, resource, resource_id, before/after JSON, ip_address, user_agent, created_at) — append-only
- [ ] `AuditService` + middleware/dependency recording mutating admin and auth actions (register, login success/failure, dealer approve/reject, inventory archive, broadcast)
- [ ] Request IP/UA captured (middleware / `get_current_user`)
- [ ] `GET /admin/audit-logs` — paginated, filterable by actor/action/resource/date, admin-only
- [ ] Optional: admin audit viewer page (read-only)
- [ ] Backend unit tests

**Technical Notes**
- Modules: new `app/models/audit_log.py`, `app/services/audit.py`, `app/repositories/audit.py`, `app/api/routes/admin.py`, `app/core/dependencies.py`
- **DB migration required** (new table + index)
- Writes synchronous with the triggering transaction
- Docs: `DATABASE_SCHEMA.md`, `API_SPECIFICATION.md`, `SYSTEM_ARCHITECTURE.md`
- Testing: pytest

#### WIQ-V1-019 — Implement Login History

- **Labels:** `auth`, `backend`, `frontend`, `enhancement`
- **Priority:** Medium  ·  **Complexity:** S  ·  **Effort:** 1d
- **Status:** Not started
- **Dependencies:** WIQ-V1-018

**Description**
No visibility into who logged into an account, when, and from where — required
for detecting compromised accounts.

**Acceptance Criteria**
- [ ] Record every login attempt (success/failure): user, IP, user-agent/device, timestamp, outcome — via the WIQ-V1-018 audit infrastructure
- [ ] `GET /auth/login-history` — own recent logins (paginated)
- [ ] `GET /admin/login-history` — all users, filterable
- [ ] Frontend: "Recent logins" card on `RoleSettingsPage`
- [ ] Backend + frontend tests

**Technical Notes**
- Modules: `app/services/auth.py`, `app/services/audit.py`, `app/api/routes/auth.py`, `app/api/routes/admin.py`, `RoleSettingsPage.tsx`
- No new table if WIQ-V1-018 ships (query `audit_logs` where `action LIKE 'login%'`)
- Docs: `API_SPECIFICATION.md`
- Testing: pytest + Vitest

### Epic 1.2 — Platform Operations

#### WIQ-V1-020 — Production-Harden Cloud Image Storage

- **Labels:** `infrastructure`, `backend`, `enhancement`
- **Priority:** Medium  ·  **Complexity:** S  ·  **Effort:** 1d
- **Status:** Not started
- **Dependencies:** None

**Description**
Cloudinary is already integrated (`app/services/upload.py`) with type/size
validation (jpg/jpeg/png/webp, 10 MB) and dev fallback. Remaining v1.0 gaps:
assets orphan on cancellation, no per-user organization, production
enforcement is a soft flag.

**Acceptance Criteria**
- [ ] Delete the Cloudinary asset when a pickup request is cancelled (store `public_id`, call `delete_resources`)
- [ ] Upload to per-user folder prefixes (`pickups/{user_id}/{uuid}`), standardized filenames
- [ ] Verify production raises 503/502 correctly (`app/main.py` handlers); document required env vars
- [ ] Keep the `ImageUploader` protocol so S3/R2 (boto3) can be swapped later; ADR note in `SYSTEM_ARCHITECTURE.md`
- [ ] Backend tests (cancel cleanup, folder prefixing, size/type rejection)

**Technical Notes**
- Modules: `app/services/upload.py`, `app/services/pickup_request_images.py`, `app/services/pickup_requests.py` (cancel), `app/core/config.py`
- No migration required (store `public_id` in existing column or a new nullable column)
- Docs: `DEPLOYMENT_GUIDE.md`, `SYSTEM_ARCHITECTURE.md`
- Testing: pytest

#### WIQ-V1-021 — Implement Background Jobs

- **Labels:** `infrastructure`, `backend`, `high priority`
- **Priority:** High  ·  **Complexity:** M  ·  **Effort:** 2d
- **Status:** Not started
- **Dependencies:** WIQ-V1-014 (email dispatch), WIQ-V1-022 (runs in the Docker image)

**Description**
Time-driven work is handled lazily on request (reservation expiry re-checked on
browse/reserve in `app/services/inventory_marketplace.py`). No scheduler or
queue exists. Needed: reservation expiry sweep, email dispatch, aging-pickup
alerts.

**Acceptance Criteria**
- [ ] In-process APScheduler started in FastAPI lifespan + `BackgroundTasks` for on-request email dispatch
- [ ] Scheduled job: expire stale reservations → release lot, emit `reservation_expired` (reuse `NotificationDispatcher`)
- [ ] Scheduled job: detect aging `pending`/`accepted` pickups → notify admins
- [ ] Idempotent, configurable, disabled in tests; last-run visibility via admin endpoint/logs
- [ ] Document Celery + Redis upgrade path for multi-instance
- [ ] Backend unit tests per job (run synchronously in tests)

**Technical Notes**
- Modules: new `app/services/jobs.py`, `app/services/inventory_marketplace.py` (extract sweep), `app/services/notifications.py`, `app/main.py`; add `apscheduler`
- No DB change
- Docs: `SYSTEM_ARCHITECTURE.md`, `DEPLOYMENT_GUIDE.md`
- Testing: pytest

#### WIQ-V1-022 — Docker Production Deployment

- **Labels:** `infrastructure`, `devops`, `high priority`
- **Priority:** High  ·  **Complexity:** M  ·  **Effort:** 2d
- **Status:** Not started
- **Dependencies:** None

**Description**
`docker-compose.yml` references a frontend build context, but
`frontend/Dockerfile` does not exist, so `docker compose up --build` fails. The
backend image is single-stage and runs as root, with no healthchecks or restart
policy — not production-safe.

**Acceptance Criteria**
- [ ] Frontend multi-stage Dockerfile (node build → nginx) + `nginx.conf` (SPA fallback, API URL config)
- [ ] Backend multi-stage Dockerfile (builder + runtime), non-root `USER app`
- [ ] Healthchecks (backend `/health`, db `pg_isready`); `restart: unless-stopped`
- [ ] `.dockerignore` for both apps; `.env.example` documenting every `Settings` var
- [ ] Production compose override with env-provided secrets (no `wasteiq/wasteiq` defaults); controlled `alembic upgrade` on start
- [ ] Full-stack smoke test (register → login) in containers; CI job builds images
- [ ] CI docker build job

**Technical Notes**
- Modules: root `docker-compose.yml`, new `frontend/Dockerfile` + `nginx.conf`, `backend/Dockerfile`, `.dockerignore` files, `frontend/vite.config.ts` (proxy tuning)
- Docs: `DEPLOYMENT_GUIDE.md`
- Testing: CI docker build + local smoke

#### WIQ-V1-023 — Monitoring & Logging

- **Labels:** `infrastructure`, `devops`, `backend`, `high priority`
- **Priority:** High  ·  **Complexity:** M  ·  **Effort:** 2d
- **Status:** Not started
- **Dependencies:** WIQ-V1-022

**Description**
The API uses bare `logging` with ad-hoc records, no request correlation, no
error tracking, and `/health` only checks process liveness.

**Acceptance Criteria**
- [ ] Structured (JSON) logging with request-id middleware; `LOG_LEVEL` setting
- [ ] Uvicorn access logs into structured format
- [ ] Sentry SDK (`SENTRY_DSN`, environment/release tagging, `user_id` context); disabled when DSN absent
- [ ] `GET /health/ready` — liveness + DB check (+ Cloudinary config in production)
- [ ] Optional Prometheus `/metrics` (`prometheus-fastapi-instrumentator`)
- [ ] Backend tests (readiness OK/DB-down, request-id present)

**Technical Notes**
- Modules: `app/main.py`, `app/core/config.py`, new `app/core/logging.py`, `app/core/middleware.py`; add `sentry-sdk` (+ optional `prometheus-fastapi-instrumentator`)
- Docs: `DEPLOYMENT_GUIDE.md`, `SYSTEM_ARCHITECTURE.md` (new env vars)
- Testing: pytest; no external calls in CI

---

## Milestone 2 — Public Beta

**Goal:** Stand up a staging environment, take a custom domain with SSL,
deploy to production, and run a closed beta with a structured feedback loop.

### Epic 2.1 — Beta Infrastructure

#### WIQ-V1-024 — Staging Environment & Deploy Pipeline

- **Labels:** `infrastructure`, `devops`, `high priority`
- **Priority:** High  ·  **Complexity:** M  ·  **Effort:** 2d
- **Status:** Not started
- **Dependencies:** WIQ-V1-022, WIQ-V1-012

**Description**
Only a production deployment exists today (per `docs/DEPLOYMENT_GUIDE.md`),
with no staging parity. A staging environment with automated deploys is
required before beta so changes can be validated without touching production.

**Acceptance Criteria**
- [ ] Staging deploy workflow (`backend-ci`/`frontend-ci` extension or separate workflow) promoting `develop` to staging
- [ ] Staging DB with alembic migrations applied; isolated from production
- [ ] Env parity documented (all `Settings` vars from `app/core/config.py` present in staging)
- [ ] Smoke checks (health, register → login) against staging post-deploy
- [ ] Rollback step documented

**Technical Notes**
- Modules: `.github/workflows/*.yml`, `docs/DEPLOYMENT_GUIDE.md`, `docker-compose*.yml`
- Docs: `DEPLOYMENT_GUIDE.md` (staging section)
- Testing: CI + post-deploy smoke

#### WIQ-V1-025 — Custom Domain & SSL

- **Labels:** `infrastructure`, `devops`, `security`
- **Priority:** High  ·  **Complexity:** S  ·  **Effort:** 1d
- **Status:** Not started
- **Dependencies:** WIQ-V1-024

**Description**
The app runs on platform-provided URLs (e.g. `waste-iq-zeta.vercel.app` /
Railway domain). A branded custom domain with automatic SSL is expected for a
public beta.

**Acceptance Criteria**
- [ ] Custom domain configured for frontend (CNAME/ALIAS) and API (A/ALIAS)
- [ ] Automatic HTTPS/SSL certificate issued and renewing (platform-managed)
- [ ] HTTP → HTTPS redirect; `CORS_ORIGINS` updated in `app/core/config.py` for the new domain
- [ ] `/health` reachable over the custom domain

**Technical Notes**
- Modules: DNS records, platform settings (Vercel/Railway/Render), `app/core/config.py` (`cors_origins`)
- Docs: `DEPLOYMENT_GUIDE.md`
- Testing: manual cert/CORS verification

#### WIQ-V1-026 — Production Go-Live

- **Labels:** `infrastructure`, `devops`, `testing`
- **Priority:** High  ·  **Complexity:** M  ·  **Effort:** 2d
- **Status:** Not started
- **Dependencies:** WIQ-V1-024, WIQ-V1-025

**Description**
Coordinate the production release of the Milestone 1 hardening work: migrate
production DB, deploy backend + frontend, verify all env vars and backups.

**Acceptance Criteria**
- [ ] Production DB migrated to the latest Alembic revision with backup taken first
- [ ] Backend + frontend deployed from release artifacts (WIQ-V1-012)
- [ ] Env vars verified: JWT secret, DB URL, Cloudinary, email/SMTP, CORS
- [ ] Release smoke checklist executed (health, auth, marketplace, admin)
- [ ] Monitoring (WIQ-V1-023) confirmed collecting production data
- [ ] Go/No-Go record added to `docs/DEPLOYMENT_GUIDE.md`

**Technical Notes**
- Modules: `docs/DEPLOYMENT_GUIDE.md`, release workflow (WIQ-V1-012)
- Docs: `DEPLOYMENT_GUIDE.md` (go-live checklist)
- Testing: smoke checklist

### Epic 2.2 — Beta Program

#### WIQ-V1-027 — Beta Feedback & Triage Workflow

- **Labels:** `frontend`, `backend`, `documentation`, `enhancement`
- **Priority:** Medium  ·  **Complexity:** M  ·  **Effort:** 2d
- **Status:** Not started
- **Dependencies:** WIQ-V1-026, WIQ-V1-003

**Description**
There is no structured way for beta users to report issues/feedback; feedback
currently has no intake path into the backlog.

**Acceptance Criteria**
- [ ] In-app feedback widget/button (dashboard) → feedback modal (type, description, screenshot, contact)
- [ ] `POST /feedback` (auth) storing feedback with user context (role, page, UA)
- [ ] Feedback triage: admin view + export; agent (WIQ-V1-003) converts reviewed feedback into issues
- [ ] `Beta` label for beta-related issues on the project board (WIQ-V1-006)
- [ ] Backend + frontend tests

**Technical Notes**
- Modules: new `app/models/feedback.py` + migration, `app/api/routes/feedback.py`, frontend widget; MSW handlers for tests
- **DB migration required** (new table)
- Docs: `API_SPECIFICATION.md`
- Testing: pytest + Vitest

#### WIQ-V1-028 — Beta Program Instrumentation

- **Labels:** `analytics`, `infrastructure`, `enhancement`
- **Priority:** Medium  ·  **Complexity:** M  ·  **Effort:** 2d
- **Status:** Not started
- **Dependencies:** WIQ-V1-023, WIQ-V1-026

**Description**
Launch success needs visibility into beta cohort behavior: activation, pickup
completion rates, marketplace activity. Only aggregate KPIs exist today
(`app/services/analytics.py`).

**Acceptance Criteria**
- [ ] Beta cohort definition (e.g. `registered_after` date or `beta` flag on users) recorded at signup
- [ ] Cohort views: activation (profile/request created), pickup completion rate, marketplace adoption per cohort
- [ ] Dashboards: extend `/admin/analytics` with cohort endpoints; frontend cards/tables
- [ ] Error-rate monitoring confirmed on beta traffic (Sentry + `/health/ready`)
- [ ] Backend tests for cohort metrics

**Technical Notes**
- Modules: `app/services/analytics.py`, `app/api/routes/analytics.py`, `app/models/user.py` (optional `beta` flag + migration), admin frontend
- Docs: `API_SPECIFICATION.md`
- Testing: pytest + Vitest (MSW)

---

## Milestone 3 — Real-Time Features

**Goal:** Deliver live updates over WebSocket built on a shared connection
manager, starting with notifications and collector tracking, then marketplace.

### Epic 3.1 — Real-Time Notification Delivery

#### WIQ-V1-029 — Real-Time Notification Delivery (WebSocket)

- **Labels:** `backend`, `frontend`, `infrastructure`, `high priority`
- **Priority:** High  ·  **Complexity:** L  ·  **Effort:** 3d
- **Status:** Not started
- **Dependencies:** None

**Description**
Notifications are DB-persisted (`NotificationService`) and users must poll the
bell. Adds real-time push via WebSocket, providing the connection manager
reused by WIQ-V1-030 and WIQ-V1-031.

**Acceptance Criteria**
- [ ] Async WS endpoint `/ws/notifications`, JWT-authenticated, with a per-user connection manager
- [ ] Push on every `NotificationService.create` (and broadcast)
- [ ] Reconnect/backoff + heartbeat; re-delivery of missed notifications
- [ ] Frontend `useRealtimeNotifications` hook (native WebSocket, no new dep); live unread badge; polling fallback
- [ ] Tests: pytest WS client flow + Vitest mocked WS / MSW

**Technical Notes**
- Modules: `app/main.py`, `app/services/notifications.py`, new `app/api/ws.py`, `app/core/dependencies.py`; frontend hooks + `NotificationsContext`
- DB sync engine: keep reads out of the connection loop or use an executor; no migration
- Docs: `API_SPECIFICATION.md`, `SYSTEM_ARCHITECTURE.md`
- Testing: `fastapi.testclient.websocket_connect`; Vitest mocked WS

### Epic 3.2 — Live Collector Tracking & Presence

#### WIQ-V1-030 — Live Collector Tracking & Presence

- **Labels:** `backend`, `frontend`, `enhancement`
- **Priority:** Medium  ·  **Complexity:** M  ·  **Effort:** 2d
- **Status:** Not started
- **Dependencies:** WIQ-V1-029

**Description**
GPS updates go through REST and the map refreshes lazily (`collector_map`,
`useCollectorMap`, `collector_location`/history). Real-time position streaming
plus presence completes the operations layer.

**Acceptance Criteria**
- [ ] Collector WS `/ws/collector/tracking` — throttled GPS pushes persisted to `collector_location` (+ history)
- [ ] Live position stream for watchers (admin/citizen) on assignment requests
- [ ] Presence: online/offline from connect/disconnect + heartbeat; expose `is_online`, `last_seen_at`
- [ ] Frontend map subscribes + invalidates React Query on messages; presence dot UI
- [ ] Tests: WS ingest (auth + validation + persistence), presence transitions, Vitest mocked WS

**Technical Notes**
- Modules: `app/services/collector_map.py`, `app/services/location.py`, `app/api/ws.py`, `app/models/collector_location.py`, `frontend/src/hooks/useCollectorMap.ts`
- **DB migration only if presence columns added**; otherwise in-memory presence registry
- Docs: `API_SPECIFICATION.md`
- Testing: pytest + Vitest

### Epic 3.3 — Live Marketplace

#### WIQ-V1-031 — Live Marketplace Updates (WebSocket)

- **Labels:** `backend`, `frontend`, `enhancement`
- **Priority:** Medium  ·  **Complexity:** M  ·  **Effort:** 2d
- **Status:** Not started
- **Dependencies:** WIQ-V1-029

**Description**
Dealers must reload to see newly listed lots, price changes, reservation
state, or released reservations. Real-time updates improve the purchase flow.

**Acceptance Criteria**
- [ ] Marketplace channel: publish lot created/updated/archived, reserved, reservation expired/cancelled, purchased — from `app/services/inventory_marketplace.py`
- [ ] Frontend `MarketplacePage`/`MarketplaceDetailsPage` subscribe; invalidate React Query keys; optimistic update for own reservation
- [ ] Reconnect re-syncs page state
- [ ] Backend WS tests per event + Vitest mocked WS

**Technical Notes**
- Modules: `app/services/inventory_marketplace.py`, `app/api/ws.py`, `frontend/src/pages/dashboard/MarketplacePage.tsx`, `frontend/src/hooks/useMarketplace.ts`
- No migration
- Docs: `API_SPECIFICATION.md`
- Testing: pytest + Vitest

---

## Milestone 4 — AI Platform

**Goal:** Turn the wired AI stubs and historical marketplace data into
production AI features across three epics: Computer Vision, AI Intelligence,
and MLOps (experiment tracking, registry, monitoring, retraining).

### Epic 4.1 — AI Computer Vision

#### WIQ-V1-032 — Implement Waste Image Classification (real inference)

- **Labels:** `ai`, `backend`, `enhancement`
- **Priority:** Medium  ·  **Complexity:** L  ·  **Effort:** 3d
- **Status:** Not started
- **Dependencies:** None

**Description**
`app/services/ai_classifier.py` defines `AIClassifierProvider` with a
`YOLOv8Classifier` stub returning a mock (`category="Unknown"`,
`confidence=0.0`). The stub is already invoked at pickup upload and results
persist to `pickup_request.category`/`confidence`, so only real inference needs
wiring.

**Acceptance Criteria**
- [ ] YOLOv8 waste-detection model (e.g. TrashNet classes mapped to `MaterialCategory`) with pinned/checksummed weights fetched at image build
- [ ] Real inference in `YOLOv8Classifier` (lazy load, GPU-optional); map detections to existing categories
- [ ] Classification non-blocking for upload (existing try/except → `Unknown/0.0` fallback)
- [ ] Persist top category + confidence (columns exist)
- [ ] Graceful model-unavailable behavior in dev/tests; no hard CI dependency
- [ ] Experiments logged to MLflow (WIQ-V1-039) once available
- [ ] Tests: mocked classifier path stays green; result-mapping unit tests

**Technical Notes**
- Modules: `app/services/ai_classifier.py`, `app/services/pickup_request_images.py`, `app/core/dependencies.py`; add `ultralytics` (+torch) via a `requirements-ai.txt`
- Docker: model weights added in the backend image build (WIQ-V1-022)
- Docs: `SYSTEM_ARCHITECTURE.md` (AI section), README
- Testing: pytest with a fake provider; deterministic output

#### WIQ-V1-033 — Waste Quality Assessment

- **Labels:** `ai`, `backend`, `enhancement`
- **Priority:** Medium  ·  **Complexity:** M  ·  **Effort:** 2d
- **Status:** Not started
- **Dependencies:** WIQ-V1-032

**Description**
`inventory_lot.quality_grade` is a manual admin field. Automate a quality
suggestion from pickup images to reduce admin effort and improve marketplace
confidence.

**Acceptance Criteria**
- [ ] Extend the WIQ-V1-032 pipeline to emit a quality grade (condition/contamination heuristic from detections + confidence)
- [ ] Store suggestion (`suggested_quality_grade`) at lot creation from the source pickup
- [ ] Admin "AI suggestion" next to the grade editor, one-click apply
- [ ] No suggestion when confidence below threshold
- [ ] Tests: mapping rules, threshold behavior, persistence

**Technical Notes**
- Modules: `app/services/ai_classifier.py`, `app/services/inventory_marketplace.py` (lot creation), `app/models/inventory_lot.py`, admin UI
- **DB migration required** (new nullable column)
- Docs: `API_SPECIFICATION.md`
- Testing: pytest

### Epic 4.2 — AI Intelligence

#### WIQ-V1-034 — Plastic Price Prediction

- **Labels:** `ai`, `backend`, `admin`, `enhancement`
- **Priority:** Medium  ·  **Complexity:** M  ·  **Effort:** 2d
- **Status:** Not started
- **Dependencies:** WIQ-V1-039 (experiment tracking), WIQ-V1-021 (refresh job)

**Description**
Pricing is rule-driven (`PricingRule`/`MaterialCategory`) and snapshotted per
lot. Predict a suggested per-kg price per category/region from historical
`inventory_lots`, `marketplace_orders`, and `marketplace_transactions` to
inform admin pricing.

**Acceptance Criteria**
- [ ] Offline training script exporting a feature dataset (category, city, quality grade, time, price per kg) to CSV/DB
- [ ] Baseline model (scikit-learn gradient boosting or rolling average ± confidence) persisted; metrics documented
- [ ] `GET /admin/pricing/prediction?category_id=&city=` — suggested price + confidence + data window, admin-only
- [ ] Admin pricing page shows suggestion alongside the current rule
- [ ] Tests: endpoint contract + fallback when artifacts/missing data

**Technical Notes**
- Modules: new `app/services/ai_pricing.py`, `app/services/analytics.py`, `app/api/routes/admin.py`/`analytics.py`, admin pricing UI
- No migration (artifacts on disk/registry)
- Docs: `SYSTEM_ARCHITECTURE.md`, README
- Testing: pytest with fixture dataset

#### WIQ-V1-035 — Dealer Demand Forecasting

- **Labels:** `ai`, `backend`, `analytics`, `enhancement`
- **Priority:** Medium  ·  **Complexity:** M  ·  **Effort:** 2d
- **Status:** Not started
- **Dependencies:** WIQ-V1-034, WIQ-V1-039

**Description**
No forward-looking demand view exists. Forecast supply/demand by material
category and city from `inventory_lots` + `marketplace_orders` + transactions,
surfaced to admins to guide pricing and collection effort.

**Acceptance Criteria**
- [ ] Forecast service (time-series baseline: rolling average + seasonality) per category/city/month
- [ ] `GET /admin/analytics/forecast?category=&city=&horizon=` with confidence bands, admin-only
- [ ] Refresh via WIQ-V1-021 scheduler; versioned artifacts in the model registry (WIQ-V1-040)
- [ ] Forecast chart on the admin analytics page (V1-002 trend charts)
- [ ] Tests: endpoint contract + deterministic forecasts on fixture data

**Technical Notes**
- Modules: new `app/services/ai_forecasting.py`, `app/services/analytics.py`, `app/api/routes/analytics.py`, admin dashboard + `useAnalytics.ts`
- No migration
- Docs: `SYSTEM_ARCHITECTURE.md`
- Testing: pytest

#### WIQ-V1-036 — Real Route Optimization (OSRM/GraphHopper)

- **Labels:** `infrastructure`, `backend`, `enhancement`
- **Priority:** Medium  ·  **Complexity:** M  ·  **Effort:** 2d
- **Status:** Not started
- **Dependencies:** None

**Description**
`app/services/routing.py` already implements greedy nearest-neighbour
multi-stop ordering and a `RoutingProvider` abstraction, but the real providers
(`osrm`, `graphhopper`, `google_directions`) throw `NotImplementedError`.
Road-network routing (not haversine) is needed for accurate collector time
estimates.

**Acceptance Criteria**
- [ ] Implement OSRM (or GraphHopper) provider with real road geometry/distance/duration (`OSRM_BASE_URL` / `GRAPHOPPER_API_KEY`)
- [ ] Keep mock provider for dev/tests; `ROUTING_PROVIDER` setting
- [ ] Apply to collector-map routes (`app/services/collector_map.py`, `app/services/routing.py`)
- [ ] Fallback to haversine mock when provider unavailable
- [ ] Tests: provider fetch mocked via httpx `MockTransport`; fallback covered

**Technical Notes**
- Modules: `app/services/routing.py`, `app/services/collector_map.py`, `app/core/config.py`
- No migration
- Docs: README env vars, `SYSTEM_ARCHITECTURE.md`
- Testing: pytest with mocked external calls (`httpx` already present)

#### WIQ-V1-037 — AI Assistant

- **Labels:** `ai`, `backend`, `frontend`, `enhancement`
- **Priority:** Medium  ·  **Complexity:** L  ·  **Effort:** 3d
- **Status:** Not started
- **Dependencies:** WIQ-V1-017

**Description**
Admins/dealers/citizens need in-product guidance (verification process,
pricing drivers, order status). A role-aware Q&A assistant handles routine
support without dedicated staff.

**Acceptance Criteria**
- [ ] `POST /assistant/chat` — role-aware context; answers scoped to project docs (README/API spec/FAQ) and visible-to-role data (no cross-tenant leakage)
- [ ] Provider config (`AI_ASSISTANT_MODEL`, `AI_ASSISTANT_API_KEY`); rule-based FAQ fallback when unset (free / graceful)
- [ ] Streaming preferred; cost controls (max tokens, per-user rate limit via WIQ-V1-017)
- [ ] Frontend chat widget (bottom-right, portal-agnostic) using the existing API client
- [ ] Tests: auth + role scoping + fallback; MSW for widget; PII guard (no raw emails/phones in outputs)

**Technical Notes**
- Modules: new `app/services/ai_assistant.py`, `app/api/routes/assistant.py`, `app/core/config.py`, frontend `AssistantWidget` + `useAssistant`
- Grounding: FAQ derived from `docs/BUSINESS_REQUIREMENTS.md`/README or a new `docs/assistant-faq.md`
- No migration
- Docs: `API_SPECIFICATION.md`, `SYSTEM_ARCHITECTURE.md`
- Testing: pytest + Vitest

#### WIQ-V1-038 — AI Analytics Dashboard

- **Labels:** `ai`, `backend`, `frontend`, `analytics`, `enhancement`
- **Priority:** Medium  ·  **Complexity:** M  ·  **Effort:** 2d
- **Status:** Not started
- **Dependencies:** WIQ-V1-034, WIQ-V1-035

**Description**
`app/services/analytics.py` (`/admin/analytics`) is descriptive — KPIs and
counts only. Add trend / composition / anomaly views backed by WIQ-V1-034 and
WIQ-V1-035 to make the admin dashboard decision-grade.

**Acceptance Criteria**
- [ ] Trend views: pickups, weight, GMV by day/week per category and city (existing tables)
- [ ] Waste composition breakdown + reserved-vs-purchased funnel
- [ ] Anomaly flags: pickup-volume dips vs baseline, reservation expiry spikes (WIQ-V1-021 events)
- [ ] `GET /admin/analytics/insights` aggregate endpoint; charts on the admin dashboard (V1-002)
- [ ] Tests: aggregation correctness on seeded fixtures; empty-state rendering

**Technical Notes**
- Modules: `app/services/analytics.py`, `app/api/routes/analytics.py`, admin dashboard page + `lib/analytics.ts` + `useAnalytics.ts`
- No migration (live aggregates; revisit indexes in perf pass)
- Docs: `API_SPECIFICATION.md`
- Testing: pytest + Vitest with MSW fixtures

### Epic 4.3 — MLOps

#### WIQ-V1-039 — MLflow Experiment Tracking

- **Labels:** `mlops`, `ai`, `infrastructure`, `enhancement`
- **Priority:** Medium  ·  **Complexity:** M  ·  **Effort:** 2d
- **Status:** Not started
- **Dependencies:** WIQ-V1-032 (first real model to track)

**Description**
No experiment tracking exists — model iterations are untraceable. MLflow
provides run logging (params, metrics, artifacts) for the Vision and
Intelligence model work and is the foundation for the registry (WIQ-V1-040).

**Acceptance Criteria**
- [ ] MLflow tracking server configured (self-hosted container in `docker-compose` or managed) with persistent backend store
- [ ] Training scripts for classification (WIQ-V1-032), pricing (WIQ-V1-034), forecasting (WIQ-V1-035) log runs: params, metrics, artifacts
- [ ] Run comparison/viewing works; URL documented
- [ ] `MLFLOW_TRACKING_URI` setting wired into backend config; no tracking when unset (dev/tests)

**Technical Notes**
- Modules: `docker-compose.yml` (mlflow service), `app/core/config.py`, training scripts in `backend/scripts/` or `ml/`
- Docs: `SYSTEM_ARCHITECTURE.md` (MLOps section)
- Testing: manual run verification; unit-test the logging wrapper with a mock client

#### WIQ-V1-040 — Model Registry

- **Labels:** `mlops`, `ai`, `infrastructure`, `enhancement`
- **Priority:** Medium  ·  **Complexity:** M  ·  **Effort:** 2d
- **Status:** Not started
- **Dependencies:** WIQ-V1-039

**Description**
Models are not versioned or promotion-gated; production uses whatever artifact
is on disk. A model registry (MLflow Model Registry) versions models and gates
promotion to staging/production.

**Acceptance Criteria**
- [ ] Registered model names per use case (`waste-classifier`, `price-predictor`, `demand-forecaster`) with staged/champion aliases
- [ ] Promotion workflow: register → stage → (approved) → production alias; rollback to previous champion supported
- [ ] Services load the production alias at startup; fallback to bundled artifact when registry unreachable
- [ ] Promotion policy documented (who/which agent approves)

**Technical Notes**
- Modules: `app/services/ai_*` (model loading), `ml/` training pipeline, `docker-compose.yml` (registry storage)
- Docs: `SYSTEM_ARCHITECTURE.md`, `CONTRIBUTING.md`
- Testing: registry client mocked in unit tests; manual promotion walkthrough

#### WIQ-V1-041 — Model Monitoring

- **Labels:** `mlops`, `ai`, `backend`, `analytics`, `enhancement`
- **Priority:** Medium  ·  **Complexity:** M  ·  **Effort:** 2d
- **Status:** Not started
- **Dependencies:** WIQ-V1-040

**Description**
No visibility into model performance post-deployment: prediction correctness,
input drift, or degradation. Monitoring is needed before AI features are
trusted in production.

**Acceptance Criteria**
- [ ] Prediction logging: inference requests logged with model version, inputs (hashed/pii-safe), predicted category/price, confidence
- [ ] Correctness/feedback capture: classification vs finalized category, predicted price vs realized price, forecast vs actual
- [ ] Drift & degradation metrics (accuracy/MAE windowed, drift alerts) surfaced in `/admin/analytics/insights` or MLOps dashboard
- [ ] Alerting hook into WIQ-V1-023 (Sentry/metrics)
- [ ] Tests: logging pipeline + metric computation on fixtures

**Technical Notes**
- Modules: `app/services/ai_*` (inference logging), new `app/services/ml_monitoring.py`, `app/api/routes/analytics.py`; optional `mlflow` tracking for metric log runs
- **DB migration required** (prediction log table) — or time-series store
- Docs: `SYSTEM_ARCHITECTURE.md`
- Testing: pytest

#### WIQ-V1-042 — Model Retraining Pipeline

- **Labels:** `mlops`, `ai`, `infrastructure`, `devops`, `enhancement`
- **Priority:** Medium  ·  **Complexity:** L  ·  **Effort:** 3d
- **Status:** Not started
- **Dependencies:** WIQ-V1-040, WIQ-V1-041

**Description**
Models are trained ad-hoc and don't incorporate new labeled data or monitoring
feedback. A scheduled retraining pipeline keeps models fresh with registry
promotion on improvement.

**Acceptance Criteria**
- [ ] Training job (scheduled via WIQ-V1-021 or cron) for each model: extract features → train → evaluate vs current champion → register candidate (WIQ-V1-040)
- [ ] Promotion gate: candidate promoted to production alias only if it beats champion on held-out metrics
- [ ] Pipeline idempotent and failure-safe (no promotion on failure); logs to MLflow (WIQ-V1-039)
- [ ] Retraining frequency configurable; runbook documented
- [ ] Tests: pipeline stages unit-tested with fixtures; promote/don't-promote logic

**Technical Notes**
- Modules: `ml/train_*.py` scripts, `app/services/jobs.py` (schedule), `app/services/ml_monitoring.py` (feedback data), `docker-compose.yml`
- Docs: `SYSTEM_ARCHITECTURE.md`, `DEPLOYMENT_GUIDE.md`
- Testing: pytest for gate logic; manual pipeline run

---

## Backlog Summary

| Milestone | Epic | Issues | Total Effort (est.) |
| --- | --- | --- | --- |
| M0 Engineering Productivity | 0.1 AI Agents · 0.2 Project Mgmt | 001–012 | 13.5d |
| M1 Production Readiness | 1.1 Auth & Security · 1.2 Platform Ops | 013–023 | 21d |
| M2 Public Beta | 2.1 Beta Infra · 2.2 Beta Program | 024–028 | 9d |
| M3 Real-Time Features | 3.1 Delivery · 3.2 Tracking · 3.3 Marketplace | 029–031 | 7d |
| M4 AI Platform | 4.1 Vision · 4.2 Intelligence · 4.3 MLOps | 032–042 | 25d |

**Total: 42 issues, ~75.5 estimated working days (≈ 7–8 two-week sprints at
2 developers, M0/M1 overlap recommended).**

## Open Decisions (to resolve during review)

1. Email provider: SMTP via existing host vs. a managed provider (SendGrid/Postmark). Affects WIQ-V1-014/015.
2. Refresh tokens: opaque DB-backed (recommended, enables revoke/logout-all) vs. stateless JWT. Affects WIQ-V1-013.
3. Rate limiter storage: in-memory (single instance on Railway/Render) vs. Redis-backed from day one. Affects WIQ-V1-017.
4. Background jobs: APScheduler in-process (recommended to start) vs. Celery + Redis. Affects WIQ-V1-021.
5. Real-time vs. REST-polling fallback mix and whether the engine must become async. Affects WIQ-V1-029–031.
6. AI inference hosting: in-image (ultralytics) vs. managed inference API. Affects WIQ-V1-032.
7. Mandatory verified-email purchase gate lands with M1. Affects WIQ-V1-014.
8. LLM provider + model for the engineering agents (opencode GitHub App), and which Actions secret stores the key. Affects WIQ-V1-001–005.
9. GitHub Project (v2) vs. org-level project; whether project automation uses a workflow action. Affects WIQ-V1-006.
10. MLflow hosting: self-hosted container vs. managed (Databricks/community) — cost/ops trade-off. Affects WIQ-V1-039–042.
11. Model promotion approval: human vs. automated gate. Affects WIQ-V1-040/042.

---

*Generated from codebase analysis of `backend/` and `frontend/`. Pending final
review before creating GitHub issues milestone by milestone.*