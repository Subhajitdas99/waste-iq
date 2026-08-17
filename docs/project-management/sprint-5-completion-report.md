# Sprint 5 Completion Report — Citizen Experience: Rich Pickup Requests, AI Preview, Notifications

**Project:** Waste-IQ (FastAPI backend + React 18 frontend)
**Sprint:** 5 — Citizen Experience (phase 1 of the guided build)
**Scope:** Pickup request creation with weight/preferred time/notes/image, AI preview placeholder, tracking, history (existing), dashboard impact + notifications, a11y, tests, and full verification.
**Date:** 31 Jul 2026

---

## 1. Summary

Sprint 5 delivered the full citizen request contract end to end. The backend now accepts `estimated_weight_kg`, `preferred_time`, and `notes` on pickup-request creation (validated, persisted, returned); the frontend request form was rewritten as a 3-step wizard carrying all Sprint 5 fields plus the existing image upload; and the dashboard gained a recycling-impact panel and a persistent, local notifications feed derived from pickup status transitions. Every gate is green: backend 155/155 tests, frontend 123/123 tests, all four coverage metrics above the 80% threshold, `tsc` clean, lint 0 errors, and a production build that succeeds.

---

## 2. Deliverables

### 2.1 Backend — pickup request details

- **Model + schema** (`app/models/pickup_request.py`, `app/schemas/pickup_request.py`): added `estimated_weight_kg` (float, `ge=0`, `le=10000`), `preferred_time` (datetime, nullable), `notes` (string, `max_length=2000`) to `PickupRequestCreate`, `PickupRequestRead`, and the SQLAlchemy model.
- **Route** (`app/api/routes/pickup_requests.py`): create endpoint now parses the three fields from `Form(...)` with the same constraints; `preferred_time` accepts ISO-8601 strings.
- **Creation service** (`app/services/pickup_request_creation.py`): persists the new fields.
- **Critical fix**: payload serialization switched from `model_dump(mode="json")` to `model_dump(mode="python")` so `preferred_time` reaches the insert as a `datetime`, not an ISO string — required for SQLite/portable inserts.
- **Serializer** (`app/services/pickup_requests.py`): emits the three fields in every pickup-request response (list and detail).
- **Migration** (`alembic/versions/20260731_0009_pickup_request_details.py`, down_revision `458a9daa25fd`): adds the three columns; hand-sequenced to sit after the Sprint 4 head.
- **Backend tests** (`tests/test_citizen.py`): +5 tests — Sprint 5 details roundtrip on create, null defaults when omitted, 422 on weight outside 0–10,000 kg, 422 on notes over 2,000 chars, and list roundtrip. Full suite: **155 passed**.

### 2.2 Frontend — request creation wizard

