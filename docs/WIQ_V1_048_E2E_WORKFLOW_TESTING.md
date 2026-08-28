# WIQ-V1-048 — Critical End-to-End Workflow Testing

WIQ-V1-048 adds **cross-feature integration coverage** for the complete
Waste-IQ citizen → collector → weight verification → dispute → completion
lifecycle. It builds on top of the four hardened feature areas that have
already been merged into `develop`:

- **WIQ-V1-044** — Security & Authorization (`#101`)
- **WIQ-V1-045** — Collection Workflow Hardening (`#104`)
- **WIQ-V1-046** — Weight Verification & Dispute (`#106`)
- **WIQ-V1-047** — Masked Citizen–Collector Communication (`#102`)

The purpose of WIQ-V1-048 is to prove that the integrated system works
end-to-end across feature boundaries, and that the boundaries hold when
exercised through real HTTP requests rather than at the service layer in
isolation.

## 1. Scope and Intent

The prior per-feature unit tests already exhaustively cover each domain
in isolation (e.g. `test_collection_workflow.py`,
`test_weight_verification.py`, `test_masked_communication.py`,
`test_security_boundaries.py`). This issue does **not** duplicate those
tests. Instead it adds:

1. **Happy-path workflow**: a single end-to-end test that exercises
   registration → login → pickup creation → assignment → collection →
   masked contact → weight recording → citizen confirmation → completion,
   with audit and notification verification at every step.
2. **Dispute workflow**: end-to-end coverage of the weight dispute
   resolution path with both `upheld` and `corrected` admin outcomes.
3. **Authorization workflows**: cross-user boundary checks at the
   workflow level (citizen ↔ citizen, collector ↔ collector, role
   isolation, IDOR/BOLA).
4. **Invalid state workflows**: explicit denials of the disallowed
   transitions called out in the issue.
5. **Authentication / session failure**: missing / invalid / malformed
   JWTs, unverified users, tokens for deleted users.
6. **Notification & audit integrity**: idempotent operations do not
   duplicate audit events or notifications; failed transitions do not
   create false successful events; audit payloads contain no phone
   numbers, tokens, or sensitive PII.
7. **Masked communication lifecycle scoping**: contact is enabled only
   in `accepted` / `on_the_way` / `collected` / `weight_recorded` and
   disabled in `pending`, `completed`, `cancelled`, and `disputed`.
8. **Replay / idempotency**: re-running the same transition does not
   produce duplicate state events.
9. **Summary statistics correctness**: citizen and collector dashboards
   reflect each transition.

All tests are deterministic and use the existing pytest + `TestClient`
infrastructure. There is no reliance on Twilio, Railway, Vercel, real
email delivery, real SMS/voice, or any external service. The
`MockMaskedCommunicationProvider` is the active provider in the test
environment.

## 2. Test File Layout

A single dedicated test module, `backend/tests/test_e2e_workflows.py`,
contains the new coverage. It is organised into twelve test classes for
readability:

| Class | What it proves |
| ----- | -------------- |
| `TestCriticalHappyPath` | Full register → login → create → assign → start → collect → mask → record → confirm → complete. |
| `TestWeightDisputeWorkflow` | Full dispute → admin resolve (upheld & corrected) flows. |
| `TestAuthorizationWorkflows` | Cross-user and role-isolation boundaries. |
| `TestInvalidStateTransitions` | Parametrised denial of disallowed transitions. |
| `TestAuthenticationSessionFailure` | Missing / invalid / malformed JWT, unverified user. |
| `TestNotificationAuditIntegrity` | Idempotency, failed transitions, no PII in audit. |
| `TestReplayIdempotency` | Replay safety of confirm, dispute, weight, cancel. |
| `TestCitizenCancellation` | Citizen cancel at pending; cannot cancel accepted. |
| `TestLegacyEndpointCompatibility` | Legacy collector endpoints are wired. |
| `TestCrossCollectorDisputeScenario` | Notifications go to the right parties during dispute. |
| `TestMaskedCommunicationLifecycleScoping` | Contact enabled/disabled per pickup state. |
| `TestSummaryStatisticsWorkflow` | Summary endpoints track each transition. |

The total number of new tests added by WIQ-V1-048 is **55** (the
project-wide test count grows from 694 to 749).

## 3. State Transitions Exercised

The test matrix covers every legal transition in the canonical
lifecycle plus every illegal transition called out in the issue:

