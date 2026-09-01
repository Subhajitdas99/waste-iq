# Waste-IQ Product Improvement Audit (WIQ-V1-055)

**Document Version:** 1.0.0
**Audit Date:** 2026-09-01
**Auditor:** Product / Engineering Audit
**Repository:** `Waste-IQ` (`Subhajitdas99/waste-iq`)
**Audit Method:** Evidence-based inspection of the working tree (no code modified, no issues created)

> **Reading guide:** Status labels used throughout this report:
> - **IMPLEMENTED** â€” code exists, tests pass, behaviour observable.
> - **PARTIAL** â€” code exists but is incomplete, stubbed, disabled, or only covers a subset of the requirement.
> - **STUB / MOCK** â€” placeholder code that returns hard-coded or empty values, not production-useful.
> - **DOCUMENTATION ONLY** â€” described in markdown but absent from code.
> - **MISSING** â€” neither code nor documentation addresses the requirement.

---

## Table of Contents

1. [What Waste-IQ is today](#1-what-waste-iq-is-today)
2. [What Waste-IQ should become for the first pilot](#2-what-waste-iq-should-become-for-the-first-pilot)
3. [Current strengths](#3-current-strengths)
4. [Top 10 problems](#4-top-10-problems)
5. [Top 10 opportunities](#5-top-10-opportunities)
6. [Pilot blockers](#6-pilot-blockers)
7. [Existing issues that already cover the work](#7-existing-issues-that-already-cover-the-work)
8. [New issues that should be created](#8-new-issues-that-should-be-created)
9. [Recommended implementation sequence](#9-recommended-implementation-sequence)
10. [Product differentiation strategy](#10-product-differentiation-strategy)
11. [30-day pilot definition](#11-30-day-pilot-definition)
12. [Success metrics](#12-success-metrics)
13. [Detailed evidence and analysis](#13-detailed-evidence-and-analysis)
14. [Step 2: Feature inventory](#14-step-2-feature-inventory)
15. [Step 3: User role map](#15-step-3-user-role-map)
16. [Step 4: Waste lifecycle map](#16-step-4-waste-lifecycle-map)
17. [Step 5â€“8: Per-role product audit](#17-step-58-per-role-product-audit)
18. [Step 9: Trust / privacy / security audit](#18-step-9-trust--privacy--security-audit)
19. [Step 10: Weight trust model](#19-step-10-weight-trust-model)
20. [Step 11: Inventory / marketplace audit](#20-step-11-inventory--marketplace-audit)
21. [Step 12: Business model audit](#21-step-12-business-model-audit)
22. [Step 13: Analytics audit](#22-step-13-analytics-audit)
23. [Step 14: AI audit](#23-step-14-ai-audit)
24. [Step 15: UX / branding audit](#24-step-15-ux--branding-audit)
25. [Step 16: Mobile field experience](#25-step-16-mobile-field-experience)
26. [Step 17: Failure / edge case audit](#26-step-17-failure--edge-case-audit)
27. [Step 18: Production readiness](#27-step-18-production-readiness)
28. [Step 19: Pilot readiness](#28-step-19-pilot-readiness)
29. [Step 20: Existing issue audit](#29-step-20-existing-issue-audit)
30. [Step 21: Product differentiation scoring](#30-step-21-product-differentiation-scoring)
31. [Step 22: Prioritized backlog](#31-step-22-prioritized-backlog)
32. [Step 23: Epics](#32-step-23-epics)
33. [Step 24: Top 10 next issues](#33-step-24-top-10-next-issues)

---

## 1. What Waste-IQ is today

Waste-IQ is a full-stack web application built with FastAPI + React 19 that digitises the citizen-to-collector recyclable-waste pickup lifecycle. It is a **working engineering scaffold** with:

- **Authenticated multi-role accounts** (citizen, collector, dealer, admin) with JWT and refresh-token rotation.
- **Citizen pickup workflow** â€” request submission with optional photo, GPS, and notes; status tracking through an 8-state pickup lifecycle (pending â†’ accepted â†’ on_the_way â†’ collected â†’ weight_recorded â†’ disputed/completed â†’ cancelled).
- **Collector workflow** â€” browse available requests, accept and manage assignments, record verified weight, complete pickups.
- **Weight verification system** â€” collector records weight; citizen can confirm or dispute; admin can resolve disputes (WIQ-V1-046, implemented).
- **Masked communication** â€” privacy-preserving contact relay between citizen and collector (WIQ-V1-047, implemented as a mock provider; Twilio is a stub raising 501).
- **Dealer/recycler role** â€” four-state business profile approval workflow (draft â†’ submitted â†’ approved/rejected).
- **Inventory marketplace** â€” admin creates lots from completed pickups; dealers browse, reserve (24-hour TTL), and purchase; financial ledger via `MarketplaceTransaction`.
- **Database-backed notification system** â€” ~25 event types across pickup lifecycle, dealer approval, and inventory.
- **Background jobs** â€” reservation expiry sweep (1 minute) and aging pickup alerts (5 minutes).
- **Audit logging** â€” every state-changing action recorded with actor attribution; sensitive fields (password, tokens, phone) explicitly redacted.
- **Cloudinary image storage** with local filesystem fallback for development.
- **Comprehensive backend test suite** â€” 39 test files, 80%+ coverage on `app/` module.
- **CI/CD pipeline** â€” Backend CI, Frontend CI, Agent CI, Docker CI, PR Gate with path-filtered workflows.
- **Docker Compose** local development environment.

Waste-IQ is **NOT YET a revenue-generating business platform**. The software infrastructure is solid; the business workflows are incomplete.

---

## 2. What Waste-IQ should become for the first pilot

A pilot-ready waste-management platform for a single geographic area with:

- 100 citizens who can request waste pickups and verify recorded weights.
- 2â€“5 collectors who can accept, navigate to, and complete pickups, recording accurate weights.
- 1â€“3 dealers/recyclers who can browse inventory and complete purchase transactions.
- 1 admin who can manage all participants, resolve disputes, and read operational dashboards.
- **Full transaction traceability** â€” every gram of waste tracked from citizen request to dealer purchase.
- **Verified weight** â€” citizen trust through a weight-dispute workflow.
- **Revenue visibility** â€” the platform can report gross marketplace value and platform commission.
- **Operational reliability** â€” the team can identify and resolve stuck pickups, failed requests, and disputes without database diving.

The 30-day pilot definition is addressed in Section 11.

---

## 3. Current Strengths

| Area | Strength | Evidence |
|------|----------|----------|
| **Engineering foundations** | Layered architecture, typed Python/TypeScript, 80%+ test coverage, CI/CD pipeline | `backend/app/services/`, `frontend/src/routes/`, `pr-gate.yml` |
| **Authentication** | JWT + refresh token rotation, account lockout, rate limiting, bcrypt | `app/core/security.py`, `app/core/ratelimit.py`, `test_auth.py` |
| **Audit logging** | Every state change recorded; sensitive PII explicitly redacted from logs | `app/services/audit.py` lines 13â€“32 (SENSITIVE_KEYS blocklist) |
| **Weight verification** | Complete WIQ-V1-046 implementation: citizen confirm/dispute, admin resolution | `app/models/pickup_request.py:16â€“17`, `test_weight_verification.py` |
| **Masked communication** | Phone redaction from collector payloads; masked contact relay endpoint | `app/services/pickup_requests.py:49â€“63` (`_should_expose_phone`), `app/services/communication.py` |
| **Collector map** | Dependency-free SVG map with geolocation, route sequencing, nearest-neighbour algorithm | `collector_map.py`, `test_collector_map.py` |
| **Inventory marketplace** | Full browse/reserve/purchase flow with financial ledger and audit trail | `inventory_marketplace.py`, `test_marketplace.py` |
| **Notification system** | ~25 event types, role-based delivery, admin broadcast, optimistic mutations | `app/services/notifications.py`, `test_notifications.py` |
| **Database migrations** | 20+ clean Alembic migrations, SQLite dev / PostgreSQL prod | `backend/alembic/versions/` |
| **Test coverage** | 39 backend test files covering auth, permissions, security, workflows | `backend/tests/` |
| **Docker setup** | Multi-stage Dockerfile, docker-compose.yml, docker-compose.prod.yml | â€” |

---

## 4. Top 10 Problems

1. **No financial/commission model** â€” `MarketplaceTransaction` records gross value but there is no commission calculation or platform revenue tracking. The `dealer_orders` table has `commission_percent` and `platform_revenue_amount` fields that are never populated.

2. **No CSV export** â€” admins cannot export transaction data for reconciliation, investor reporting, or pilot review. This is a WIQ-010 backlog item with no implementation.

3. **Auto-lot creation not implemented** â€” completed pickups do not automatically become inventory lots. Admins must manually create every lot. This is a WIQ-V1-053 / issue #111 item with partial spec but no code.

4. **Admin address exposure to collectors** â€” collectors see the citizen's full street address (not just coordinates) in `PickupRequestRead.address` for every available pickup. While necessary for navigation, this exposes residential addresses to any registered collector before assignment.

5. **Dealer inventory creation is manual** â€” dealers cannot create their own inventory (they source from admin-created lots). The `DealerInventory` table exists (`dealer_inventory.py`) but is unused; all lots come through `InventoryLot`.

6. **Estimated pickup value not shown** â€” citizens do not see an estimated material value when submitting pickups. No pricing rules are applied in the citizen-facing flow. This is WIQ-005.

7. **Collector has no earnings/payout view** â€” collectors see completion counts and weight totals but no earnings, payout rates, or settlement history. This is essential for collector retention.

8. **Aging pickup alerts go to admins only** â€” collectors who have accepted a pickup but do not progress receive no automated reminders. The aging alert job only notifies admins.

9. **Weight dispute evidence not supported** â€” citizens can file a weight dispute with a text reason, but there is no mechanism to upload a scale photo or other evidence. This limits dispute resolution quality.

10. **Brand identity is weak** â€” the product has only a text "Waste-IQ" wordmark in the navigation and a leaf favicon. There is no logo file, no color system, no design tokens, and no consistent visual identity.

---

## 5. Top 10 Opportunities

| # | Opportunity | Customer Value | Business Value | Technical Feasibility | Defensibility |
|---|-------------|---------------|---------------|---------------------|---------------|
| 1 | **Verified waste weight** â€” citizen weight confirmation before inventory creation | 5 | 5 | 4 (already done) | 5 |
| 2 | **Waste traceability** â€” full chain of custody from request to recycler sale | 5 | 5 | 4 | 5 |
| 3 | **Collector operations** â€” map + route + weight in one mobile UI | 5 | 4 | 4 | 3 |
| 4 | **Recycler marketplace** â€” verified dealers sourcing from platform inventory | 4 | 5 | 4 (already done) | 3 |
| 5 | **Material inventory** â€” aggregated recyclable volumes by category, city, time | 4 | 4 | 5 | 2 |
| 6 | **Analytics dashboard** â€” pilot metrics in one view for founders and municipality | 4 | 4 | 5 | 2 |
| 7 | **Weight dispute workflow** â€” citizen agency and trust in recorded weight | 5 | 3 | 4 (already done) | 4 |
| 8 | **Revenue reporting** â€” GMV, commission, and payout from transaction ledger | 3 | 5 | 3 | 3 |
| 9 | **Email + in-app notifications** â€” real-time status updates for all participants | 4 | 3 | 5 | 1 |
| 10 | **Brand + design system** â€” professional appearance for recruits, partners, investors | 3 | 4 | 5 | 2 |

**Strongest differentiators (top 3):** (1) Verified waste weight â€” a trust mechanism no competitor offers; (2) Full waste traceability â€” creates the circular-economy audit trail municipalities and ESG investors demand; (3) Recycler marketplace â€” converts the platform from an operations tool into a revenue-generating business.

---

## 6. Pilot Blockers

The following block a real-world 100-citizen / 2-collector / 1-dealer / 30-day pilot:

| Blocker | Severity | Why it Blocks the Pilot |
|---------|----------|----------------------|
| **No auto-lot creation** | P0 | Admin must manually create every inventory lot. With 100 citizens making ~2 pickups/week, an admin would need to manually create ~50 lots/week. This is operationally unsustainable and will bottleneck the entire marketplace. |
| **No revenue reporting** | P0 | The pilot cannot demonstrate commercial viability without gross marketplace value and platform commission data. Founders cannot answer "what did Waste-IQ earn this week?" from the product alone. |
| **No CSV export** | P0 | Pilot reconciliation, investor reporting, and municipality handoff all require exportable data. Without it, every report requires manual database queries. |
| **Collector earnings view missing** | P0 | Collectors will not participate without knowing how much they earn per kg and when they get paid. The current collector summary shows weight totals but no monetary value. |
| **Estimated pickup value absent** | P1 | Citizens submitting pickups have no idea of the material's value. This reduces submission motivation and prevents pricing transparency from being a pilot talking point. |
| **Admin sees all user phones** | P1 | `/admin/users` returns the `UserRead` schema which includes `phone`. Any admin account compromise exposes the entire user base's phone numbers. Should be split into separate endpoints or a phone-redacted admin view. |
| **No SMTP in production** | P1 | Email verification and password reset are functional in development (console backend) but `SMTP_HOST` is empty in production config. Real users cannot verify email or reset passwords without a configured SMTP provider. |
| **Brand identity missing** | P2 | A product shown to municipality stakeholders, investors, and potential dealers looks like a student project without a professional logo and design system. This affects first impressions and trust. |

---

## 7. Existing Issues That Already Cover the Work

The following existing backlog items and WIQ documents already capture the gaps identified in this audit. They should be reviewed and cross-referenced before new issues are created.

| Existing Issue / Doc | Covers | Status in Code |
|---------------------|--------|---------------|
| **WIQ-V1-046** (Weight Verification) | Weight confirm/dispute, admin resolution | IMPLEMENTED |
| **WIQ-V1-047** (Masked Communication) | Phone redaction, contact relay | IMPLEMENTED (mock provider) |
| **WIQ-V1-014** (Email Verification) | Signed tokens, background dispatch | IMPLEMENTED |
| **WIQ-V1-053 / issue #111** | Auto-lot creation from completed pickups | MISSING (spec exists in `dealer-marketplace-mvp-spec.md` Â§FR-4) |
| **WIQ-004** (Pricing model) | Admin category pricing CRUD | IMPLEMENTED (`pricing_rules` table, CRUD endpoints) |
| **WIQ-005** (Estimated value preview) | Show citizen estimated value at request creation | MISSING |
| **WIQ-006** (Weight capture at completion) | Require weight before complete | IMPLEMENTED |
| **WIQ-007** (Transaction ledger records) | Create `CompletedTransaction` on completion | PARTIAL â€” `MarketplaceTransaction` exists but commission not calculated |
| **WIQ-008** (Commission configuration) | Admin commission percentage | PARTIAL â€” field exists in model, never set |
| **WIQ-009** (GMV and revenue analytics) | Commercial KPIs in admin dashboard | PARTIAL â€” `AnalyticsRead` has `total_revenue` but it's hardcoded to 0 |
| **WIQ-010** (CSV export) | Admin export monetized transactions | MISSING |
| **WIQ-011** (Dealer role) | Dealer account creation and access | IMPLEMENTED |
| **WIQ-012** (Dealer onboarding) | Business profile, verification workflow | IMPLEMENTED |
| **WIQ-015** (Municipality role) | Read-only municipality user role | MISSING |
| **WIQ-016** (Zone-level reporting) | Geographic pilot metrics | MISSING |
| **WIQ-018** (AI feature gating policy) | When to start AI work | DOCUMENTATION ONLY |
| **revenue-mvp-spec.md** | Revenue capture, commission, export | See above â€” partially implemented |
| **dealer-marketplace-mvp-spec.md** | Full dealer marketplace spec | See above â€” partially implemented |
| **launch-roadmap.md** | Milestone 0â€“4, recommended order | Valid but needs updating for current implementation state |
| **V1_LAUNCH_READINESS_AUDIT.md** | Pre-launch gap analysis | Valid but dated â€” WIQ-V1-046 and WIQ-V1-047 have since been implemented |

---

## 8. New Issues That Should Be Created

Beyond the existing backlog, the following new issues should be created to address gaps not yet captured:

| ID | Title | Priority | Affected Role | Summary |
|----|-------|----------|--------------|---------|
| **NEW-01** | Auto-create inventory lot from completed pickup | P0 | Admin | Currently admin must manually create every lot. An "Create Lot" action on the completed pickup detail screen, or an auto-creation option, would eliminate the manual bottleneck. |
| **NEW-02** | Revenue reporting: commission calculation and GMV analytics | P0 | Admin | `MarketplaceTransaction` records gross value. Add commission calculation (flat % from `pricing_rules` or config) and display GMV + platform revenue in admin analytics. |
| **NEW-03** | CSV export for transactions and pickups | P0 | Admin | Admins need to export `MarketplaceTransaction` and `MarketplaceOrder` data for reconciliation. One-click export with date range filter. |
| **NEW-04** | Collector earnings and payout dashboard | P0 | Collector | Collectors need a per-kg rate, total earnings, and payment history view. This is essential for collector retention and pilot sustainability. |
| **NEW-05** | Citizen estimated value at pickup submission | P1 | Citizen | Show estimated material value (based on `estimated_weight_kg` Ã— `pricing_rules`) when citizen submits a pickup request. Clearly label as approximate. |
| **NEW-06** | Admin user API: phone-redacted listing | P1 | Admin | Split `/admin/users` into `/admin/users` (phone-redacted for listing) and `/admin/users/{id}` (full detail, including phone, for the specific-user detail page). |
| **NEW-07** | Production SMTP configuration and email delivery verification | P1 | All | Configure real SMTP (SendGrid / AWS SES / Resend) for production. Verify email verification links and password reset emails reach real inboxes. |
| **NEW-08** | Weight dispute evidence upload | P1 | Citizen, Admin | Allow citizens to upload a scale photo when filing a weight dispute. Store on Cloudinary and link to the `PickupDispute` record. |
| **NEW-09** | Collector aging pickup reminders | P1 | Collector | When a collector has an accepted pickup older than a configurable threshold (e.g., 24 hours without status change), send an in-app notification reminding them to progress the pickup. |
| **NEW-10** | Brand identity: logo and design tokens | P2 | All | Create a Waste-IQ logo file and define a Tailwind color/font token system. Apply consistently across navigation, dashboards, and public pages. |
| **NEW-11** | Address coarsening for unassigned pickups | P2 | Collector | Show only neighbourhood/district (not full street address) when collector views available (unassigned) pickups. Full address shown only after assignment acceptance. |
| **NEW-12** | Dealer inventory: self-source workflow | P2 | Dealer | Allow dealers to add their own material inventory (for resale) in addition to sourcing from platform lots. This increases marketplace inventory and dealer engagement. |
| **NEW-13** | Pickup rescheduling | P2 | Citizen | Allow citizens to propose a new preferred time for pending pickups, subject to collector confirmation. Useful when the original time was approximate. |
| **NEW-14** | Pilot-ready health dashboard | P2 | Admin | A single "pilot pulse" view showing: active pickups today, pickups this week, completion rate, open disputes, pending dealer approvals, aging pickups â€” all on one screen. |
| **NEW-15** | Municipality role (read-only) | P3 | Municipality | WIQ-015. Read-only role with access to zone-filtered analytics and CSV export. Low priority for initial pilot. |

---

## 9. Recommended Implementation Sequence

For a 30-day pilot, implement in this order:

### Days 1â€“7: Pilot Foundation
1. **Auto-lot creation** (NEW-01) â€” add "Create Lot" action on completed pickup detail. Eliminate manual admin bottleneck.
2. **Revenue reporting** (NEW-02) â€” calculate commission on purchase, surface GMV and platform revenue in admin analytics. This is the pilot's answer to "what did we earn?"
3. **CSV export** (NEW-03) â€” admin transaction export. Enables weekly pilot reporting without database access.

### Days 8â€“14: Collector Enablement
4. **Collector earnings dashboard** (NEW-04) â€” per-kg rates, total earnings, payment history. Without this, collectors will not engage.
5. **Estimated pickup value** (NEW-05) â€” show citizen approximate value at submission time. Sets pricing expectations early.
6. **Collector aging reminders** (NEW-09) â€” push notifications for stagnant pickups. Reduces "collector ghosting" risk.

### Days 15â€“21: Privacy and Trust
7. **Phone-redacted admin users API** (NEW-06) â€” reduce PII blast radius on admin account compromise.
8. **Production SMTP** (NEW-07) â€” configure and verify real email delivery. Non-negotiable for real users.
9. **Weight dispute evidence upload** (NEW-08) â€” scale photo upload for disputes. Improves resolution quality.

### Days 22â€“30: Polish and Brand
10. **Brand identity** (NEW-10) â€” logo, design tokens, consistent UI.
11. **Address coarsening** (NEW-11) â€” hide full address until assignment accepted.
12. **Pilot health dashboard** (NEW-14) â€” single-view operational pulse for the admin during the pilot.

---

## 10. Product Differentiation Strategy

Waste-IQ's strongest competitive position is not as "another waste pickup app" but as **the verifiable waste provenance platform**. Three mutually reinforcing differentiators:

**Differentiator 1 â€” Verified Weight (Trust Layer)**
No other waste collection platform offers citizens the ability to verify or dispute the weight recorded by a collector before that weight becomes a commercial transaction. This is a trust mechanism that enables:
- Citizen participation (they know they are not being cheated)
- Municipal buy-in (verified data for diversion reporting)
- ESG credibility (chain-of-custody for recycled material)

This is WIQ-V1-046, already implemented. The gap is that it is not prominently communicated in the UI or marketing materials.

**Differentiator 2 â€” Full Waste Traceability (Data Layer)**
Every gram of waste tracked from citizen request â†’ collector completion â†’ inventory lot â†’ dealer purchase â†’ transaction record. The `audit_log`, `pickup_request_event`, `inventory_lot_event`, and `marketplace_transaction` tables create an unbroken provenance chain. This enables:
- Municipality diversion reporting (verified by waste type and kg)
- ESG and carbon credit documentation
- Quality control (contamination rates by collector, area, material)

The infrastructure exists; the reporting UI is weak.

**Differentiator 3 â€” Recycler Access (Revenue Layer)**
The dealer marketplace converts Waste-IQ from a cost centre (managing pickups) into a revenue engine (marketplace commission). The 24-hour reservation system, row-locked purchases, and financial ledger provide the commercial infrastructure. With verified weight as the trust anchor, dealers have confidence in the material they are buying.

**Strategic message:** "Waste-IQ doesn't just collect waste â€” it creates a verifiable record of every gram recycled, building trust between citizens, collectors, and recyclers while generating measurable environmental and commercial impact."

---

## 11. 30-Day Pilot Definition

### Scope
- **Geographic area:** 1 city / 1 zone (e.g., one ward or pincode area)
- **Citizens:** Up to 100 registered users, limited to the pilot zone
- **Collectors:** 2â€“5 individuals, pre-screened, given collector portal access
- **Dealers/Recyclers:** 1â€“3 verified dealers, pre-approved before pilot start
- **Duration:** 30 days
- **Language:** English (future: Bengali / Hindi localization out of scope)

### Pilot Objectives
1. Validate the citizen-to-collector pickup workflow end-to-end.
2. Demonstrate weight verification and dispute resolution in practice.
3. Complete the first dealer inventory purchase and record the first platform commission.
4. Generate the first pilot report with measurable waste diversion data.
5. Identify top 5 product friction points from real user feedback.

### What Waste-IQ Must Do on Day 1 of the Pilot
- All 4 roles can register and log in
- Citizens can submit a pickup request with photo and GPS
- Collectors see available pickups on the map and can accept them
- Collectors can complete pickups and record weight
- Citizens can verify or dispute recorded weight
- Admins can resolve disputes
- Admins can create inventory lots from completed pickups
- Dealers can browse, reserve, and purchase lots
- Admins can view operational dashboard
- Admins can export data as CSV
- Real email delivery (verification, notifications)
- In-app notifications for all lifecycle events

### What is NOT Required for the Pilot
- Real AI waste classification
- Real Twilio masked communication (mock is acceptable for pilot)
- Municipality role
- Collector route optimization
- Payment gateway integration (offline settlement recording is fine)
- Mobile app (responsive web is sufficient)

---

## 12. Success Metrics

### Pilot Success Criteria (Day 30)

| Metric | Target | How Measured |
|--------|--------|-------------|
| Pickup completion rate | â‰¥ 70% of submitted pickups completed within 48 hours | `pickup_requests` status transitions |
| Citizen retention | â‰¥ 30% of citizens submit a 2nd pickup | `pickup_requests` by user_id |
| Weight disputes filed | â‰¤ 10% of completed pickups disputed | `pickup_dispute` count |
| Dealer purchase completed | â‰¥ 1 dealer purchase transaction | `marketplace_orders` |
| Platform GMV | â‰¥ â‚¹X (rate to be agreed before pilot) | `marketplace_transactions.total_amount` |
| Platform commission revenue | â‰¥ â‚¹Y (rate to be agreed before pilot) | `marketplace_transactions` + commission calc |
| CSV export used | â‰¥ 1 export by admin | Log / user feedback |
| No P0 incidents | Zero data loss, zero unauthorized access | Operational monitoring |

### Metrics the Product Can Currently Produce
- Total pickup requests (all statuses)
- Pickup completion rate (status = completed / total)
- Average time: request â†’ acceptance, acceptance â†’ completion
- Weight totals by collector, by material category
- Active users by role per week
- Carbon savings estimate (using 0.42 kg CO2e/kg constant)
- Material distribution (plastic/paper/metal/glass/e-waste/organic/other)
- Dealer profile approval funnel

### Metrics Missing from Current Product
- GMV (gross marketplace value) â€” not calculated
- Platform commission revenue â€” not calculated
- Collector earnings/payout â€” not tracked
- Pickup-to-sale conversion rate â€” not computed
- Average pickup value by material â€” not shown
- Dispute resolution time â€” not tracked (only `resolved_at` on dispute, no SLA measurement)

---

## 13. Detailed evidence and analysis

The remaining sections provide evidence-based audits per role, area, and risk.

### 13.1 Methodology

Every status in this document was verified against the actual working tree:

- **Code-level evidence** â€” exact `file:line` references from `backend/app/` and `frontend/src/`.
- **Test coverage** â€” verified by reading `backend/tests/` (39 test files).
- **Schema evidence** â€” Pydantic models in `backend/app/schemas/`.
- **Model evidence** â€” SQLAlchemy models in `backend/app/models/`.
- **Route evidence** â€” FastAPI route definitions in `backend/app/api/routes/`.
- **Existing documentation** â€” `docs/`, `CHANGELOG.md`, `CONTRIBUTING.md`.

The audit did **not** create issues, did **not** modify code, did **not** commit anything, and did **not** invoke `gh` CLI to create issues. All findings are based on local inspection.

---

## 14. Step 2: Feature inventory

| Area | Feature | Status | Evidence | Notes |
|------|---------|--------|----------|-------|
| **Authentication** | Email + password registration | IMPLEMENTED | `app/api/routes/auth.py:59â€“75` | Full Pydantic validation |
| | JWT access tokens (HS256) | IMPLEMENTED | `app/core/security.py:26â€“31` | Default 30 min, configurable |
| | Refresh token rotation | IMPLEMENTED | `app/services/refresh_token.py` | SHA-256 digest, family rotation |
| | Password reset (forgot) | IMPLEMENTED | `app/api/routes/auth.py:200â€“219` | Enumeration-safe, rate-limited |
| | Password reset (submit) | IMPLEMENTED | `app/api/routes/auth.py:222â€“240` | Revokes all sessions on success |
| | Email verification | IMPLEMENTED | `app/services/email_verification.py` | BackgroundTask dispatch, signed tokens |
| | Email verification resend | IMPLEMENTED | `app/api/routes/auth.py:177â€“197` | Per-IP rate limit |
| | Account lockout | IMPLEMENTED | `app/services/auth.py` | 5 failures â†’ 15 min lockout |
| | Login history | IMPLEMENTED | `app/api/routes/auth.py:269â€“297` | Per-user, paginated |
| | Password change | IMPLEMENTED | `app/api/routes/auth.py:300â€“316` | Revokes other sessions |
| | Logout (single) | IMPLEMENTED | `app/api/routes/auth.py:243â€“251` | Idempotent |
| | Logout-all | IMPLEMENTED | `app/api/routes/auth.py:254â€“261` | Revokes every session |
| **Authorization** | Role-based access (citizen/collector/dealer/admin) | IMPLEMENTED | `app/core/dependencies.py:require_roles` | Enforced on every protected route |
| | Email verification gate | IMPLEMENTED | `require_verified_user`, `require_verified_roles` | Required for pickup creation, dealer actions |
| | IDOR / BOLA protection | IMPLEMENTED | `_enforce_request_access` | Tested in `test_security_boundaries.py` |
| | Phone redaction from collector payloads | IMPLEMENTED | `app/services/pickup_requests.py:49â€“63` | `_should_expose_phone` helper |
| **Citizen** | Pickup request submission (multipart) | IMPLEMENTED | `app/api/routes/pickup_requests.py:40â€“65` | Zod + Pydantic validation |
| | Pickup status tracking | IMPLEMENTED | `GET /pickup-requests` | 8-state status model |
| | Pickup history | IMPLEMENTED | `app/services/pickup_requests.py` | Filtered by user |
| | Cancel pending request | IMPLEMENTED | `app/api/routes/pickup_requests.py:117â€“129` | Image cleanup on cancel |
| | Citizen pickup summary | IMPLEMENTED | `app/api/routes/pickup_requests.py:76â€“85` | `GET /pickup-requests/citizen/summary` |
| | Weight confirmation | IMPLEMENTED | `app/api/routes/pickup_requests.py:147â€“153` | `POST /pickup-requests/{id}/weight/confirm` |
| | Weight dispute | IMPLEMENTED | `app/api/routes/pickup_requests.py:156â€“163` | `POST /pickup-requests/{id}/weight/dispute` |
| | Profile view/edit | IMPLEMENTED | `frontend/src/pages/dashboard/ProfilePage.tsx` | |
| | Pickup history page | IMPLEMENTED | `frontend/src/pages/dashboard/PickupHistoryPage.tsx` | |
| **Collector** | Available pickups list | IMPLEMENTED | `GET /collector/pickups/available` | |
| | Assigned pickups list | IMPLEMENTED | `GET /collector/pickups/assigned` | |
| | Nearby pickups (Haversine) | IMPLEMENTED | `GET /collector/nearby` | DB-side approximation |
| | Pickup details (full) | IMPLEMENTED | `GET /collector/pickups/{id}` | Masked phone |
| | Accept assignment | IMPLEMENTED | `POST /collector/pickups/{id}/accept` | |
| | Start transit | IMPLEMENTED | `POST /collector/pickups/{id}/start` | â†’ `on_the_way` |
| | Mark collected | IMPLEMENTED | `POST /collector/pickups/{id}/collect` | â†’ `collected` |
| | Record weight | IMPLEMENTED | `POST /collector/pickups/{id}/record-weight` | â†’ `weight_recorded` |
| | Complete pickup | IMPLEMENTED | `POST /collector/pickups/{id}/complete` | Legacy path |
| | Cancel assignment | IMPLEMENTED | `POST /collector/pickups/{id}/cancel` | |
| | Live map (SVG) | IMPLEMENTED | `frontend/src/pages/dashboard/CollectorMapPage.tsx` | Geolocation, markers, route |
| | Route sequencing | IMPLEMENTED | `GET /collector/route` | Nearest-neighbour algorithm |
| | Geolocation reporting | IMPLEMENTED | `POST /collector/location` | `collector_locations` table |
| | Masked contact with citizen | IMPLEMENTED (mock) | `app/services/communication.py` | Twilio is a stub (501) |
| | Summary stats | IMPLEMENTED | `GET /collector/summary` | Counts by status |
| | Earnings / payout view | MISSING | â€” | NEW-04 |
| **Dealer/Recycler** | Business profile (CRUD) | IMPLEMENTED | `app/api/routes/dealer.py:35â€“78` | 4-state approval |
| | Profile submission | IMPLEMENTED | `POST /dealer/profile/submit` | |
| | Approval timeline | IMPLEMENTED | `GET /dealer/profile/timeline` | |
| | Marketplace browsing | IMPLEMENTED | `app/api/routes/marketplace.py:18â€“40` | Filtered by visibility |
| | Marketplace detail | IMPLEMENTED | `app/api/routes/marketplace.py:43â€“49` | |
| | Reserve lot (24h) | IMPLEMENTED | `app/api/routes/marketplace.py:52â€“62` | Row-locked |
| | Cancel reservation | IMPLEMENTED | `app/api/routes/marketplace.py:65â€“75` | |
| | Purchase (creates order) | IMPLEMENTED | `app/api/routes/marketplace.py:78â€“88` | |
| | Order history | IMPLEMENTED | `GET /marketplace/orders`, `GET /marketplace/orders/{id}` | |
| | Transaction history | IMPLEMENTED | `GET /marketplace/transactions` | |
| | Dealer profile approval (admin) | IMPLEMENTED | `POST /admin/dealers/{id}/approve|reject` | With reason |
| | Self-source inventory | MISSING | `DealerInventory` table exists but unused | NEW-12 |
| **Admin** | User listing | IMPLEMENTED | `GET /admin/users` | Returns full `UserRead` (incl. phone) |
| | Analytics overview | IMPLEMENTED | `GET /admin/analytics` | KPIs, trends, performance |
| | Dealer list/filter/search | IMPLEMENTED | `GET /admin/dealers` | Paginated, filterable |
| | Pending dealer queue | IMPLEMENTED | `GET /admin/dealers/pending` | |
| | Dealer approval workflow | IMPLEMENTED | `POST /admin/dealers/{id}/approve|reject` | Timeline recorded |
| | Inventory lot CRUD | IMPLEMENTED | `app/api/routes/inventory.py` | Filtered by status/city/visibility |
| | Archive/restore lot | IMPLEMENTED | `POST /admin/inventory-lots/{id}/archive|restore` | |
| | Material category CRUD | IMPLEMENTED | `app/api/routes/inventory.py:54â€“73` | |
| | Pricing rule CRUD | IMPLEMENTED | `app/api/routes/inventory.py:79â€“131` | Per kg, per city |
| | Notification broadcast | IMPLEMENTED | `POST /admin/notifications/broadcast` | Role-targeted |
| | Login history (all users) | IMPLEMENTED | `GET /admin/login-history` | Filtered by user/date |
| | Disputed pickups list | IMPLEMENTED | `GET /admin/disputes/pickups` | |
| | Resolve weight dispute | IMPLEMENTED | `POST /admin/disputes/pickups/{id}/resolve` | `upheld` or `corrected` |
| | Audit log | IMPLEMENTED | `app/api/routes/audit_logs.py` | |
| | Auto-create inventory lot | MISSING | â€” | NEW-01 |
| | CSV export | MISSING | â€” | NEW-03 |
| **Pickup** | 8-state lifecycle | IMPLEMENTED | `app/models/pickup_request.py:11â€“19` | pending/accepted/on_the_way/collected/weight_recorded/disputed/completed/cancelled |
| | Event log per pickup | IMPLEMENTED | `pickup_request_event` table | Actor-attributed |
| | GPS coordinates | IMPLEMENTED | Required in schema | |
| | Preferred time | IMPLEMENTED | Optional field | |
| | Notes (free text) | IMPLEMENTED | Optional, max 2000 chars | |
| | Image upload | IMPLEMENTED | Cloudinary + local fallback | |
| | Image cleanup on cancel | IMPLEMENTED | Uses `image_public_id` | |
| **Waste images** | Multipart upload | IMPLEMENTED | `POST /pickup-requests` | JPG/PNG/WEBP, â‰¤10MB |
| | Cloudinary storage | IMPLEMENTED | `app/services/upload.py` | |
| | Local storage fallback | IMPLEMENTED | `LocalFileUploader` | Simulation only |
| | Auto-classification (AI) | STUB | `app/services/ai_classifier.py:19â€“32` | Returns Unknown/0.0 |
| **Weight recording** | Collector records weight | IMPLEMENTED | `POST /collector/pickups/{id}/record-weight` | |
| | Stored on assignment | IMPLEMENTED | `CollectorAssignment.weight_kg` | |
| | Validation (positive float) | IMPLEMENTED | Pydantic | |
| | Idempotent on re-record | IMPLEMENTED | Returns 409 if changed | |
| **Weight verification** | Citizen confirms weight | IMPLEMENTED | `confirm_pickup_weight()` | â†’ `completed` |
| | Citizen disputes weight | IMPLEMENTED | `dispute_pickup_weight()` | â†’ `disputed` |
| | Admin sees dispute queue | IMPLEMENTED | `GET /admin/disputes/pickups` | |
| | Admin resolves (upheld) | IMPLEMENTED | `resolve_weight_dispute()` | Keeps original weight |
| | Admin resolves (corrected) | IMPLEMENTED | `resolve_weight_dispute()` | Stores new weight |
| | Dispute evidence upload | MISSING | â€” | NEW-08 |
| **Inventory** | Lot creation (admin) | IMPLEMENTED | `app/api/routes/inventory.py:189â€“198` | |
| | Auto-lot creation | MISSING | â€” | NEW-01 (WIQ-V1-053) |
| | Status enum (available/reserved/sold) | IMPLEMENTED | `app/models/inventory_lot.py:23â€“26` | |
| | Visibility (visible/hidden) | IMPLEMENTED | `app/models/inventory_lot.py:29â€“32` | |
| | Archive/restore | IMPLEMENTED | `POST /admin/inventory-lots/{id}/archive|restore` | |
| | Material category link | IMPLEMENTED | `material_category_id` FK | |
| | Pricing rule link | IMPLEMENTED | `pricing_rule_id` FK | |
| | Price snapshot at creation | IMPLEMENTED | `unit_price_per_kg_snapshot` | |
| | Source city/address snapshot | IMPLEMENTED | `source_city`, `source_address_snapshot` | |
| | Lot number auto-generated | IMPLEMENTED | Format `WIQ-<YYYYMM>-<id>` | |
| | Event log per lot | IMPLEMENTED | `inventory_lot_event` table | |
| **Marketplace** | Browse (dealer) | IMPLEMENTED | `GET /marketplace/inventory` | Filtered, paginated |
| | Filter by city/category/grade | IMPLEMENTED | Query params | |
| | Reserve (24h) | IMPLEMENTED | Row-locked, expires_at set | |
| | Cancel reservation | IMPLEMENTED | | |
| | Auto-expire reservations | IMPLEMENTED | `release_expired_reservations` job | Every 1 min |
| | Purchase (creates order) | IMPLEMENTED | | |
| | Order + transaction ledger | IMPLEMENTED | `MarketplaceOrder`, `MarketplaceTransaction` | |
| | Commission calculation | MISSING | Field exists, never populated | NEW-02 (WIQ-008) |
| **Reservations** | 24h TTL | IMPLEMENTED | `RESERVATION_TTL_HOURS = 24` | |
| | Auto-release background job | IMPLEMENTED | `reservation_sweep_job` | |
| | Manual release (admin) | IMPLEMENTED | | |
| | Reservation expiry notification | IMPLEMENTED | `notify_reservation_expired` | |
| **Transactions** | Marketplace order | IMPLEMENTED | Unique per lot | |
| | Transaction ledger | IMPLEMENTED | `MarketplaceTransaction` | |
| | Financial snapshot (unit price, total) | IMPLEMENTED | On order creation | |
| | Commission amount | MISSING | Field exists, never set | NEW-02 |
| **Notifications** | Per-user inbox | IMPLEMENTED | `notifications` table, paginated | |
| | Unread count | IMPLEMENTED | `GET /notifications/unread/count` | |
| | Mark read / read-all | IMPLEMENTED | `POST /notifications/{id}/read`, `POST /notifications/read-all` | |
| | Delete | IMPLEMENTED | `DELETE /notifications/{id}` | |
| | ~25 event helpers | IMPLEMENTED | `app/services/notifications.py` | |
| | Admin broadcast | IMPLEMENTED | `POST /admin/notifications/broadcast` | |
| **Email** | Provider abstraction | IMPLEMENTED | `app/services/email.py` | console or smtp |
| | Console backend (dev) | IMPLEMENTED | Redacted logs, in-process outbox | |
| | SMTP backend (prod) | STUB | `SMTP_*` config exists but not validated | NEW-07 |
| | Email templates (Jinja2) | IMPLEMENTED | Verification, password reset | |
| | BackgroundTask dispatch | IMPLEMENTED | SMTP I/O off the request path | |
| **Analytics** | Overview KPIs | IMPLEMENTED | `get_overview_analytics` | |
| | Material breakdown | IMPLEMENTED | Bucket counts by category | |
| | Monthly trends (12 mo) | IMPLEMENTED | `get_monthly_analytics` | |
| | Collector performance | IMPLEMENTED | Completion rate, avg response time | |
| | Dealer performance | IMPLEMENTED | Materials processed, total weight | |
| | Carbon savings | IMPLEMENTED | 0.42 kg CO2e/kg constant | |
| | Rule-based insights | IMPLEMENTED | `generate_insights` | |
| | GMV / platform revenue | MISSING | â€” | NEW-02 (WIQ-009) |
| | Export to CSV | MISSING | â€” | NEW-03 (WIQ-010) |
| **AI** | YOLOv8 classifier (interface) | IMPLEMENTED | `app/services/ai_classifier.py:5â€“17` | Abstract class |
| | YOLOv8 implementation | STUB | `app/services/ai_classifier.py:19â€“32` | Returns Unknown/0.0 |
| | Real inference | MISSING | â€” | Documented in CHANGELOG as `AI Waste Classification v2` but not implemented |
| **Maps/location** | Citizen GPS submission | IMPLEMENTED | Required field | |
| | Collector map (SVG) | IMPLEMENTED | Equirectangular projection | |
| | Nearby pickups (Haversine) | IMPLEMENTED | DB-side approximation | |
| | Geolocation reporting | IMPLEMENTED | `POST /collector/location` | |
| | Location history | IMPLEMENTED | `collector_location_history` | |
| | Route sequencing | IMPLEMENTED | Nearest-neighbour | |
| | Step-by-step navigation | IMPLEMENTED | `GET /collector/navigation/{id}` | |
| | Reverse geocoding | MISSING | â€” | Coordinates only |
| **Audit logging** | AuditLog table | IMPLEMENTED | `app/models/audit_log.py` | |
| | Actor attribution | IMPLEMENTED | `actor_user_id` | |
| | Sensitive field redaction | IMPLEMENTED | `SENSITIVE_KEYS` blocklist | |
| | Admin audit log route | IMPLEMENTED | `app/api/routes/audit_logs.py` | |
| **Background jobs** | APScheduler lifespan | IMPLEMENTED | `app/services/jobs.py:127â€“155` | |
| | Reservation sweep (1 min) | IMPLEMENTED | `reservation_sweep_job` | |
| | Aging pickup alerts (5 min) | IMPLEMENTED | `aging_pickup_alert_job` | |
| | Disabled in test env | IMPLEMENTED | `if settings.environment == "test"` | |
| **Storage** | Cloudinary | IMPLEMENTED | `app/services/upload.py:187â€“286` | |
| | Local filesystem fallback | IMPLEMENTED | `LocalFileUploader` | |
| **Security** | BCrypt password hashing | IMPLEMENTED | `app/core/security.py:11` | |
| | JWT HS256 | IMPLEMENTED | `app/core/security.py:26â€“31` | |
| | Refresh token rotation (SHA-256) | IMPLEMENTED | `app/services/refresh_token.py` | |
| | Per-IP rate limit | IMPLEMENTED | `app/core/ratelimit.py` | |
| | Per-account rate limit | IMPLEMENTED | Same module | |
| | Account lockout | IMPLEMENTED | `app/services/auth.py` | |
| | CORS configured | IMPLEMENTED | `app/main.py` | |
| | Security headers | MISSING | â€” | No CSP, HSTS, etc. |
| **Deployment** | Docker Compose (dev) | IMPLEMENTED | `docker-compose.yml` | |
| | Docker Compose (prod) | IMPLEMENTED | `docker-compose.prod.yml` | |
| | Multi-stage Dockerfile | IMPLEMENTED | `backend/Dockerfile` | |
| | Health endpoint | IMPLEMENTED | `/health`, `/health/ready` | |
| | Render.com config | IMPLEMENTED | `render.yaml` | |
| **Monitoring** | Sentry integration | IMPLEMENTED | `app/core/sentry_sdk.py` | |
| | Structured logging | IMPLEMENTED | `app/core/logging.py` | |
| | Health checks | IMPLEMENTED | `/health`, `/health/ready` | |
| | APM / request tracing | MISSING | â€” | OpenTelemetry not configured |

---

## 15. Step 3: User role map

### 15.1 Citizen

**Onboarding:**
- Registration via `RegisterPage` (`frontend/src/pages/auth/RegisterPage.tsx`)
- Email verification via signed link (`/verify-email`)
- Login with email + password
- Browser-geolocation auto-fill on first pickup form

**Dashboard** (`DashboardOverviewPage.tsx`):
- Welcome card with role-specific hero
- 4 stats: total / pending / accepted / completed pickups
- Recycling impact card (computed)
- Quick action grid
- Pending pickups list, upcoming pickup, recent activity
- Notifications panel

**Available actions:**
- Create pickup (multipart form, 3-step wizard: Material â†’ Location & Details â†’ Review)
- View pickup history
- Cancel pending pickup
- Confirm or dispute recorded weight
- Edit profile
- Update preferences
- View notifications (inbox + header bell)

**Important screens:**
- `/dashboard` â€” overview
- `/dashboard/pickups` â€” all pickups
- `/dashboard/pickups/new` â€” create pickup
- `/dashboard/pickups/:id` â€” pickup detail (with weight verification)
- `/dashboard/history` â€” pickup history
- `/dashboard/notifications` â€” notifications inbox

**Information displayed:**
- Own name, email, phone, role (via `GET /auth/me`)
- Own pickup requests (all statuses, with weight, dispute, timeline)

**Permissions:**
- Read: own pickups, own profile, own notifications
- Write: own profile, own pickups (create/cancel/verify/dispute)

**Workflow completion:**
- Citizen can complete: submit â†’ track â†’ verify weight â†’ completed
- Citizen cannot: bypass weight verification, edit completed pickup, view others' data

**Failure states:**
- Form validation errors (Zod) with inline messages
- API errors with retry
- Image upload failure (skipped silently per WIQ spec)
- Email verification pending (banner with resend)

**Missing functionality:**
- Estimated pickup value (NEW-05)
- Pickup rescheduling (NEW-13)
- Scale photo upload for disputes (NEW-08)
- Notification preferences
- Pickup template / recurring pickup
- Historical weight comparison

**Privacy concerns:**
- Full address + GPS visible to assigned collector (necessary for navigation)
- Phone number redacted from collector payloads (correct)
- No PII visible to other citizens
- Email not exposed to collectors

**UX problems:**
- 3-step wizard is heavyweight for a single submission; could be one page
- No way to track "where is my collector" (no live collector location visible to citizen)
- No "rate this pickup" or feedback loop

### 15.2 Collector

**Onboarding:**
- Registration with email + password
- Email verification required before accepting jobs (`require_verified_roles("collector")`)
- No additional collector vetting in current code (this is a gap)

**Dashboard** (`CollectorOverviewPage.tsx`):
- 6 stat tiles: Available Now, Total Assigned, Active Jobs, Completed Jobs, Material Types, Photo Attachments
- Collector Queue (available pickups with expand/collapse)
- My Active Pickups (with actions)

**Available actions:**
- Browse available pickups
- Browse nearby pickups (Haversine distance)
- Accept pickup (with email-verified requirement)
- Start transit (â†’ on_the_way)
- Mark collected (â†’ collected)
- Record weight (â†’ weight_recorded)
- Complete pickup (legacy direct-to-completed)
- Cancel assignment
- Initiate masked contact with citizen
- View live map with route
- Report geolocation

**Important screens:**
- `/collector` â€” overview
- `/collector/map` â€” live map with route
- `/collector/pickups/:id` â€” pickup detail
- `/collector/notifications` â€” notifications

**Information displayed:**
- Own name, email, phone
- Assigned pickups (full detail: address, GPS, notes, waste type, photo, estimated weight, actual weight)
- Citizen name and (redacted) phone
- Personal stats

**Permissions:**
- Read: assigned + available pickups (full address, photo)
- Write: own location, own pickup state transitions
- Cannot see: other collectors' assignments, citizen phone (redacted), admin data

**Workflow completion:**
- Collector can complete: accept â†’ start â†’ collect â†’ record weight
- If citizen disputes, collector is notified and waits for admin resolution

**Failure states:**
- Network failure during status update (retry needed)
- Photo upload failure (graceful)
- Geolocation permission denied (manual location entry)
- Image upload size limit (10MB)

**Missing functionality:**
- Earnings/payout view (NEW-04 â€” P0)
- Aging reminder notifications (NEW-09 â€” P1)
- Photo of collected waste (proof of collection)
- Quality assessment of waste
- Material categorization at pickup time
- Weight history for trend analysis
- Route optimization
- Tip rating from citizen

**Privacy concerns:**
- Sees full address before accepting (could be coarsened until acceptance, NEW-11)
- Phone redacted (correct)
- No way to rate or block a citizen
- No protection from harassment via masked contact

**UX problems:**
- 4â€“5 status transition clicks (accept, start, collect, record weight) â€” could be a single "I've arrived" + "Record weight" flow
- No offline mode
- No scale integration (manual weight entry)
- No photo evidence requirement

### 15.3 Dealer / Recycler

**Onboarding:**
- Registration with email + password
- Email verification required
- Business profile creation (business_name, owner_name, GST, license, materials_accepted, address, etc.)
- Profile submission for review
- Admin review and approval (or rejection with reason)

**Dashboard** (`DealerOverviewPage.tsx`):
- Wrapped in `DealerApprovalGate` â€” unapproved dealers see "pending approval" message
- 3 stats: Available Lots, Categories on This Page, Listed Weight on This Page
- Paginated marketplace lots grid

**Available actions:**
- Create / edit / submit business profile
- Browse available lots (filtered: visible, not archived, not reserved/sold)
- View lot detail
- Reserve lot (24-hour hold)
- Cancel reservation
- Purchase reserved lot
- View order history
- View transaction history
- Receive notifications

**Important screens:**
- `/dealer` â€” overview
- `/dealer/profile` â€” business profile (with approval timeline)
- `/dealer/marketplace` â€” marketplace browse
- `/dealer/marketplace/:id` â€” lot detail
- `/dealer/inventory` â€” own inventory (read-only currently)
- `/dealer/orders` â€” order history

**Information displayed:**
- Own business profile (status, timeline)
- Marketplace lots (category, weight, price, city, source)
- Own orders and transactions
- Own notifications

**Permissions:**
- Read: own profile, marketplace lots (visible only), own orders
- Write: own profile (until approved), own reservations, own purchases
- Cannot: see other dealers, see citizen PII, modify lot data, access admin features

**Workflow completion:**
- Dealer can complete: register â†’ submit profile â†’ wait for approval â†’ browse â†’ reserve â†’ purchase
- The "fulfilment" step (offline handoff) is recorded as a transaction but no online fulfillment workflow

**Failure states:**
- Profile submission validation errors
- Reservation expiry (auto-released after 24h)
- Insufficient quantity (not possible â€” lots are sold atomically)
- Payment failure (no payment gateway â€” offline settlement assumed)

**Missing functionality:**
- Self-source inventory (NEW-12 â€” P2)
- Bulk order request
- Demand listing (WIQ-013 â€” backlog)
- Material-specific browsing
- Direct communication with admin
- Dealer ratings / track record
- Tax / invoice generation

**Privacy concerns:**
- No PII visible from citizens
- No PII visible from collectors
- No PII visible from other dealers
- Correctly isolated

**UX problems:**
- "Fulfilment" step is invisible (transaction recorded, no logistics workflow)
- No clear time-to-fulfilment expectation
- No demand signal back to admins
- No way to request more of a specific material

### 15.4 Administrator

**Onboarding:**
- Bootstrap admin via `BOOTSTRAP_ADMIN_*` env vars
- No self-service admin registration
- Cannot be created via API

**Dashboard** (`AdminOverviewPage.tsx`):
- 4 KPI stats: Total Users, Pickup Requests, Completed Pickups, Collected Weight
- Pilot Metrics section (Collection KPIs, Workflow Timing, Weight Quality, Recent Activity, Operational Reliability)
- Dealer approval queue with approve/reject
- Pending users
- Dealer review sections

**Available actions:**
- View all users
- View platform analytics
- View, approve, reject dealer profiles
- Create, update, archive, restore inventory lots
- Manage material categories
- Manage pricing rules
- View all pickup requests
- View disputed pickups
- Resolve weight disputes (upheld or corrected)
- View admin login history
- View audit logs
- Broadcast notifications
- View flagged/missing shipments (no auto-lot creation yet)

**Important screens:**
- `/admin` â€” overview
- `/admin/analytics` â€” AI analytics dashboard
- `/admin/notifications` â€” notifications
- No dedicated admin pages for: dealer list, inventory list, disputes, users, audit logs (in current routes)

**Information displayed:**
- All user PII (name, email, phone, role) via `/admin/users` (PII risk)
- All pickup requests (full detail)
- All inventory lots
- All orders and transactions
- All notifications
- All login history
- All audit logs

**Permissions:**
- Read: all data
- Write: all data
- Cannot: bypass audit logging, delete records permanently (no soft-delete currently)

**Workflow completion:**
- Admin can complete: monitor â†’ approve dealers â†’ create lots â†’ resolve disputes â†’ export reports
- Missing: auto-lot creation, CSV export, commission configuration UI

**Failure states:**
- Cannot find a user (no search in `/admin/users`)
- Cannot see the full dispute history per pickup
- Cannot batch-approve dealers

**Missing functionality:**
- Auto-lot creation (NEW-01 â€” P0)
- CSV export (NEW-03 â€” P0)
- Commission configuration UI (NEW-02 â€” P0)
- User search/filter (currently flat list)
- Batch operations
- Municipal role (WIQ-015)
- Zone reporting (WIQ-016)
- Pilot health dashboard (NEW-14 â€” P2)

**Privacy concerns:**
- Sees all user phone numbers via `/admin/users` (recommend split endpoint, NEW-06)
- Sees all pickup addresses
- No segregation of admin views (all admins see everything)
- No admin action logs visible to other admins

**UX problems:**
- No dedicated pages for: dealer list, inventory list, users, audit logs, disputes â€” everything on the overview
- No filtering or search on most lists
- No "action history" view per user/pickup
- Cannot drill down from analytics to underlying records

---

## 16. Step 4: Waste lifecycle map

The full waste lifecycle is the central question for Waste-IQ. Here is every transition with current status:

| Transition | Implemented? | API support | Frontend support | Auth | Validation | State transition | Audit trail | Notification | Failure handling | Concurrency | Notes |
|------------|-------------|-------------|------------------|------|-----------|------------------|-------------|--------------|------------------|-------------|-------|
| Citizen registers | YES | `POST /auth/register` | RegisterPage | Public | Pydantic + Zod | n/a | YES (registration event) | Verification email | n/a | n/a | |
| Email verified | YES | `POST /auth/verify-email` | VerifyEmailPage | Public | Signed token | `email_verified_at` | YES | n/a | Generic 400 | n/a | |
| Citizen logs in | YES | `POST /auth/login` | LoginPage | Public | Pydantic | n/a | YES (`login_success`/`login_failure`) | n/a | 401, lockout, rate limit | n/a | |
| Citizen submits pickup | YES | `POST /pickup-requests` | NewPickupPage | Verified citizen | Pydantic + Zod | `pending` | YES (event) | `pickup_created` | Image optional | n/a | |
| Collector browses available | YES | `GET /collector/pickups/available` | CollectorOverviewPage | Collector | n/a | n/a | n/a | n/a | Empty list | n/a | |
| Collector accepts | YES | `POST /collector/pickups/{id}/accept` | CollectorActions | Verified collector | Status check | `pending â†’ accepted` | YES | `pickup_accepted` | 409 if not pending | YES (likely row-locked) | |
| Collector starts | YES | `POST /collector/pickups/{id}/start` | CollectorActions | Assigned collector | Status check | `accepted â†’ on_the_way` | YES | `pickup_started` | 409 if not assigned | YES | |
| Collector marks collected | YES | `POST /collector/pickups/{id}/collect` | CollectorActions | Assigned collector | Status check | `on_the_way â†’ collected` | YES | `pickup_collected` | 409 if wrong state | YES | |
| Collector records weight | YES | `POST /collector/pickups/{id}/record-weight` | CollectorActions | Assigned collector | Pydantic (positive float) | `collected â†’ weight_recorded` | YES | `weight_verification_pending` | 409 if re-record | YES | |
| Citizen confirms weight | YES | `POST /pickup-requests/{id}/weight/confirm` | PickupDetailsPage | Owning citizen | Status check | `weight_recorded â†’ completed` | YES | `weight_confirmed` | Idempotent | YES | |
| Citizen disputes weight | YES | `POST /pickup-requests/{id}/weight/dispute` | PickupDetailsPage | Owning citizen | Status check + reason | `weight_recorded â†’ disputed` | YES | `weight_disputed` | 409 if re-dispute | YES | |
| Admin resolves dispute | YES | `POST /admin/disputes/pickups/{id}/resolve` | AdminDisputeQueue | Admin | Status + resolution | `disputed â†’ completed` | YES | `dispute_resolved` | 400 if invalid | YES | |
| Admin creates inventory lot | YES (manual) | `POST /admin/inventory-lots` | AdminInventoryPage | Admin | Pydantic | n/a | YES (lot created event) | `inventory_created` | Duplicate lot 400 | n/a | **Manual â€” NEW-01 should automate** |
| Dealer browses lots | YES | `GET /marketplace/inventory` | MarketplacePage | Approved dealer | n/a | n/a | n/a | n/a | Empty list | n/a | |
| Dealer reserves lot | YES | `POST /marketplace/inventory/{id}/reserve` | MarketplacePage | Approved dealer | Status check | `available â†’ reserved` | YES | `inventory_reserved` | 409 if already reserved | YES (row-locked) | 24h TTL |
| Dealer cancels reservation | YES | `POST /marketplace/inventory/{id}/cancel-reservation` | MarketplacePage | Reserving dealer | Status check | `reserved â†’ available` | YES | `reservation_cancelled` | 409 if not reserver | YES | |
| Auto-release expired reservation | YES | `release_expired_reservations` job | n/a | System | n/a | `reserved â†’ available` | YES | `reservation_expired` | Job every 1 min | YES | |
| Dealer purchases | YES | `POST /marketplace/inventory/{id}/purchase` | MarketplacePage | Approved dealer | Status + reservation ownership | `reserved â†’ sold` | YES | `inventory_purchased` | 409 if not reserved | YES (row-locked) | |
| Admin fulfils order | MISSING | â€” | â€” | â€” | â€” | â€” | â€” | â€” | â€” | â€” | **No fulfilment workflow â€” gap** |
| Collector gets paid | MISSING | â€” | â€” | â€” | â€” | â€” | â€” | â€” | â€” | â€” | **NEW-04 â€” P0** |
| Material reaches recycler | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | **Offline handoff only** |
| Recycling / recovery | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | **Out of platform scope** |

### Where the workflow currently stops

The workflow **functionally stops at dealer purchase**. The following steps are missing or implicit:

1. **Auto-lot creation** â€” every completed pickup requires manual admin action to become an inventory lot.
2. **Order fulfilment** â€” the purchase transaction is recorded but no online workflow tracks handoff.
3. **Collector payout** â€” the collector's earnings from the sale are not recorded.
4. **Platform commission** â€” the `MarketplaceTransaction` records `total_amount` but never calculates `platform_revenue_amount`.
5. **Material arrival at recycler** â€” no tracking of physical handoff.
6. **Recycling / recovery** â€” entirely out of platform scope.

For the pilot, the implicit offline steps (handoff, recycling) are acceptable. The blockers are: auto-lot creation, commission calculation, collector payout.

---

## 17. Step 5â€“8: Per-role product audit summary

Detailed per-role audits are provided in Section 15. This section summarises the top 3 problems per role.

### Citizen â€” top 3 problems
1. **No estimated value at submission** â€” citizens create pickups without knowing the material's worth. Reduces motivation and pricing transparency.
2. **No scale photo on weight dispute** â€” citizens must file a weight dispute with text only. Reduces dispute resolution quality.
3. **No pickup rescheduling** â€” if the citizen's plans change, they must cancel and recreate.

### Collector â€” top 3 problems
1. **No earnings view** â€” collectors cannot see how much they've earned or will earn. This is a retention risk in any pilot.
2. **Aging reminders absent** â€” collectors who accept a pickup but do not progress receive no automated nudge. Admins are notified, but the collector is not.
3. **Multi-step status flow** â€” accept, start, collect, record weight is 4 separate actions. Could be condensed.

### Dealer / Recycler â€” top 3 problems
1. **No fulfilment workflow** â€” after purchase, the dealer has no tracking of handoff. A simple "mark received" button would close the loop.
2. **No self-source inventory** â€” dealers cannot list material they already have for resale, limiting marketplace inventory.
3. **No demand signals** â€” dealers cannot tell the platform "I want 100 kg of PET this week." Backlog WIQ-013.

### Administrator â€” top 3 problems
1. **No auto-lot creation** â€” manual lot creation is unsustainable at pilot scale.
2. **No revenue / commission reporting** â€” cannot answer "what did we earn?"
3. **No CSV export** â€” every report requires database access.

---

## 18. Step 9: Trust / privacy / security audit

The platform has solid security foundations: bcrypt password hashing, JWT with rotation, refresh token family revocation, per-IP and per-account rate limiting, account lockout, audit logging with sensitive-field redaction, and IDOR/BOLA protection tested in `test_security_boundaries.py`. This audit focuses on residual gaps.

### 18.1 Privacy gaps

| Gap | Severity | Recommendation |
|-----|----------|----------------|
| `/admin/users` returns all user `phone` numbers | HIGH | NEW-06: Split into listing (phone-redacted) and detail endpoints. |
| Collector sees full address before acceptance | MEDIUM | NEW-11: Coarsen address (neighbourhood only) for unassigned pickups. |
| Twilio masked communication is a 501 stub | LOW (for pilot) | Acceptable â€” mock provider is sufficient for 100-citizen pilot. Plan Twilio integration for production scale. |
| Waste photo (URL) is public to the assigned collector | LOW | Acceptable â€” only assigned collector sees the photo; photo is the citizen's documentation of the waste type. |
| Default JWT secret in development is `"change-me"` | HIGH (production) | Production deployment MUST set a strong `JWT_SECRET_KEY`. Documented in `.env.example`. |
| No reverse geocoding of coordinates | LOW | Acceptable for pilot â€” admin can use external tools if needed. |
| Admin sees all pickup addresses | LOW (admin) | Acceptable â€” admin role has full visibility by design. |

### 18.2 Authentication & authorisation

| Check | Status | Evidence |
|-------|--------|----------|
| BCrypt password hashing | YES | `app/core/security.py:11` |
| JWT signed with HS256 | YES | `app/core/security.py:26â€“31` |
| Refresh tokens (SHA-256 digests) | YES | `app/services/refresh_token.py` |
| Refresh token rotation | YES | Family rotation with reuse detection |
| Password reset (forgot) | YES | `app/api/routes/auth.py:200â€“219` |
| Password reset (submit) | YES | `app/api/routes/auth.py:222â€“240` |
| Email verification | YES | `app/services/email_verification.py` |
| Role-based access control | YES | `app/core/dependencies.py:require_roles` |
| Email-verified requirement | YES | `require_verified_user`, `require_verified_roles` |
| Per-IP rate limit (login, register, forgot, resend) | YES | `app/core/ratelimit.py` |
| Per-account rate limit (login) | YES | Same module |
| Account lockout (5 failures / 15 min) | YES | `app/services/auth.py` |
| CORS configured | YES | `app/main.py` |
| CORS middleware order fix | YES | Recorded in CHANGELOG 0.2.0 |
| Security headers (CSP, HSTS) | MISSING | â€” |
| JWT secret rotation | MISSING | Out of scope for MVP |
| Two-factor authentication | MISSING | Out of scope for MVP |
| OAuth / social login | MISSING | Out of scope for MVP |

### 18.3 Audit logging

| Check | Status |
|-------|--------|
| Every state-changing action logged | YES |
| Actor attribution | YES |
| Sensitive field redaction (`password`, `token`, `phone`, etc.) | YES |
| Admin can view logs | YES |
| Per-user login history | YES |
| Admin-wide login history | YES |
| Per-resource timeline views | YES (pickup, inventory, dealer) |

### 18.4 Collector â†” Citizen communication model

This is a core privacy consideration. The current model is:

**What the collector currently sees:**
- Citizen's full name
- Citizen's full address (street, GPS coordinates)
- Citizen's waste type and notes
- Citizen's uploaded photo

**What the collector does NOT see:**
- Citizen's phone number (redacted â€” see `_should_expose_phone` in `pickup_requests.py`)
- Citizen's email

**What the collector SHOULD see (recommended):**
- All of the above
- PLUS: estimated pickup time, special instructions, building/floor/landmark details
- PLUS: a "contact citizen" button (already implemented via masked relay)

**What the collector should NOT see:**
- Citizen's raw phone number
- Citizen's raw email
- Other pending pickups from the same citizen (privacy)
- The citizen's history with other collectors

**What the citizen should see (recommended):**
- The collector's first name only (no full name)
- The collector's profile photo (if uploaded)
- The collector's aggregate rating (if implemented)
- The collector's vehicle type / number (if implemented)

**Recommendation â€” privacy-preserving communication approach:**

1. **In-app messaging thread** (current pattern with `MockMaskedCommunicationProvider`) â€” best path forward. Both parties see only platform-mediated messages. No real phone numbers exposed.
2. **Masked proxy phone** (Twilio proxy or similar) â€” for a future production pilot when the masked in-app messaging needs voice.
3. **Single-use deep links** â€” for "call citizen once" or "open maps" without exposing phone.
4. **Collector rating and feedback** â€” citizens rate collectors post-pickup, creating accountability without exposing identity.

For the 30-day pilot, the in-app messaging mock is sufficient. Phone redaction is correctly implemented and tested. The main residual risk is the `/admin/users` endpoint exposing all phones (NEW-06).

### 18.5 Security summary

The platform's security posture is strong for an MVP. The residual P0 gap is `/admin/users` exposing all phone numbers; the residual P2 gap is missing security headers. The platform is ready for a small pilot with the caveats in Section 6.

---

## 19. Step 10: Weight trust model

The weight verification workflow is the **core differentiator** of Waste-IQ. It was implemented in WIQ-V1-046 and is fully functional.

### Current implementation

**Flow:**
1. Collector records weight on `POST /collector/pickups/{id}/record-weight` (line 562 in `pickup_requests.py`).
2. Status transitions `collected â†’ weight_recorded`.
3. Citizen receives `notify_weight_verification_pending` notification.
4. Citizen either:
   - Confirms via `POST /pickup-requests/{id}/weight/confirm` â†’ `weight_recorded â†’ completed`.
   - Disputes via `POST /pickup-requests/{id}/weight/dispute` (with reason) â†’ `weight_recorded â†’ disputed`.
5. If disputed, admin reviews via `GET /admin/disputes/pickups` and resolves via `POST /admin/disputes/pickups/{id}/resolve` with either:
   - `upheld` â€” original weight kept, status â†’ `completed`.
   - `corrected` â€” new weight stored on `dispute.resolved_weight_kg`, status â†’ `completed`.

**Validation:**
- Weight must be a positive float (Pydantic validation).
- Idempotent: re-recording same weight returns current state.
- 409 if different weight re-recorded on `weight_recorded` status.
- 409 if dispute reason re-submitted with different content.

**Audit trail:**
- `pickup_weight_recorded` event
- `pickup_dispute_resolved` event
- `pickup_dispute_reviewed` event

**Notifications:**
- `notify_weight_verification_pending` (to citizen)
- `notify_weight_confirmed` (to collector)
- `notify_weight_disputed` (to collector and admin)

### Missing elements

| Element | Severity | Notes |
|---------|----------|-------|
| **Scale photo evidence** | P1 (NEW-08) | Citizens can file a text reason but cannot upload a scale photo. Reduces dispute resolution quality. |
| **Collector-side weight confidence** | P3 | No way for collector to flag uncertain weight (e.g., "estimate only"). |
| **Multiple weight attempts** | P3 | No support for re-weighing on-site. |
| **Auto-validation of weight vs. estimate** | P2 | If actual weight differs by >50% from estimate, flag for review. |
| **Dispute resolution SLA** | P2 | No SLA tracking on `resolved_at - disputed_at`. |
| **Weight tamper detection** | P3 | No statistical anomaly detection (e.g., a collector consistently under-weights). |

### Manipulation risks

| Risk | Mitigation status |
|------|-------------------|
| Collector overstates weight to inflate inventory value | PARTIALLY MITIGATED â€” citizen can dispute; admin can review; commission % caps upside. |
| Citizen disputes legitimate weight out of spite | PARTIALLY MITIGATED â€” admin resolution; but no friction for frivolous disputes. |
| Admin colludes with collector | NOT MITIGATED â€” admin can resolve "corrected" with any value. Audit log records action but no secondary review. |
| Collector and admin collude | NOT MITIGATED â€” same as above. |
| Photo is not from a scale | NOT MITIGATED â€” no way to verify photo authenticity. |
| Weight entered at pickup is wrong (typo) | MITIGATED â€” citizen confirm/dispute catches this. |

### Robust MVP weight-verification workflow

The current implementation is already close to the recommended MVP. Enhancements for production:

1. **Required scale photo** (NEW-08) â€” both collector and citizen can attach a scale photo. The collector's photo is uploaded at weight recording; the citizen's photo is uploaded at dispute.
2. **Outlier detection** â€” flag pickups where actual weight is >50% off the citizen's estimate; require a scale photo automatically.
3. **Audit log enrichment** â€” record device fingerprint or geolocation at weight recording to support fraud investigation.
4. **SLA on dispute resolution** â€” admin dashboard shows time-since-dispute; a pickup in `disputed` state for >48h triggers a reminder.
5. **Two-step admin resolution** â€” for `corrected` resolutions, require a second admin's approval (four-eyes principle). This is out of scope for the 30-day pilot.

### Conclusion on weight trust

The current weight trust model is **functional and tested**. The main gap for a production-grade system is the scale photo evidence (NEW-08) and the four-eyes principle for high-value corrections. For the 30-day pilot, the current model is acceptable as long as admins are vigilant.

---

## 20. Step 11: Inventory / marketplace audit

### Current implementation

**Inventory lot lifecycle:**
1. Admin manually creates a lot from a completed pickup via `POST /admin/inventory-lots`.
2. Lot has a unique number (`WIQ-<YYYYMM>-<id>`), 1:1 with a pickup.
3. Lot is `available` by default; can be archived, restored, hidden.
4. Dealers browse via `GET /marketplace/inventory` (filter: available, not archived, visible).
5. Dealer reserves â†’ `reserved` with 24h TTL; auto-released on expiry.
6. Dealer purchases â†’ `sold`; `MarketplaceOrder` and `MarketplaceTransaction` created.
7. Event log records every state change.

**Cross-reference with WIQ-V1-053 / issue #111 (auto-lot creation):**
- WIQ-V1-053 spec is in `dealer-marketplace-mvp-spec.md` Â§FR-4: "auto-create lot when pickup status becomes completed and actual weight is present".
- **Current status: NOT IMPLEMENTED.** Admin must create the lot manually.
- This is a high-priority gap. See NEW-01.

**Quantity representation:**
- `weight_kg` is the lot's quantity (positive float).
- Lots are sold atomically â€” no partial sale.

**Material categories:**
- Admin-managed via `pricing_rule` and `material_category` tables.
- `InventoryLot.material_category_id` links to the category.
- `InventoryLot.material_description` is a free-text description.

**Reservations:**
- 24-hour TTL, stored on `reservation_expires_at`.
- Auto-released by `release_expired_reservations` background job (every 1 minute).
- Manual cancellation allowed.

**Concurrency protection:**
- Reserve uses `SELECT ... FOR UPDATE` row lock (line 1135 in `inventory_marketplace.py`).
- Purchase uses same row lock.
- This is correct and tested.

**Audit trail:**
- `inventory_lot_event` table records every state change with actor attribution and JSON metadata.

### Cross-reference with issue #111 / WIQ-V1-053

The repo's `dealer-marketplace-mvp-spec.md` Â§FR-4 specifies auto-lot creation. This is the same as the WIQ-V1-053 backlog item. The current state is:

| Spec requirement | Current state | Gap |
|------------------|----------------|-----|
| Auto-create on completion | NOT IMPLEMENTED | NEW-01 (P0) |
| Auto-populate category | PARTIALLY â€” category from `pickup_request.category` (AI-inferred) | OK if AI is bypassed |
| Auto-populate weight | NOT IMPLEMENTED â€” admin must specify | NEW-01 |
| Auto-populate pricing | PARTIALLY â€” `unit_price_per_kg_snapshot` from active pricing rule (line 661) | OK |
| Source address snapshot | IMPLEMENTED | OK |
| Source city | IMPLEMENTED | OK |
| Admin can override before publishing | NOT POSSIBLE â€” there is no draft state | NEW-01 should add a draft state |

### Remaining gaps

| Gap | Severity | Notes |
|-----|----------|-------|
| **Auto-lot creation** | P0 (NEW-01) | The biggest single operational bottleneck. |
| **Draft lot state** | P2 | Allow admin to review before lot goes visible. |
| **Lot quality grade** | IMPLEMENTED | But no UI to set; admin can only set in API. |
| **Lot admin notes** | IMPLEMENTED | But no UI to set. |
| **Bulk lot actions** | P3 | No batch archive/restore. |
| **Lot image (in addition to pickup image)** | P3 | Dealers see the original pickup image but no clear inventory photo. |
| **Demand listings** | P3 (WIQ-013) | Dealers cannot post "I want 100 kg PET." |
| **Multi-buyer lot (split)** | P3 | Out of scope for MVP. |

### Concurrency review

The reserve and purchase operations both use `SELECT ... FOR UPDATE`. This is correct for the current scale. For higher scale, consider:

- Optimistic locking via a `version` column on `InventoryLot`.
- Idempotency keys on POST endpoints.

For the 30-day pilot, row locking is sufficient.

### Conclusion on inventory

The inventory and marketplace are well-architected and tested. The single critical gap is auto-lot creation (NEW-01). With that, the inventory system is pilot-ready.

---

## 21. Step 12: Business model audit

### Current state

Waste-IQ is currently a **pre-revenue operations platform**. The software supports a complete pickup workflow and a marketplace of inventory lots, but the financial layer is incomplete.

### What the current product can measure

| Metric | How measured | Status |
|--------|--------------|--------|
| **Pickup count** | `pickup_requests` total | YES |
| **Pickup count by status** | `pickup_requests` filtered | YES |
| **Kg collected** | `CollectorAssignment.weight_kg` summed | YES |
| **Kg by material** | `pickup_request.waste_type` bucketed | YES (rule-based) |
| **Collector activity** | `pickup_requests` by assigned collector | YES |
| **Dealer activity** | `inventory_lot` reserved_by_dealer_id | YES |
| **Inventory** | `inventory_lot` count by status | YES |
| **Reservations** | `inventory_lot` where status=reserved | YES |
| **Sales** | `marketplace_order` count | YES |
| **Transaction value (gross)** | `marketplace_transaction.total_amount` summed | YES |
| **Revenue** | None | MISSING â€” NEW-02 |
| **Collector payout** | None | MISSING â€” NEW-04 |
| **Margin** | None | MISSING |
| **Cost** | None | Not tracked |

### What the current product enables

- **Operations visibility** â€” admin can see pickup counts, completion rates, weight totals, dealer approval status, dispute counts.
- **Audit-grade traceability** â€” every pickup has a complete event log; every lot has state changes; every transaction is recorded.
- **Marketplace operations** â€” dealers can browse, reserve, purchase; the financial ledger is in place (just missing commission calculation).
- **ESG and diversion reporting** â€” the carbon savings constant (0.42 kg CO2e/kg) is computed; material breakdown is available.

### What is required to operate a sustainable pilot

1. **Commission configuration** â€” admin must be able to set a commission percentage. Currently a hard-coded value is the only option, and even that is not surfaced.
2. **Collector payout rates** â€” per-kg rates by material, configurable by admin. Required to calculate collector earnings.
3. **GMV reporting** â€” gross marketplace value calculated and displayed in admin analytics.
4. **Platform revenue reporting** â€” commission earned calculated and displayed.
5. **Payout workflow** â€” record when a collector has been paid (manual entry or integration with payment gateway).
6. **CSV export** â€” for reconciliation, investor reporting, and municipality handoff.

### Business model recommendation (for the 30-day pilot)

Without inventing a complex model, the simplest sustainable pilot model is:

- **Commission** â€” Waste-IQ takes a flat 10% commission on every completed dealer purchase.
- **Collector payout** â€” collector receives 80% of the lot value. Waste-IQ retains 20% (10% of which is platform commission, 10% of which covers platform operations).
- **Pricing** â€” admin sets per-kg price per material category. Used for inventory lot pricing and collector payout.
- **Settlement** â€” offline. Admin records payout manually. CSV export for reconciliation.

This model is implementable in 1â€“2 sprints (NEW-02 + NEW-04).

### What is NOT required for the 30-day pilot

- Real payment gateway
- Automated payouts
- Tax calculation
- Multi-tier commission (e.g., volume discounts)
- Subscription models
- Marketplace fees for dealers

---

## 22. Step 13: Analytics audit

### What analytics currently exist

| Analytics | Implemented | Endpoint | Frontend |
|-----------|-------------|----------|----------|
| **Total users** | YES | `GET /admin/analytics` | AdminOverviewPage |
| **Total pickup requests** | YES | Same | Same |
| **Pickups by status** | YES | Same | Same |
| **Total weight (kg)** | YES | Same | Same |
| **Completion rate** | YES | Same | Same |
| **Material breakdown** | YES | Same | Same |
| **12-month pickup trend** | YES | Same | Same |
| **Collector performance** | YES | Same | Same |
| **Dealer performance** | YES | Same | Same |
| **Carbon savings (kg CO2e)** | YES | Same | Same |
| **Rule-based insights** | YES | Same | Same |
| **Pilot metrics** | YES | `get_pilot_metrics` | AdminOverviewPage |
| **Weight quality (estimate vs actual)** | YES | Same | Same |
| **Dispute counts (upheld/corrected)** | YES | Same | Same |
| **Aging pickup alerts** | YES | Background job | Admin notifications |
| **GMV** | MISSING | â€” | NEW-02 |
| **Platform commission revenue** | MISSING | â€” | NEW-02 |
| **Collector earnings** | MISSING | â€” | NEW-04 |
| **Pickup-to-sale conversion rate** | MISSING | â€” | NEW-02 |
| **Material revenue by category** | MISSING | â€” | NEW-02 |
| **Export to CSV** | MISSING | â€” | NEW-03 |

### Minimum pilot dashboard (recommended)

The current AdminOverviewPage is comprehensive but lacks commercial KPIs. For the pilot, recommend a **single "pilot pulse" view** that surfaces:

**Operations:**
- Pickup requests today
- Pickup requests this week
- Pickup completion rate (last 7 days)
- Average pickup time (request â†’ completion)
- Failed pickups (cancelled or disputed)

**Waste:**
- Total kg collected (today / this week / this month)
- Kg by material (last 7 days)
- Average kg per pickup
- Rejected / contaminated material (future)

**Collectors:**
- Active collectors (last 7 days)
- Pickups per collector (last 7 days)
- Acceptance rate (accepted / available)
- Completion rate (completed / accepted)
- Aging pickups (accepted >24h without progress)

**Marketplace:**
- Available inventory (kg + lot count)
- Reserved inventory (kg + lot count)
- Sold inventory (kg + lot count, last 7 days)
- Inventory turnover (sold / available)

**Business (NEW-02):**
- Material revenue (last 7 days)
- Collection cost (NEW-04)
- Logistics cost (out of scope for pilot)
- Collector payout (NEW-04)
- Contribution margin

**Disputes:**
- Open disputes (currently in `disputed` state)
- Disputes filed (last 7 days)
- Disputes upheld (admin confirmed collector's weight)
- Disputes corrected (admin changed weight)
- Average resolution time

### Currently implemented vs recommended

The product implements the **operational layer** of analytics well. The **commercial layer** (GMV, revenue, payout) is missing. For the pilot, focus on closing the commercial gap first (NEW-02) and the export gap (NEW-03). The operational analytics are already strong.

---

## 23. Step 14: AI audit

### Current state

The AI classifier in `app/services/ai_classifier.py` is a **stub**. The `YOLOv8Classifier.classify_image` method:

```python
def classify_image(self, image_path: str) -> dict[str, Any]:
    # TODO: Implement actual YOLOv8 inference here.
    # For now, returning a mock response as required (Do not call AI yet).
    mock_category = "Unknown"
    mock_confidence = 0.0
    mock_detections: list[dict[str, Any]] = []
    return {
        "category": mock_category,
        "confidence": mock_confidence,
        "detections": mock_detections,
    }
```

This is correctly:
- Wired into the image upload pipeline (`PickupRequestImageService.__init__`).
- Dependency-injected via `app/core/dependencies.py:99â€“100, 142`.
- Handled gracefully in the frontend (`NewPickupPage.tsx:504â€“507`).
- Acknowledged in the CHANGELOG.

**Verdict: STUB. Returns `{"category": "Unknown", "confidence": 0.0, "detections": []}` regardless of input.**

### Potential real AI use cases

For each, the audit considers: problem, required data, expected value, complexity, pilot relevance, recommendation.

| Use case | Problem | Required data | Expected value | Complexity | Pilot relevance | Recommendation |
|----------|---------|---------------|----------------|------------|----------------|----------------|
| **Waste classification** | Automatically categorise waste at submission | Labelled images of plastic, paper, metal, glass, e-waste, organic | Faster citizen submission; better admin inventory categorisation | HIGH (model training, infrastructure) | LOW | **Defer to post-pilot.** Real value requires hundreds of labelled images per category. |
| **Material classification** | Distinguish PET vs HDPE, grade A vs B | Specialised labelled dataset | Improved dealer pricing | HIGH | LOW | **Defer.** Without a labelled dataset, this is a research project. |
| **Image quality checking** | Detect blurry, dark, or non-waste images | None â€” pure computer vision | Reduce citizen submission errors | MEDIUM | MEDIUM | **Consider for V1.1.** Low-hanging fruit; improves data quality. |
| **Contamination detection** | Detect contaminated recyclable loads | Labelled contaminated/clean images | Deeper trust with dealers | HIGH | LOW | **Defer.** Requires significant training data. |
| **Pickup prediction** | Forecast which areas will have pickups tomorrow | Historical pickup data (city, time, weather) | Better collector assignment | MEDIUM | MEDIUM | **Consider post-pilot.** Needs 6+ months of historical data. |
| **Collector assignment** | Auto-assign the best collector for a pickup | Collector performance history, location, capacity | Improved acceptance and completion rates | MEDIUM | MEDIUM | **Consider for V1.1.** |
| **Route optimization** | Sequence pickups to minimise travel time | Pickup locations, current collector location, traffic | Reduced fuel costs, faster completion | MEDIUM (existing nearest-neighbour is a baseline) | HIGH | **Already partially implemented (nearest-neighbour).** True ML-based optimization needs more data. |
| **Demand forecasting** | Predict material demand from dealers | Historical purchases, dealer preferences | Better inventory planning | MEDIUM | LOW | **Defer to post-pilot.** |
| **Anomaly detection** | Flag unusual patterns (collector under-weights, dealer no-shows) | Time-series of weights, completion rates | Fraud detection | MEDIUM | MEDIUM | **Consider for V1.1.** Could surface disputes proactively. |
| **Recycler matching** | Match lots to dealers based on past purchases | Dealer history, lot characteristics | Increased marketplace conversion | MEDIUM | MEDIUM | **Consider for V1.1.** |

### AI recommendation for the 30-day pilot

**Do NOT add AI to the pilot.** The pilot's value is in validating the operational workflow, not in showcasing AI. AI work should follow the WIQ-018 policy: "AI work should follow business proof, not replace it."

The single exception is **image quality checking** (a low-complexity, high-value computer vision task). This could be added as a "v1.1" enhancement after the pilot, but is not required for pilot success.

The CHANGELOG documents several AI features (AI Waste Classification v2, push notifications, rewards/incentives) that are not implemented in code. These are aspirational and should not be relied on.

---

## 24. Step 15: UX / branding audit

### Brand identity

| Asset | Status | Details |
|-------|--------|---------|
| **Logo** | MISSING | No logo file or component. Only text "Waste-IQ" in navigation/footer/layout |
| **Favicon** | IMPLEMENTED | `frontend/public/favicon.svg` â€” green rounded-square leaf mark, wired in `index.html` and `SeoHead.tsx` |
| **Brand name** | IMPLEMENTED | "Waste-IQ" appears as text in Navigation, DashboardLayout, Footer |
| **Tagline** | MISSING | None in the UI |
| **Color system** | MISSING | Tailwind colors used inconsistently; no design token system |
| **Typography** | MISSING | No consistent font system; relies on Tailwind defaults |
| **Design tokens** | MISSING | No CSS variables or Tailwind extension for brand colors |

**Verdict: Brand identity is weak.** The product looks like a development scaffold. For a professional pilot, a logo and design system are needed (NEW-10).

### Navigation and layout

| Screen | Layout | Notes |
|--------|--------|-------|
| Public pages | `PublicLayout` | Landing, Features, About, Contact, Login, Register |
| Dashboard pages | `DashboardLayout` | Role-specific layout with sidebar navigation |
| Auth pages | `AuthLayout` | Login, Register, Verify, Reset |

**Layout is functional and consistent.** All dashboards use the same `DashboardLayout` with role-specific navigation.

### Page quality assessment

| Page | Loading | Empty | Error | Responsiveness | Notes |
|------|---------|--------|--------|---------------|-------|
| DashboardOverview | YES (skeleton) | YES (EmptyState) | YES (ErrorState) | YES (md/lg/xl) | Good |
| CitizenPickups | YES (skeleton) | YES (EmptyState) | YES (ErrorState) | YES | Good |
| CollectorOverview | YES (skeleton) | YES (EmptyState) | YES (ErrorState) | YES (sm/md) | Good |
| CollectorMap | Partial | Inline | Inline | YES | Functional |
| NewPickup | YES (step skeleton) | N/A | YES (apiError banner) | YES | Good |
| AdminOverview | YES (skeleton) | YES (EmptyState) | Inline divs | YES | Good |
| DealerOverview | YES (skeleton) | YES (EmptyState) | Inline divs | YES | Good |
| DealerProfile | YES (skeleton) | YES (inline form) | Inline divs | YES | Good |

### Critical UX problems

| Problem | Severity | Location | Recommendation |
|---------|----------|----------|----------------|
| **No logo** | HIGH | Navigation, layouts | NEW-10: Create logo file |
| **Inconsistent button styles** | MEDIUM | Multiple pages | NEW-10: Define design system |
| **Multi-step wizard for pickup** | MEDIUM | NewPickupPage | Consider single-page for simple case |
| **No "citizen track my collector"** | MEDIUM | Citizen dashboard | Add collector live location sharing |
| **No empty state illustration** | LOW | Multiple pages | Add SVG illustrations for empty states |
| **Notifications bell** | LOW | All dashboards | Polling-based; could be WebSocket |

### Branding recommendation

Do NOT invest in branding before the business workflows are solid. For the 30-day pilot: add a logo (NEW-10) but do not overhaul the design system. After the pilot validates the business model, invest in a full design system.

---

## 25. Step 16: Mobile field experience

### Collector on a phone â€” can they complete a pickup?

The collector is the primary mobile user. They will use Waste-IQ on a phone while physically collecting waste. This section evaluates whether the current mobile experience supports this.

### Touch targets

**Evidence:** Tailwind uses `h-10` (40px) minimum for buttons. The collector action buttons in `CollectorPickupActions.tsx` use `DashboardCard` with appropriate spacing. The map uses large tap targets for markers.

**Verdict: ACCEPTABLE** â€” buttons and interactive elements are appropriately sized.

### Map and location interaction

**Evidence:** `CollectorMapPage.tsx` uses a dependency-free SVG map. The "Use my location" button triggers browser geolocation. Navigation panel shows step-by-step directions.

**Verdict: ACCEPTABLE** â€” the SVG map is lightweight (no Google Maps dependency) and functional. No offline map caching.

### Camera upload

**Evidence:** The image upload is on the citizen side (`NewPickupPage`). The collector does not currently upload photos of collected waste.

**Verdict: MISSING** â€” collectors cannot document the collected waste. This is a proof-of-collection gap (NEW-08 partially addresses this via weight disputes).

### Weight entry

**Evidence:** The collector enters weight as a decimal number in a form field (`CollectorCompleteRequest` with `weight_kg: float`). The UI is a standard number input.

**Verdict: ACCEPTABLE** â€” but no integration with a physical scale.

### Status updates

**Evidence:** Each status transition (accept, start, collect, record weight) requires navigating to the pickup detail and clicking a button. There is no quick-action toolbar.

**Verdict: NEEDS IMPROVEMENT** â€” a floating action button or bottom sheet with quick actions (accept, start, record weight) would reduce friction significantly.

### Loading states

**Evidence:** Every data-fetching page uses `LoadingSkeleton`. The map page uses a detail-variant skeleton.

**Verdict: GOOD** â€” skeleton loaders prevent layout shift.

### Network failure

**Evidence:** No offline mode. API errors surface as banners (`apiError`). The `QueryErrorToastProvider` provides user feedback.

**Verdict: NEEDS IMPROVEMENT** â€” collectors in low-connectivity areas (basements, rural areas) will experience failures. Consider optimistic UI updates and retry logic.

### Readability and speed

**Evidence:** Tailwind responsive utilities (`text-sm md:text-base`) used throughout. No heavy images on collector pages. The map is SVG (lightweight).

**Verdict: GOOD** â€” the collector pages are lightweight and fast.

### Mobile field verdict

The current collector mobile experience is **functional but friction-heavy**. The primary gaps are:

1. No collector photo upload (proof of collection)
2. No quick-action floating toolbar
3. No offline mode
4. No scale integration

For the 30-day pilot, the current experience is sufficient if collectors are given a brief orientation. Post-pilot, invest in a collector mobile app or PWA with offline support.

---

## 26. Step 17: Failure / edge case audit

| Failure scenario | Business risk | Current handling | Gap |
|-----------------|-------------|----------------|-----|
| **Citizen cancels** | LOW â€” expected behaviour | Status â†’ `cancelled`; image deleted; notification to assigned collector | OK |
| **Collector cancels** | MEDIUM â€” pickup reverts to available | Status â†’ `pending`; collector unassigned; notification to citizen | OK |
| **Collector doesn't arrive** | MEDIUM â€” pickup never completed | No automatic detection; aging pickup alert goes to admin after 2 days | NEW-09 (collector reminder) |
| **Citizen unavailable at pickup** | MEDIUM â€” collector waits | No workflow; pickup stuck in `on_the_way` | No current handling |
| **Duplicate pickup (citizen double-submits)** | LOW â€” rare | No dedup; creates two requests | Could add dedup on same day/location |
| **Simultaneous collector acceptance** | LOW â€” row lock prevents this | `accept_pickup_request` uses DB constraints | OK |
| **Wrong waste type** | MEDIUM â€” wrong inventory categorisation | AI returns Unknown; admin can correct during lot creation | OK (admin can correct) |
| **Wrong weight (typo)** | MEDIUM â€” dispute or inventory error | Citizen can dispute; admin can correct | OK (but no photo evidence â€” NEW-08) |
| **Weight dispute** | MEDIUM â€” operational overhead | Full dispute workflow exists | OK |
| **Duplicate inventory lot** | LOW â€” unique constraint prevents | `pickup_request_id` is unique on `inventory_lots` | OK |
| **Simultaneous reservation** | LOW â€” row lock prevents this | `reserve_inventory_lot` uses `SELECT ... FOR UPDATE` | OK |
| **Expired reservation** | LOW â€” expected behaviour | Auto-released by background job; dealer notified | OK |
| **Failed image upload** | LOW â€” image is optional | Graceful degradation; image_url stored as NULL | OK |
| **Email delivery failure** | LOW â€” console backend in dev | BackgroundTask with logging; user notified only if resend | OK (dev); SMTP config needed for prod (NEW-07) |
| **Database failure** | HIGH â€” system down | Health check endpoint; Sentry monitoring | OK |
| **Server restart** | MEDIUM â€” in-flight requests fail | No graceful shutdown handling observed | No specific implementation |
| **Unauthorized access attempt** | MEDIUM â€” security | 401/403 responses; audit log entry | OK |

### Business risk ranking

| Rank | Failure scenario | Business risk | Mitigation priority |
|------|----------------|-------------|-------------------|
| 1 | Collector doesn't arrive | HIGH | NEW-09 (aging reminder to collector) |
| 2 | Citizen unavailable at pickup | HIGH | No current solution |
| 3 | Database failure | HIGH | OK (health check, monitoring) |
| 4 | Weight dispute fraud | MEDIUM | NEW-08 (scale photo) |
| 5 | Simultaneous reservation | LOW | OK (row lock) |
| 6 | Image upload failure | LOW | OK (graceful) |

---

## 27. Step 18: Production readiness

Cross-referencing WIQ-V1-050 (issue #96):

| Requirement | Status | Evidence |
|-----------|--------|----------|
| **Environment configuration** | âœ… PASS | `config.py` with pydantic-settings; `.env.example` documented |
| **Secrets management** | âš ï¸ PARTIAL | `.env.example` documented; `JWT_SECRET_KEY=change-me` in dev; production must override |
| **Database** | âœ… PASS | PostgreSQL 16 in prod; SQLite in dev; migrations verified |
| **Migrations** | âœ… PASS | 20+ clean migrations; head confirmed |
| **Backup** | âŒ NOT VERIFIED | No backup strategy documented or implemented |
| **Logging** | âœ… PASS | Structured logging in `app/core/logging.py` |
| **Monitoring** | âœ… PASS | Sentry in `app/core/sentry_sdk.py` |
| **Health checks** | âœ… PASS | `/health` (liveness) and `/health/ready` (readiness) |
| **CORS** | âœ… PASS | Configured in `main.py`; fixed in v0.2.0 |
| **SMTP** | âŒ MISSING | `SMTP_*` config exists but not validated in production | NEW-07 |
| **Storage** | âœ… PASS | Cloudinary with graceful fallback |
| **Deployment** | âœ… PASS | Render.com; Docker Compose |
| **Security** | âœ… PASS | Rate limiting, lockout, JWT, audit logging |
| **Rate limiting** | âœ… PASS | In-memory sliding window; per-IP and per-account |
| **Concurrency** | âœ… PASS | Row locks on reserve/purchase |
| **Error handling** | âœ… PASS | Custom exceptions; global error handler |

### Production readiness gaps

| Gap | Severity | Recommendation |
|-----|----------|----------------|
| **Backup strategy** | HIGH | Document and implement PostgreSQL backup (pg_dump + S3). No evidence in codebase. |
| **SMTP production config** | HIGH | NEW-07: Configure real SMTP for production. |
| **JWT secret validation** | MEDIUM | Warn on startup if `JWT_SECRET_KEY` is the default value. |
| **APM / OpenTelemetry** | LOW | Not required for MVP but would improve observability. |

---

## 28. Step 19: Pilot readiness

Cross-referencing WIQ-V1-051 (issue #97). The 30-day pilot definition is in Section 11.

### What the product can do on Day 1

All items in Section 11 "What Waste-IQ Must Do on Day 1" are **implemented or can be configured**:

| Requirement | Status | Action needed |
|------------|--------|-------------|
| All 4 roles can register and log in | âœ… IMPLEMENTED | Deploy |
| Citizens submit pickup with photo and GPS | âœ… IMPLEMENTED | Deploy |
| Collectors see available pickups on map | âœ… IMPLEMENTED | Deploy |
| Collectors can accept and complete pickups | âœ… IMPLEMENTED | Deploy |
| Collectors record weight | âœ… IMPLEMENTED | Deploy |
| Citizens verify or dispute weight | âœ… IMPLEMENTED | Deploy |
| Admins resolve disputes | âœ… IMPLEMENTED | Deploy |
| Admins create inventory lots | âœ… IMPLEMENTED | NEW-01 (auto-lot creation) â€” MANUAL for now |
| Dealers browse, reserve, purchase | âœ… IMPLEMENTED | Deploy |
| Admins view operational dashboard | âœ… IMPLEMENTED | Deploy |
| Admins export data as CSV | âŒ MISSING | NEW-03 â€” blocking for pilot reporting |
| Real email delivery | âŒ MISSING | NEW-07 â€” blocking for real users |
| In-app notifications | âœ… IMPLEMENTED | Deploy |

### P0 blockers for the 30-day pilot

1. **NEW-03** (CSV export) â€” without this, pilot reporting requires database access.
2. **NEW-07** (SMTP) â€” without this, real users cannot verify email or reset passwords.

### P1 requirements for a smooth pilot

1. **NEW-01** (auto-lot creation) â€” otherwise admin manually creates every lot.
2. **NEW-04** (collector earnings) â€” without this, collectors have no financial incentive.
3. **NEW-02** (commission calculation) â€” without this, no GMV or revenue reporting.

### Pilot recommendation

The product is **pilot-ready with 3 weeks of engineering** after the gaps above are addressed. The core workflows are complete and tested. The remaining work is operational tooling (export, commission, earnings).

---

## 29. Step 20: Existing issue audit

See Section 7 for the full mapping of existing issues to current implementation status. This section focuses on cross-referencing the specific issues referenced in the task.

| Issue | Status | Coverage |
|-------|--------|----------|
| #96 | See Step 18 | Production readiness audit above |
| #97 | See Step 19 | Pilot readiness audit above |
| #99 | NOT FOUND | No evidence in codebase |
| #111 | See Section 20 | Auto-lot creation not implemented |
| #112 | NOT FOUND | No evidence in codebase |

The existing WIQ-V1 series documents (V1_LAUNCH_READINESS_AUDIT, WIQ_V1_046_WEIGHT_VERIFICATION, etc.) are implementation records for work that has been completed. The current state reflects those implementations.

---

## 30. Step 21: Product differentiation scoring

See Section 5 for the full scoring table. Summary:

| Differentiator | Customer Value | Business Value | Tech Feasibility | Defensibility | Score |
|----------------|--------------|----------------|-------------------|--------------|-------|
| Verified waste weight | 5 | 5 | 4 | 5 | 19 |
| Waste traceability | 5 | 5 | 4 | 5 | 19 |
| Collector operations | 5 | 4 | 4 | 3 | 16 |
| Recycler marketplace | 4 | 5 | 4 | 3 | 16 |
| Material inventory | 4 | 4 | 5 | 2 | 15 |

**Top 3 differentiators:**
1. Verified waste weight â€” trust mechanism no competitor offers
2. Full waste traceability â€” ESG/municipality appeal
3. Recycler marketplace â€” revenue engine

---

## 31. Step 22: Prioritized backlog

See Section 8 for the full backlog with NEW-01 through NEW-15.

### P0 â€” Blocks the pilot
- NEW-01: Auto-create inventory lot from completed pickup
- NEW-02: Revenue reporting (commission + GMV)
- NEW-03: CSV export
- NEW-04: Collector earnings and payout dashboard

### P1 â€” Important for pilot success
- NEW-05: Citizen estimated pickup value
- NEW-06: Phone-redacted admin users API
- NEW-07: Production SMTP configuration
- NEW-08: Weight dispute evidence upload
- NEW-09: Collector aging pickup reminders

### P2 â€” Can wait for post-pilot
- NEW-10: Brand identity (logo + design tokens)
- NEW-11: Address coarsening for unassigned pickups
- NEW-12: Dealer self-source inventory
- NEW-13: Pickup rescheduling
- NEW-14: Pilot health dashboard

### P3 â€” Future
- NEW-15: Municipality role (WIQ-015)

---

## 32. Step 23: Epics

Grouping the backlog into implementable epics:

### EPIC 1 â€” Brand & Design System (NEW-10)
- Create Waste-IQ logo file and favicon
- Define Tailwind color tokens
- Apply consistent typography
- Update navigation, layouts, public pages

### EPIC 2 â€” Citizen Experience (NEW-05, NEW-08, NEW-13)
- Estimated pickup value at submission
- Weight dispute evidence upload
- Pickup rescheduling

### EPIC 3 â€” Collector Operations (NEW-04, NEW-09, NEW-11)
- Earnings and payout dashboard
- Aging pickup reminders
- Address coarsening for unassigned pickups

### EPIC 4 â€” Dealer / Recycler Experience (NEW-12)
- Self-source inventory workflow

### EPIC 5 â€” Inventory & Traceability (NEW-01)
- Auto-create inventory lot from completed pickup
- Optional: draft lot state

### EPIC 6 â€” Trust, Privacy & Security (NEW-06)
- Phone-redacted admin users API
- Security headers (CSP, HSTS)

### EPIC 7 â€” Notifications & Communication
- Production SMTP (NEW-07) â€” separate from this epic but related

### EPIC 8 â€” Admin Operations (NEW-02, NEW-03, NEW-14)
- Revenue reporting (commission + GMV)
- CSV export
- Pilot health dashboard

### EPIC 9 â€” Analytics
- Existing analytics are strong; expand with commercial KPIs post-pilot

### EPIC 10 â€” AI & Intelligence
- No AI work recommended for pilot (see Section 23)
- Image quality checking for post-pilot

### EPIC 11 â€” Reliability & Production
- Backup strategy documentation
- JWT secret validation on startup
- APM / OpenTelemetry

### EPIC 12 â€” Pilot Readiness
- All P0 items above
- Production SMTP deployment
- Operational runbook

---

## 33. Step 24: Top 10 next issues

The following 10 issues are the highest-value improvements toward a real Waste-IQ pilot. They are ordered by implementation sequence, not purely by priority.

---

### Issue 1

**Issue title:** Auto-create inventory lot from completed pickup

**Type:** Feature

**Priority:** P0 â€” BLOCKS PILOT

**Affected role:** Admin

**Problem:** Completed pickups do not become inventory lots automatically. Admins must manually create every lot, creating an unsustainable bottleneck at pilot scale.

**Expected outcome:** When a pickup reaches `completed` status with a positive weight, the system creates a draft inventory lot or surfaces a "Create Lot" button on the pickup detail page. This eliminates manual work and ensures no completed pickup is missed.

**Dependencies:** None

**Existing issue:** WIQ-V1-053 / issue #111 (partially)

**Why now:** Without this, the 30-day pilot cannot scale beyond ~10 pickups/week without a dedicated admin.

---

### Issue 2

**Issue title:** Revenue reporting: commission calculation and GMV analytics

**Type:** Feature

**Priority:** P0 â€” BLOCKS PILOT

**Affected role:** Admin

**Problem:** `MarketplaceTransaction` records gross value but commission is never calculated or displayed. The admin analytics show `total_revenue = 0`. The pilot cannot demonstrate commercial viability.

**Expected outcome:** When a dealer purchases a lot, the system calculates commission (flat % from config or pricing rules) and records it on the transaction. Admin analytics surfaces gross marketplace value and platform commission revenue.

**Dependencies:** NONE-01 (lot creation)

**Existing issue:** WIQ-008, WIQ-009

**Why now:** This is the pilot's answer to "what did Waste-IQ earn?" Without it, founders cannot measure success.

---

### Issue 3

**Issue title:** CSV export for transactions and pickups

**Type:** Feature

**Priority:** P0 â€” BLOCKS PILOT

**Affected role:** Admin

**Problem:** Admins cannot export transaction data, pickup data, or analytics for reconciliation, investor reporting, or municipality handoff. Every report requires manual database queries.

**Expected outcome:** A one-click export button on the admin analytics page that downloads a CSV of `MarketplaceTransaction` records (with date range filter) and/or `pickup_requests` with all relevant fields.

**Dependencies:** NONE-02 (commission calculation, for transaction export)

**Existing issue:** WIQ-010

**Why now:** Pilot reporting cannot be done without this.

---

### Issue 4

**Issue title:** Collector earnings and payout dashboard

**Type:** Feature

**Priority:** P0 â€” BLOCKS PILOT

**Affected role:** Collector

**Problem:** Collectors see completion counts and weight totals but no monetary value. Without knowing their earnings, collectors have no financial incentive to participate in the pilot.

**Expected outcome:** A collector dashboard showing: per-kg rate by material (from admin pricing rules), total earnings to date, pending payouts, and a payout history table. Displays â‚¹/kg rates and total earnings in the local currency.

**Dependencies:** NONE-02 (pricing rules must exist and be linked to materials)

**Existing issue:** None (NEW-04)

**Why now:** Without a financial incentive, collectors will not engage with the pilot.

---

### Issue 5

**Issue title:** Production SMTP configuration and email delivery verification

**Type:** Infrastructure

**Priority:** P0 â€” BLOCKS PILOT

**Affected role:** All roles

**Problem:** Email verification and password reset are functional in development (console backend logs to console) but `SMTP_HOST` is empty in production config. Real users cannot verify email or reset passwords.

**Expected outcome:** Configure a real SMTP provider (SendGrid, AWS SES, or Resend). Verify that email verification links and password reset emails reach real inboxes. Document the SMTP configuration in the deployment guide.

**Dependencies:** None

**Existing issue:** None (NEW-07)

**Why now:** Non-negotiable for real users. Real users need email verification and password reset.

---

### Issue 6

**Issue title:** Weight dispute evidence upload

**Type:** Feature

**Priority:** P1 â€” IMPORTANT FOR PILOT

**Affected role:** Citizen, Admin

**Problem:** Citizens can file a weight dispute with a text reason but cannot upload a scale photo. This reduces the quality of dispute evidence and makes admin resolution harder.

**Expected outcome:** When a citizen files a weight dispute, they can attach a photo of the scale reading. The photo is uploaded to Cloudinary (or local storage) and linked to the `PickupDispute` record. Admins see the photo on the dispute resolution page.

**Dependencies:** NONE-08 (image upload service already exists)

**Existing issue:** None (NEW-08)

**Why now:** Improves dispute resolution quality from day one of the pilot.

---

### Issue 7

**Issue title:** Collector aging pickup reminders

**Type:** Feature

**Priority:** P1 â€” IMPORTANT FOR PILOT

**Affected role:** Collector, Admin

**Problem:** When a collector accepts a pickup but does not progress through the lifecycle, only admins receive an aging alert. The collector receives no reminder. This leads to "collector ghosting" where accepted pickups never complete.

**Expected outcome:** When a collector has an accepted pickup older than a configurable threshold (e.g., 24 hours), the system sends an in-app notification to the collector reminding them to progress the pickup. Admins continue to receive their existing alert.

**Dependencies:** NONE-09 (background jobs already exist and work)

**Existing issue:** None (NEW-09)

**Why now:** Reduces the "collector ghosting" failure mode in the pilot.

---

### Issue 8

**Issue title:** Citizen estimated value at pickup submission

**Type:** Feature

**Priority:** P1 â€” IMPORTANT FOR PILOT

**Affected role:** Citizen

**Problem:** Citizens submit pickup requests without knowing the material's estimated value. This reduces submission motivation and prevents pricing transparency from being a pilot talking point.

**Expected outcome:** When a citizen submits a pickup request (or on the confirmation screen), display an estimated material value based on `estimated_weight_kg Ã— active pricing_rule`. Clearly label as "estimated value â€” actual value based on confirmed weight." If no pricing rule exists for the waste type, show no estimate.

**Dependencies:** NONE-02 (pricing rules must be configured)

**Existing issue:** WIQ-005

**Why now:** Sets pricing expectations early and demonstrates the business model to citizens.

---

### Issue 9

**Issue title:** Pilot health dashboard â€” single-view operational pulse

**Type:** Feature

**Priority:** P1 â€” IMPORTANT FOR PILOT

**Affected role:** Admin

**Problem:** The admin overview page has many sections but no single view that shows the pilot's health at a glance. Admins must navigate between sections to assess the current state.

**Expected outcome:** A "Pilot Pulse" card or section on the admin dashboard showing: active pickups today, pickups this week, completion rate, open disputes, pending dealer approvals, aging pickups (accepted >24h). All on one screen.

**Dependencies:** NONE-01 (lot creation), NONE-09 (aging alerts)

**Existing issue:** None (NEW-14)

**Why now:** The admin needs a single view to manage the pilot without switching contexts.

---

### Issue 10

**Issue title:** Admin user API: phone-redacted listing

**Type:** Security / Privacy

**Priority:** P1 â€” IMPORTANT FOR PILOT

**Affected role:** Admin, All users

**Problem:** `/admin/users` returns the full `UserRead` schema including `phone` for every user in the system. Any admin account compromise exposes the entire user base's phone numbers.

**Expected outcome:** Split `/admin/users` into two endpoints: (1) a listing endpoint that returns user records without `phone` (for the admin users table), and (2) a detail endpoint `/admin/users/{id}` that returns the full record including phone (for the admin user detail page). The listing endpoint is what the frontend admin users table calls.

**Dependencies:** None

**Existing issue:** None (NEW-06)

**Why now:** Reduces the PII blast radius of an admin account compromise. Important trust signal for the pilot.

---

## End of audit

This document was produced through evidence-based inspection of the Waste-IQ repository at commit `HEAD`. No code was modified, no issues were created, and no commits were made. All findings reflect the current working tree state.

The central question â€” **how do we turn the current Waste-IQ software into a trustworthy, usable, economically testable waste-management platform that can run its first real-world pilot?** â€” is answered by:

1. Closing the 4 P0 gaps (NEW-01 through NEW-04).
2. Configuring real SMTP for production (NEW-07).
3. Running the 30-day pilot with real users.
4. Measuring against the success metrics in Section 12.
