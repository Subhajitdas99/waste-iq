# WIQ-V1-045 — Citizen-Collector Collection Workflow Hardening

WIQ-V1-045 hardens the entire pickup lifecycle so the citizen → collector →
collection → weight → completion flow is reliable, idempotent, and
production-ready. The canonical lifecycle is now:

```
pending
   ↓
accepted
   ↓
on_the_way
   ↓
collected
   ↓
weight_recorded       ← new integration boundary for WIQ-V1-046
   ↓
completed

(cancelled is reachable only from `pending` or `accepted`)
```

## State Machine

| State            | Source states                              | Actor        | Notes                                                                                         |
| ---------------- | ------------------------------------------ | ------------ | --------------------------------------------------------------------------------------------- |
| `pending`        | initial                                    | citizen      | Created on `POST /pickup-requests`.                                                           |
| `accepted`       | `pending`                                  | collector    | `POST /collector/pickups/{id}/accept`. Single assignment enforced by DB unique constraint.    |
| `on_the_way`     | `accepted`                                 | collector    | `POST /collector/pickups/{id}/start`.                                                         |
| `collected`      | `on_the_way`                               | collector    | `POST /collector/pickups/{id}/collect`.                                                       |
| `weight_recorded`| `collected`                                | collector    | `POST /collector/pickups/{id}/record-weight` (WIQ-V1-045 new endpoint).                       |
| `completed`      | `weight_recorded` or `collected` (legacy)  | collector    | `POST /collector/pickups/{id}/complete`. Finalized state.                                     |
| `cancelled`      | `pending`                                  | citizen      | `POST /pickup-requests/{id}/cancel`.                                                          |

### Explicit denials

The service layer rejects any transition whose source state is not listed
above with `HTTP 400 Bad Request` and a deterministic error message. Examples:

- `pending → completed` → DENY (`HTTP 400`)
- `pending → collected` → DENY (`HTTP 400`)
- `completed → accepted` → DENY (`HTTP 400`)
- `completed → on_the_way` → DENY (`HTTP 400`)
- `cancelled → accepted` → DENY (`HTTP 400`)
- `cancelled → collected` → DENY (`HTTP 400`)

## Authorization

The hardened workflow preserves all WIQ-V1-044 security boundaries:

- **Authentication**: every mutation requires a valid bearer token.
- **Email verification**: collector mutations require `require_verified_roles`.
- **Role enforcement**: only collectors can drive collector transitions; only the
  requesting citizen can cancel their own pickup.
- **Assignment enforcement**: a collector can only transition pickups whose
  `assignment.collector_id == current_user.id`. Attempts by an unassigned
  collector return `HTTP 403`.
- **IDOR / BOLA**: collector A cannot mutate collector B's pickup. The
  `_ensure_assigned_collector` helper centralises this check.
- **Admin**: admins can view audit logs and the pickup, but do not bypass
  lifecycle ownership boundaries.
- **PII redaction**: WIQ-V1-047 masking remains intact. `citizen_phone` is
  never returned to assigned or unassigned collectors; contact remains
  restricted to the masked communication channel.

## Idempotency

Each lifecycle mutation is hardened against repeated requests:

| Operation              | Repeated call by same actor                        | Repeated call by another actor |
| ---------------------- | -------------------------------------------------- | ------------------------------ |
| `accept`               | 200, no new assignment/event/notification          | 400, "no longer available"     |
| `start` (on_the_way)   | 200, no transition / no event                      | 403, not assigned              |
| `collect`              | 200, no transition / no event                      | 403, not assigned              |
| `record-weight` (same) | 200, no new event                                  | 403, not assigned              |
| `record-weight` (diff) | 409 Conflict — prevents silent weight overwrite    | 403, not assigned              |
| `complete`             | 200, no transition / no event                      | 403, not assigned              |
| `cancel` (citizen)     | 400, "Only pending requests can be cancelled"      | 403, not your pickup           |
| `cancel-assignment`    | 400, "Only accepted requests can be cancelled"     | 403, not assigned              |

Race conditions on accept are protected by the `collector_assignments.request_id`
`UNIQUE` constraint and the in-transaction re-check of the source state.

