# WIQ-V1-046 — Waste Weight Verification & Dispute Workflow

**Status:** Implemented
**Feature Branch:** `feature/wiq-v1-046-weight-verification`
**Base:** `develop` (36c392b)

---

## Overview

WIQ-V1-046 adds a mandatory citizen verification step between collector weight recording and final pickup completion. After a collector records the measured weight, the citizen must explicitly confirm or dispute the weight before the pickup transitions to `completed`. Disputed pickups enter an admin-review workflow.

---

## State Machine

### Extended Lifecycle

```
pending
  → accepted          (collector accepts)
  → on_the_way        (collector starts trip)
  → collected         (collector marks collected)
  → weight_recorded   (collector records measured weight)
  ──────────────────────────────────────────────── WIQ-V1-046 boundary
  → disputed          (citizen disputes weight)
  → completed         (citizen confirms OR admin resolves)
```

### State Transitions

| From | To | Actor | Endpoint |
|---|---|---|---|
| `collected` | `weight_recorded` | collector | `POST /collector/pickups/{id}/record-weight` |
| `weight_recorded` | `completed` | citizen | `POST /pickup-requests/{id}/weight/confirm` |
| `weight_recorded` | `disputed` | citizen | `POST /pickup-requests/{id}/weight/dispute` |
| `disputed` | `completed` | admin | `POST /admin/disputes/pickups/{id}/resolve` |
| `collected` | `completed` | collector | Legacy path (see below) |

### Legacy Collector Completion Path

The collector `complete` endpoint (`POST /collector/pickups/{id}/complete`) is retained for backward compatibility and legacy scenarios. It only accepts `collected` as a source state — **not** `weight_recorded`. This prevents collectors from bypassing citizen verification.

### Invalid Transitions (Enforced Server-Side)

- Citizen cannot confirm/dispute before `weight_recorded`
- Citizen cannot dispute a `completed` or `cancelled` pickup
- Collector cannot `complete` from `weight_recorded`
- Admin cannot resolve a non-disputed pickup
- Resolution of an already-resolved dispute returns the current state

---

## Weight Immutability

The collector's original recorded measurement on `collector_assignments.weight_kg` is **never overwritten** by dispute or resolution:

- **Confirmed pickup:** original weight remains on `assignment.weight_kg`
- **Upheld dispute:** original weight on `assignment.weight_kg`; `dispute.resolved_weight_kg` is null
- **Corrected dispute:** original weight preserved on `assignment.weight_kg`; corrected weight stored on `dispute.resolved_weight_kg`

The `pickup_disputes.resolved_weight_kg` column stores the admin-accepted corrected weight separately.

---

## Dispute Model

### `pickup_disputes` Table

| Column | Type | Description |
|---|---|---|
| `id` | PK | |
| `request_id` | FK → `pickup_requests` | One dispute per pickup (unique) |
| `reason` | Text | Citizen-provided dispute reason |
| `disputed_at` | DateTime | Server-assigned timestamp |
| `resolved_at` | DateTime | Set by admin resolution |
| `resolution` | Enum | `upheld` or `corrected` |
| `resolved_weight_kg` | Float | Admin-set corrected weight |
| `resolution_notes` | Text | Admin notes |
| `resolved_by_id` | FK → `users` | Admin who resolved |

### Dispute Resolution Outcomes

- **`upheld`:** Accept the collector's original measurement; pickup transitions to `completed`
- **`corrected`:** Accept the dispute; the corrected weight is stored in `resolved_weight_kg`; pickup transitions to `completed`

---

## API Endpoints

### Citizen Weight Confirmation

```
POST /pickup-requests/{request_id}/weight/confirm
Role: citizen (owner only)
Status: weight_recorded
Idempotent: yes (confirmed pickup returns 200)
```

### Citizen Weight Dispute

```
POST /pickup-requests/{request_id}/weight/dispute
Role: citizen (owner only)
Status: weight_recorded or disputed
Body: { "reason": string (5-2000 chars) }
Idempotent: yes (same reason returns 200; different reason returns 409)
```

### Admin Dispute Resolution