| Source state | Target state | Coverage | Verdict |
| ------------ | ------------ | -------- | ------- |
| (none)       | `pending`    | happy path | 201 |
| `pending`    | `accepted`   | happy path | 200 |
| `pending`    | `cancelled`  | `TestCitizenCancellation` | 200 |
| `pending`    | `start`      | `TestInvalidStateTransitions` | 403 |
| `pending`    | `collect`    | `TestInvalidStateTransitions` | 400 / 403 |
| `pending`    | `record-weight` | `TestInvalidStateTransitions` | 400 / 403 |
| `pending`    | `complete`   | `TestInvalidStateTransitions` | 400 / 403 |
| `pending`    | `dispute`    | `TestNotificationAuditIntegrity.test_failed_dispute_does_not_emit_audit` | 400 |
| `accepted`   | `on_the_way` | happy path | 200 |
| `accepted`   | `pending`    | `TestReplayIdempotency.test_collector_cancel_releases_assignment` | 200 |
| `accepted`   | `collect` (without start) | `TestInvalidStateTransitions.test_cannot_collect_from_accepted_without_starting` | 400 |
| `on_the_way` | `record-weight` (without collect) | `TestInvalidStateTransitions.test_cannot_record_weight_from_on_the_way_without_collecting` | 400 |
| `collected`  | `weight_recorded` | happy path | 200 |
| `weight_recorded` | `completed` (citizen) | happy path | 200 |
| `weight_recorded` | `disputed` | `TestWeightDisputeWorkflow` | 200 |
| `weight_recorded` | `completed` (collector bypass) | `TestCollectionWorkflow` + `TestInvalidStateTransitions.test_cannot_complete_from_weight_recorded_without_citizen_verification` | 400 |
| `disputed`   | `completed` (admin upheld) | `TestWeightDisputeWorkflow.test_dispute_uphold_workflow` | 200 |
| `disputed`   | `completed` (admin corrected) | `TestWeightDisputeWorkflow.test_dispute_corrected_workflow` | 200 |
| `disputed`   | `completed` (collector bypass) | `TestCollectionWorkflow` + `TestInvalidStateTransitions.test_cannot_complete_a_disputed_pickup_normally` | 400 |
| `completed`  | `dispute`    | `TestInvalidStateTransitions.test_cannot_dispute_a_completed_pickup` | 400 |
| `completed`  | re-accept   | covered in `test_collection_workflow.py` | 400 |
| `completed`  | re-`record-weight` | `TestInvalidStateTransitions.test_cannot_record_a_second_weight_after_completion` | 400 |
| `cancelled`  | any collector mutation | `TestInvalidStateTransitions.test_cannot_mutate_a_cancelled_pickup` | 400 / 403 / 404 |

## 4. Authorization Scenarios

WIQ-V1-048 proves the following authorization boundaries at the
workflow level:

1. **Citizen A cannot access Citizen B's pickup** — listing, detail,
   PATCH, cancel all return `403`.
2. **Collector A cannot mutate Collector B's assigned pickup** — accept,
   start, collect, record-weight, complete, cancel all return `403`.
3. **Unassigned collector cannot initiate masked contact** — `403`.
4. **Other citizen cannot initiate masked contact** — `403`.
5. **Collector never sees plaintext citizen phone** — even on their
   assigned pickup; contact must use the masked channel from
   WIQ-V1-047.
6. **Citizen cannot perform admin dispute resolution** — `403`.
7. **Collector cannot perform admin dispute resolution** — `403`.
8. **Unverified users cannot perform protected mutations** — collect,
   accept, weight-confirm all return `403` with `Email verification
   required`.
9. **Unauthenticated requests fail with `401`** on every protected
   endpoint.
10. **Token for a non-existent user returns `401`**.
11. **Malformed `Authorization` header returns `401` / `403`**.

## 5. Masked Communication Lifecycle Scoping

WIQ-V1-047's contact boundary is verified at every state:

| Pickup state | `POST /pickup-requests/{id}/contact` | Rationale |
| ------------ | ------------------------------------- | --------- |
| `pending` | 400 — "no collector assigned yet" | No recipient to mask |
| `accepted` | 200 — masked session created | Active state |
| `on_the_way` | 200 — masked session created | Active state |
| `collected` | 200 — masked session created | Active state |
| `weight_recorded` | 200 — masked session created | Active state |
| `disputed` | 400 — not eligible | Awaiting admin review |
| `completed` | 400 — contact closed | Work concluded |
| `cancelled` | 400 — not eligible | Work abandoned |

Across all of these, the contact response never includes the real
citizen or collector phone number.

## 6. Audit and Notification Integrity

The end-to-end tests confirm that the audit log and notification
infrastructure behave as required:

- **Successful transitions generate the expected audit events** —
  `pickup_created`, `pickup_accepted`, `pickup_started`,
  `pickup_collected`, `pickup_weight_recorded`,
  `pickup_weight_confirmed`, `pickup_weight_disputed`,
  `pickup_dispute_resolved`, `communication_requested`, and
  `pickup_dispute_reviewed` are all emitted on the right pickup at the
  right moment.
- **Replay / idempotent operations do not duplicate audit events** —
  double-accept produces exactly one `pickup_accepted` row.
- **Notifications correspond to successful state transitions only** —
  double-accept produces exactly one `pickup_accepted` notification;
  failed transitions (e.g. an invalid start) do not produce
  `pickup_started` notifications.
- **Failed operations do not create false successful transition
  events** — a rejected collector-complete attempt does not create a
  `pickup_completed` audit row, and a premature dispute attempt does
  not create a `pickup_weight_disputed` row.
- **Audit payloads contain no PII** — keys `phone`, `citizen_phone`,
  `password`, `secret` never appear in audit before/after snapshots.
  The default test citizen phone number (`9000000001`) is never
  present in audit payloads.
- **Communication audit is PII-free** — the
  `communication_requested` audit event only includes `session_id`,
  `requester_role`, and `status`; never any phone, token, or API
  key.

## 7. Test Strategy

WIQ-V1-048 follows the existing test conventions:

- **Framework**: `pytest` + `fastapi.testclient.TestClient`.
- **Database**: in-memory SQLite with `StaticPool`, autouse fixtures
  for rate-limiter reset and email outbox clear.
- **Authentication**: existing `citizen_headers`, `collector_headers`,
  `admin_headers`, `make_user`, and `auth_headers` fixtures from
  `backend/tests/conftest.py`.
- **No external services**: `MockMaskedCommunicationProvider` is the
  active provider. No real Twilio, SMTP, or HTTP calls.
- **Deterministic**: every assertion is checked synchronously after a
  finite sequence of `TestClient` calls. There are no `sleep` calls,
  no polling loops, and no reliance on background tasks completing
  before the test ends (background email delivery is pointed at the
  test DB so it can be observed through `db_session`).
- **Isolated**: every test gets a fresh database, fresh email outbox,
  and reset rate limiter.
- **Regression-safe**: the tests do not weaken any production
  authorization rule or application behaviour to make assertions
  pass. All assertions are on observable API responses and the
  `audit_logs` / `notifications` API surfaces.

## 8. CI Execution

The new tests run as part of the standard backend test suite:

```bash
cd backend
python -m pytest -q
```

The new module adds **55 tests**, growing the backend suite from
**694 to 749** tests. The full suite runs in approximately 9–10 minutes
in CI.

Linting, formatting, and type checks:

```bash
ruff check .
black --check .
mypy app
```

All three pass on the new file. (`ruff` and `black` flag a few
pre-existing formatting issues in the alembic migration files that are
unrelated to WIQ-V1-048; these are tracked in the existing backlog and
are not part of this change.)

## 9. Frontend Coverage

The existing `frontend/src/test/collector-lifecycle.test.tsx` already
exercises the canonical collector lifecycle end-to-end through the
MSW-backed `handlers.ts` (accept → start → collect → record weight →
awaiting citizen confirmation). The release handover also includes
`accessibility.test.tsx`, `dashboards.test.tsx`, and the per-page
component tests.

WIQ-V1-048 deliberately does **not** introduce a Playwright or browser
E2E stack — the repository does not currently carry the infrastructure
to support it cleanly, and the cost/benefit ratio does not justify
adding it for this issue. The Vitest + MSW layer already gives
deterministic, fast, CI-safe coverage of the lifecycle from the
user's perspective. The frontend test count remains at **204** tests.

## 10. Known Limitations

- The end-to-end happy-path test currently issues a manual
  `email_verified_at` update directly against `db_session` for the
  freshly registered citizen. This mirrors the public registration
  flow (the API does not auto-verify), and avoids depending on
  real email delivery in CI.
- The full backend test suite is intentionally slow (~10 min) because
  it runs 749 isolated tests serially. This is the existing CI
  baseline; WIQ-V1-048 follows the same pattern.
- The WIQ-V1-048 tests do not exercise the rate limiter or login
  history features; those are already covered by
  `test_rate_limiting.py` and `test_login_history.py`.

## 11. Files Changed

- `backend/tests/test_e2e_workflows.py` — **new** (55 tests).
- `docs/WIQ_V1_048_E2E_WORKFLOW_TESTING.md` — **new** (this document).

No production code, no migrations, no frontend code was modified.