## Failure / Retry Behavior

- All mutations commit through a single database transaction with the audit
  event and notification row. If any step fails, the whole transition is
  rolled back.
- External notification provider failures do not corrupt the lifecycle. The
  notification helper (`NotificationDispatcher`) writes to the DB inside the
  caller's active transaction; provider delivery is a separate, monitored
  path.
- The collector detail view optimistically reflects the next status and rolls
  back on API error.

## Audit Trail

The `AuditService` is called for every successful lifecycle transition. The
following action names are emitted:

- `pickup_created`
- `pickup_accepted`
- `pickup_started`
- `pickup_collected`
- `pickup_weight_recorded`
- `pickup_completed`
- `pickup_cancelled`
- `pickup_assignment_released`

Audit snapshots go through `sanitize_snapshot`, which strips
`phone`, `token`, `password`, `secret`, `api_key`, and similar fields. PII
never reaches the audit log.

## Notifications

Notifications are dispatched exactly once per real transition. The existing
`NotificationDispatcher` (`pickup_created`, `pickup_accepted`, `pickup_started`,
`pickup_collected`, `pickup_completed`) is reused unchanged; the new
`weight_recorded` state reuses `pickup_completed` to inform the citizen that
the weight has been reported. Repeated calls return the existing notification
without creating a new row.

## WIQ-V1-046 Integration Boundary

WIQ-V1-046 (citizen weight verification / dispute) is not implemented here.
The lifecycle now includes a dedicated `weight_recorded` state that:

- Records the collector-measured weight on the assignment.
- Does **not** mark the pickup `completed`.
- Triggers the existing `pickup_completed` notification so the citizen is
  prompted to verify.
- Allows the citizen (or admin) to either confirm or dispute the weight
  through a follow-up transition (out of scope for this issue).

This means a future WIQ-V1-046 implementation only needs to add transitions
*from* `weight_recorded` to either `completed` (citizen confirmed) or a new
`disputed` state, without rewriting the collector's canonical workflow.

## WIQ-V1-047 Compatibility

Masked communication continues to be the only contact mechanism between
citizen and assigned collector. The `_ELIGIBLE_COMMUNICATION_STATUSES` set
is extended to include `weight_recorded` so the citizen can still reach the
collector while verification is pending. Completed and cancelled pickups
remain contact-inactive.

## Frontend Behavior

- `CollectorPickupActions` exposes state-appropriate buttons:
  - `pending` → Accept Request
  - `accepted` → Start Trip / Release Request
  - `on_the_way` → Mark as Collected
  - `collected` → Record Weight
  - `weight_recorded` → Mark as Completed
  - `completed` / `cancelled` → no actions
- Buttons are disabled while a mutation is in flight to prevent duplicate
  submissions.
- `ProgressTracker` renders `weight_recorded` as an explicit intermediate
  step with a distinct colour.
- The contact button is hidden outside the eligible communication statuses.

## Database

No new migrations were required. The new `weight_recorded` enum value is
registered in the existing `PickupStatus` enum and is persisted as a string
column. The unique constraint on `collector_assignments.request_id` already
guarantees single-assignment semantics for the accept race.

## Test Coverage

A new file `tests/test_collection_workflow.py` covers:

- All valid transitions, including `weight_recorded`.
- All invalid transitions (rejection or idempotent no-op).
- Idempotency for accept, start, collect, record-weight, complete.
- Repeated weight recording with the same / different values.
- Authorization (collector A vs B, citizen vs collector).
- Audit event emission and non-duplication on retries.
- Notification emission and non-duplication on retries.
- WIQ-V1-047 masked communication compatibility.

Existing tests in `test_collector.py`, `test_citizen.py`,
`test_masked_communication.py`, `test_security_boundaries.py`, and
`test_notifications.py` continue to pass without modification to their
semantic expectations.

## Validation

- `pytest` → 662 passed (632 prior + 30 new).
- `ruff check` → clean.
- `black --check` → clean.
- `mypy app` → no issues.
- `npm test` → 204 passed.
- `npm run build` → succeeded.