```
GET /admin/disputes/pickups
Role: admin
Pagination: page, page_size

POST /admin/disputes/pickups/{request_id}/resolve
Role: admin
Status: disputed only
Body: { "resolution": "upheld" | "corrected", "resolved_weight_kg"?: float, "notes"?: string }
Corrected requires resolved_weight_kg (0.01–10000)
Idempotent: yes (already-resolved returns current state)
```

---

## Authorization Boundaries

| Role | Can Confirm | Can Dispute | Can View Weight | Can Resolve |
|---|---|---|---|---|
| citizen (owner) | yes | yes | yes | no |
| citizen (other) | no | no | 403 | no |
| collector (assigned) | no | no | via API | no |
| collector (other) | no | no | 403 | no |
| admin | no | no | yes (via admin endpoint) | yes |

### Security Properties Preserved

- **WIQ-V1-044:** Role-based authorization boundaries enforced
- **WIQ-V1-047:** Masked communication compatible; phone numbers not exposed to collectors
- **WIQ-V1-045:** State machine, audit trail, notifications preserved

---

## Audit Events

| Event | Actor | Trigger |
|---|---|---|
| `pickup_weight_recorded` | collector | Weight recorded |
| `pickup_weight_confirmed` | citizen | Weight confirmed |
| `pickup_weight_disputed` | citizen | Dispute filed |
| `pickup_dispute_resolved` | admin | Admin resolves |
| `pickup_dispute_reviewed` | admin | Admin reviews |

### Audit Snapshot Rules

- Phone numbers are never recorded in audit snapshots (enforced by `AuditService.sanitize`)
- `weight_kg` values are included (not PII)
- Dispute reason is **not** included in the audit snapshot (to avoid recording the reason)

---

## Notifications

| Event | Recipient | Notification Type |
|---|---|---|
| Collector records weight | citizen | `weight_recorded` |
| Citizen confirms | citizen | `weight_confirmed` |
| Citizen disputes | citizen | `weight_disputed` |
| Citizen disputes | collector | `weight_disputed` |
| Admin resolves | citizen | `dispute_resolved` |

Notifications are **not** duplicated on idempotent retries. Each notification helper is called only once per successful state transition.

---

## Idempotency & Concurrency

| Operation | Idempotent Behavior |
|---|---|
| Record weight (same value) | Returns current state, no new event/audit/notification |
| Record weight (different value) | Returns 409 Conflict |
| Confirm (already completed) | Returns current state |
| Confirm (weight_recorded) | Transitions to completed |
| Dispute (same reason) | Returns current disputed state |
| Dispute (different reason) | Returns 409 Conflict |
| Resolve (already resolved) | Returns current state |

---

## Database Migration

**Migration:** `20260828_0020_pickup_weight_dispute`

Creates `pickup_disputes` table (additive, non-destructive). Extends `PickupStatus` enum with `disputed` value. No existing data is modified.

---

## Testing

- **Backend:** 35 dedicated tests in `test_weight_verification.py`
- **Integration:** Existing `test_collection_workflow.py` updated to use WIQ-V1-046 paths
- **Frontend:** 5 lifecycle tests updated; 204 tests total passing
- **Security:** IDOR, authorization, audit PII sanitization all verified

---

## Frontend Changes

### Citizen View (`PickupDetailsPage`)

- Weight Verification card appears when status is `weight_recorded`, `disputed`, or `completed`
- Shows recorded weight and current status badge
- **Confirm Weight** button (only in `weight_recorded` state)
- **Dispute Weight** button with reason modal (only in `weight_recorded` state)
- Disputed state shows reason and timestamp
- Completed state shows confirmation message

### Collector View (`CollectorPickupActions`)

- `weight_recorded` state shows informational badge: "Weight recorded — awaiting citizen confirmation"
- `disputed` state shows informational badge: "Weight disputed — under admin review"
- No completion actions available in these states

### Status Configuration

- `PICKUP_STATUS_FLOW` includes `weight_recorded` and `disputed`
- Progress tracker shows all 7 active states
- `getPickupProgress` maps correctly through the extended flow