- **Types + API** (`src/types/pickup.ts`, `src/api/pickupRequests.ts`, `src/test/factories.ts`): `PickupRequest`/`CreatePickupRequestPayload` gained the three fields; `buildPickupFormData` appends them (numbers stringified, nulls omitted); factory defaults them to null.
- **`NewPickupPage.tsx` rewritten** as a 3-step wizard (Material / Location & Details / Review) with:
  - Zod validation: weight 0.1–10,000 kg, future-only `preferred_time`, notes ≤ 2,000 chars, image type jpg/jpeg/png/webp and ≤ 10 MB;
  - step-scoped validation (`trigger` on the current step's fields only) and a Back button that preserves entered values;
  - review step showing the exact backend payload preview;
  - success panel with the request id, status, AI image preview placeholder, and a link to the details page;
  - side cards documenting the supported request fields and the AI classifier standby behaviour (model returns `Unknown` / 0% until the inference service is deployed).
- **`PickupDetailsPage.tsx`**: info grid now shows requested vs preferred pickup time, estimated weight, AI category + confidence (with standby note), and notes.
- **`PickupCard.tsx`**: weight stat falls back to `estimated_weight_kg` when no assignment weight exists; expanded details show estimated weight, preferred time, and notes.

### 2.3 Dashboard — recycling impact and notifications

- **`src/lib/recycling.ts`**: `computeRecyclingImpact` sums completed pickups' weights into Total Recycled / CO₂ Saved (`0.42` kg CO₂ per kg) / Eco Points (`10` per kg), with `formatImpactNumber` display formatting.
- **`src/components/dashboard/RecyclingImpactCard.tsx`**: three-stat card (Total Recycled / CO₂ Saved / Eco Points).
- **`src/hooks/useCitizenNotifications.ts`**: pure `deriveNotifications` + `useCitizenNotifications` hook. No backend notification endpoints exist, so notifications are derived client-side from pickup status transitions and persisted to `localStorage` (`wasteiq_citizen_notifications_v1` / `wasteiq_citizen_pickup_statuses_v1`, capped at 30). First run seeds statuses silently; notifications fire only on transitions (created, accepted, on-the-way, collected, completed, cancelled) or new requests. The derive function returns the previous status-map reference when nothing changed so the persistence effect stays loop-free.
- **`src/components/dashboard/NotificationsPanel.tsx`**: unread badge (`aria-label` with the unread count), mark-one-read / mark-all-read actions, `aria-live` region; empty state.
- **`DashboardOverviewPage.tsx`**: wired both panels in place of the announcements placeholder.

### 2.4 Testing (frontend)

- New suites: `src/test/recycling.test.ts` (pure computation), `src/test/notifications.test.tsx` (derive logic + hook/panel flows with rerenders simulating status transitions), `src/test/new-pickup.test.tsx` (wizard validation, image rejection, full payload submission via multipart capture, AI preview result, back-button walkthrough).
- `src/test/handlers.ts`: global `http.post("*/pickup-requests")` handler echoes the new fields and returns `image_url` + `category: "Unknown"` + `confidence: 0` when an image is present.

### 2.5 Issues found and fixed during verification

1. **First-run seeding bug** (`useCitizenNotifications`): the first-run branch discarded the seeded status map (`nextStatusMap: previousStatusMap`), so transition notifications never fired. Fixed by returning the updated map on first run.
2. **Test env multipart limitation**: MSW 2.15 + jsdom drops File bytes when a multipart body is parsed with `request.formData()` (undici assertion crash). Payload assertions now capture `request.text()` and assert on multipart parts (string fields fully asserted; the image part's `name="image"` + `Content-Type` prove it is attached). The image→`image_url` round-trip remains covered by the AI-preview test.
3. **Success banner unreachable** (`NewPickupPage`): the "was created successfully" banner lived inside the Review-step block, but `onSubmit` resets to step 0 — the banner could never render. Moved it above the wizard so it persists on every step after success.
4. **Test corrections**: notifications tests must render a pending baseline before rerendering changed statuses (first-run seeding is silent by design); heading queries disambiguated from stepper labels; a 2,001-char notes validation uses `fireEvent.change` instead of 2,001 typed keystrokes (test timeout).

---

## 3. Verification Results (all green)

### Backend (`F:\waste-iq\backend`, venv Python)

| Gate | Command | Result |
|---|---|---|
| Tests | `.\venv\Scripts\python.exe -m pytest tests -q` | **155 passed** (21 citizen-suite incl. 5 new Sprint 5 tests) |

### Frontend (`F:\waste-iq\frontend`)

| Gate | Command | Result |
|---|---|---|
| TypeScript | `npx tsc -b --noEmit` (via `npm run build`) | exit 0 |
| Lint | `npm run lint` | exit 0 — 0 errors, 3 pre-existing fast-refresh warnings (accepted convention) |
| Tests | `npm run test` | 13/13 suites, **123/123 tests passed** (was 99; +24 from Sprint 5) |
| Coverage | `npm run test:coverage` | Statements **89.42%** · Branches **80.95%** · Functions **87.2%** · Lines **89%** (threshold 80% each) |
| Build | `npm run build` | exit 0 — 2,183 modules, ~17 s; `NewPickupPage` chunk 17.4 kB (5.3 kB gzip) |

---

## 4. Sprint 5 Recommendations (not blocking)

1. **Real AI inference** — `ai_classifier.py` still returns `Unknown`/0.0 by design; deploy the YOLOv8 service and the success panel / details page will render real categories automatically.
2. **Server-side notifications** — derive-to-localStorage works, but a real `notifications` endpoint (or SSE/WebSocket push) would make the feed multi-device and collector-triggered; the hook is structured so `deriveNotifications` can be swapped for a server feed.
3. **`preferred_time` scheduling** — no collector-side scheduling UI exists yet; the field is informational until a scheduler is added.
4. **Apply the new migration** — `20260731_0009_pickup_request_details.py` is written but not yet applied to a live database (`alembic upgrade head`).
5. **Weight verification** — estimated weight is citizen-entered; consider collector-side confirmation during completion (currently only the reported `weight_kg` on the assignment is authoritative).

---

## 5. Files Changed in Sprint 5

**Backend:**
- `app/models/pickup_request.py`, `app/schemas/pickup_request.py`, `app/api/routes/pickup_requests.py`, `app/services/pickup_request_creation.py`, `app/services/pickup_requests.py`
- `alembic/versions/20260731_0009_pickup_request_details.py` (new)
- `tests/test_citizen.py`

**Frontend — modified:**
- `src/pages/dashboard/NewPickupPage.tsx` (wizard rewrite), `src/pages/dashboard/PickupDetailsPage.tsx`, `src/pages/dashboard/DashboardOverviewPage.tsx`
- `src/components/dashboard/PickupCard.tsx`
- `src/types/pickup.ts`, `src/api/pickupRequests.ts`
- `src/test/handlers.ts`, `src/test/factories.ts`

**Frontend — new:**
- `src/lib/recycling.ts`
- `src/hooks/useCitizenNotifications.ts`
- `src/components/dashboard/NotificationsPanel.tsx`, `src/components/dashboard/RecyclingImpactCard.tsx`
- `src/test/recycling.test.ts`, `src/test/notifications.test.tsx`, `src/test/new-pickup.test.tsx`

---

## 6. Conclusion

Sprint 5 completes the citizen pickup-request experience: rich validated requests (weight, preferred time, notes, photo), an AI preview placeholder wired to the existing classifier contract, status tracking and history, and a dashboard with recycling impact and live local notifications. Backend 155/155 and frontend 123/123 tests pass, coverage is above the 80% gate on every metric, and the build/lint/type gates are clean. The remaining recommendations are enhancement items — none block the next sprint.
