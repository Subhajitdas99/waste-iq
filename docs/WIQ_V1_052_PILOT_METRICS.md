# WIQ-V1-052 — Pilot Metrics & Operational Dashboard

Issue: **#98 (WIQ-V1-052)**

## Summary

Adds an admin-facing "Pilot Metrics" snapshot that aggregates platform data
already captured in the database. The snapshot surfaces honest, derived
metrics (collection, timing, weight quality, activity) and explicitly marks
unavailable signals (API errors, notification failures, job failures, uptime)
as **N/A** rather than fabricating zero values.

## Endpoint

`GET /api/v1/admin/analytics/pilot`

- **Auth:** `require_roles("admin")` (unchanged from existing analytics routes).
- **Response model:** `PilotMetrics` (see `backend/app/schemas/analytics.py`).
- **No PII:** All metrics are platform aggregates; no user names, emails, or
  identifiers are returned.

## Response shape

```json
{
  "window": { "start": "...", "end": "...", "days": 42 },
  "collection": { "total_pickups": 0, "completed_pickups": 0, ... },
  "timing": { "median_request_to_acceptance_hours": null, ... },
  "weight_quality": { "pickups_with_estimate": 0, ... },
  "activity": { "pickups_last_7_days": 0, ... },
  "reliability": { "api_error_rate_available": false, ... }
}
```

## Source-of-truth audit

Each metric was traced to the database columns or jobs module that already
capture the underlying signal. Metrics that **cannot** be derived from
authoritative state are returned as `null` with `available=false` and a
human-readable `note`.

| Metric | Source | Status |
| --- | --- | --- |
| Total / completed / cancelled pickups | `pickup_requests.status` | ✅ available |
| Completion rate | derived | ✅ available |
| Total / average weight | `collector_assignments.weight_kg` joined to completed pickups | ✅ available |
| Active citizens | `COUNT(DISTINCT pickup_requests.user_id)` | ✅ available |
| Active collectors | `COUNT(DISTINCT collector_assignments.collector_id)` | ✅ available |
| Request → acceptance timing | `pickup_requests.created_at`, `collector_assignments.accepted_at` | ✅ available |
| Acceptance → completion timing | `collector_assignments.accepted_at` / `completed_at` | ✅ available |
| Estimate vs actual weight | `pickup_requests.estimated_weight_kg` vs `collector_assignments.weight_kg` | ✅ available |
| Disputes upheld / corrected | `pickup_disputes.resolution` enum | ✅ available |
| Pickups (7d / 30d) | `pickup_requests.created_at` window filter | ✅ available |
| Lots listed / sold | `inventory_lots.status` | ✅ available |
| Pending dealer applications | `dealer_profiles.approval_status == submitted` | ✅ available |
| **API error rate** | none — audit log is admin actions only | ❌ N/A |
| **Notification failure rate** | none — notifications written synchronously, no failure status | ❌ N/A |
| **Background job failure count** | none — only `last_runs` timestamp is persisted | ❌ N/A |
| **Platform uptime** | none — no uptime tracking | ❌ N/A |

### Why these are explicitly N/A

- **Audit logs** record administrative actions (approvals, edits, login
  events), not request/response outcomes. They cannot be used to compute an
  API error rate without middleware instrumentation.
- **Notifications** are created in-band with the originating request. The
  `notifications` table has no `status` for delivery failure.
- **Background jobs** (`app/services/jobs.py`) persist `last_runs` as a
  module-level dict but no failure history. A dedicated job history table is
  required.
- **Platform uptime** is not tracked anywhere in the application layer.

In each case, the response returns `null` plus `*_available=false` and
`*_note="..."` so the UI can render a clear "N/A" and admins can see **why**
the metric is not shown — not a misleading zero.

## Window selection

- Start: `MIN(pickup_requests.created_at)` so the window reflects actual
  pilot history (never empty). Falls back to `now - 30 days` when no
  requests exist yet.
- End: `now` (UTC).
- `days` is the inclusive count, clamped to `>= 1`.

## Frontend

- New types in `frontend/src/types/admin.ts` (`PilotMetrics`, etc.).
- New `getPilotMetrics()` in `frontend/src/api/admin.ts`.
- New `usePilotMetrics()` hook in `frontend/src/hooks/useAdminDashboard.ts`.
- New `<PilotMetricsSection />` rendered in `AdminOverviewPage.tsx` below
  the dealer review queue. It includes:
  - KPI cards (total pickups, completion rate, total weight, active citizens).
  - Workflow timing block (median + average hours).
  - Weight quality block (estimates, recorded, dispute counts).
  - Recent activity block (7d/30d pickups, lots, pending dealers).
  - Operational reliability block (N/A signals with notes).

## Tests

`backend/tests/test_pilot_metrics.py` covers:

- Empty state (no pickups) — all metrics return safe defaults; reliability
  fields are all `available=false`.
- Collection KPIs with completed + cancelled pickups.
- Timing calculations (median + average hours, sample size).
- Weight quality with estimate + recorded weight + a dispute (upheld).
- Activity windows (7d / 30d) and dealer lot counts.
- Reliability fields are always N/A.
- RBAC: non-admin requests get 403.

## Out of scope (follow-up)

- Middleware-based API request/error instrumentation.
- Async notification pipeline with delivery state.
- Background job history table (with `success/failure` outcomes).
- Health-check / uptime tracking (external monitoring).
