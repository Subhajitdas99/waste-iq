# Waste-IQ V1 Security & Authorization Audit / Remediation (WIQ-V1-044)

**Document Version:** 1.0.0  
**Audit Date:** 2026-08-27  
**Auditor:** Lead Systems & Security Engineer  
**Repository:** `Waste-IQ`  
**Branch:** `feature/wiq-v1-044-security-authorization`  
**Baseline Commit:** `2ae1bd6`  

---

## 1. Executive Summary

As part of the Waste-IQ V1 Launch Readiness roadmap, a comprehensive security and authorization audit was conducted to identify, remediate, and verify all launch-blocking authorization, privacy, authentication, and role-boundary vulnerabilities.

### Key Outcomes:
1. **Email Verification Enforcement (`P1` - Remediated):** Enforced verified-account checks across all state-mutating and sensitive operations (`POST /pickup-requests`, `POST /collector/pickups/{id}/accept`, `POST /dealer/profile/submit`, `POST /marketplace/inventory/{id}/reserve`, etc.). Unverified accounts are prevented from performing domain mutations.
2. **Citizen PII Exposure Redaction (`P0` - Remediated):** Eliminated plaintext citizen phone number leakage in unassigned public queues (`/collector/pickups/available`, `/collector/nearby`, `/collector/pickups/{id}`). Phone numbers are now strictly restricted to the owning citizen, the specifically assigned collector, or administrators.
3. **Object-Level Authorization (IDOR/BOLA) (Verified & Tested):** Verified that strict ownership filters are authoritative in the backend across pickups, collector assignments, dealer inventory, marketplace orders, and notifications.
4. **No Database Migration Required:** All security controls were implemented cleanly in the application service and dependency layers with zero schema drift.

---

## 2. Scope of Audit

The audit covered all backend and frontend layers:
- **Authentication & Security Core:** `backend/app/core/security.py`, `backend/app/core/dependencies.py`, `backend/app/core/ratelimit.py`.
- **API Route Handlers:**
  - Citizen & Pickups: `backend/app/api/routes/pickup_requests.py`
  - Collector Lifecycle & Navigation: `backend/app/api/routes/collector.py`, `backend/app/api/routes/collector_map.py`
  - Dealer & Marketplace: `backend/app/api/routes/dealer.py`, `backend/app/api/routes/marketplace.py`, `backend/app/api/routes/inventory.py`
  - Administration & Governance: `backend/app/api/routes/admin.py`, `backend/app/api/routes/analytics.py`, `backend/app/api/routes/audit_logs.py`, `backend/app/api/routes/jobs.py`
  - Notifications & Sessions: `backend/app/api/routes/notifications.py`, `backend/app/api/routes/auth.py`
- **Domain Services & Repositories:** All service classes ensuring server-side authorization enforcement.
- **Frontend Route Protection:** `frontend/src/routes/ProtectedRoute.tsx`, ensuring client routing mirrors server-authoritative rules.

---

## 3. Existing Security Architecture Review

Waste-IQ's security foundation incorporates modern enterprise defensive patterns:
- **Authentication:** Dual-token model with short-lived JWT access tokens and opaque 384-bit rotated refresh tokens stored as SHA-256 digests. Token reuse triggers family revocation.
- **Abuse Prevention:** In-memory sliding-window rate limiters per IP and per account for `/auth/login`, `/auth/register`, `/auth/forgot-password`, and `/auth/resend-verification`. Account lockout is enforced after 5 failed attempts with a 15-minute cooldown.
- **Audit Logging:** Append-only structured `AuditLog` records for sensitive security and administrative actions, featuring automatic redaction of password, secret, and token fields.
- **Role Isolation:** Built-in enum roles (`citizen`, `collector`, `dealer`, `admin`) enforced via FastAPI dependency injection (`require_roles`).

---

## 4. Audit Findings & Classifications

### Finding 1: Unverified Account Mutation Access
- **Classification:** `CONFIRMED VULNERABILITY` (Remediated)
- **Severity:** `P1 (Critical)`
- **Component / Endpoints:**
  - `POST /pickup-requests`, `PATCH /pickup-requests/{id}`, `POST /pickup-requests/{id}/cancel`
  - `POST /collector/pickups/{id}/accept`, `/start`, `/collect`, `/complete`, `/cancel`
  - `POST /collector/location`
  - `POST /dealer/profile/submit`, `/dealer/inventory/*`
  - `POST /marketplace/inventory/{id}/reserve`, `/cancel-reservation`, `/purchase`
- **Affected Roles:** Citizen, Collector, Dealer
- **Attack Scenario:** A malicious user creates disposable accounts with invalid/fake emails and immediately spams fraudulent pickup requests or claims legitimate collector jobs, disrupting real-world operations without verifying email ownership.
- **Current Behavior:** Handlers only checked authentication and role enum; `user.email_verified` was ignored during mutation execution.
- **Expected Behavior:** Stateful mutations must reject unverified users with HTTP 403 `{"detail": "Email verification required"}`.
- **Remediation:**
  - Added `require_verified_user` and `require_verified_roles(*roles)` in `app/core/dependencies.py`.
  - Applied verified dependency guards to all state-mutating endpoints across citizen, collector, and dealer routers.
- **Regression Test:** `tests/test_security_boundaries.py::test_unverified_citizen_cannot_create_pickup`, `test_unverified_collector_cannot_accept_pickup`, `test_unverified_dealer_cannot_submit_profile`, etc.

---

### Finding 2: Plaintext Citizen Phone Number Exposure in Public Collector Queues
- **Classification:** `CONFIRMED VULNERABILITY` (Remediated)
- **Severity:** `P0 (Blocker)`
- **Component / Endpoints:**
  - `GET /collector/pickups/available`
  - `GET /collector/nearby`
  - `GET /collector/pickups/{id}` (for unassigned pending pickups)
- **Affected Roles:** Citizen (victims), Collector (recipient)
- **Attack Scenario:** Any registered collector queries the public/available pickup queue and scrapes the personal phone numbers of every citizen who submitted a pickup across the city.
- **Current Behavior:** `_to_schema()` unconditionally populated `citizen_phone = pickup_request.citizen.phone`.
- **Expected Behavior:** Unassigned/public pickup listings must have `citizen_phone: null`. Raw phone numbers must only be visible to:
  1. The citizen owner of the request.
  2. The specifically assigned collector once a job is accepted.
  3. Administrators.
- **Remediation:**
  - Implemented `_should_expose_phone(pickup_request, viewer)` in `app/services/pickup_requests.py`.
  - Updated `_to_schema`, `_to_nearby_schema`, and `_to_detail_schema` to accept the authenticated viewer and redact `citizen_phone` to `None` for unassigned viewers.
- **Regression Test:** `tests/test_security_boundaries.py::test_available_pickup_queue_redacts_citizen_phone`, `test_nearby_pickup_queue_redacts_citizen_phone`, `test_unassigned_pickup_detail_redacts_citizen_phone_for_collector`, `test_assigned_pickup_exposes_citizen_phone_only_to_assigned_collector`.

---

### Finding 3: Object-Level Authorization / IDOR Boundaries
- **Classification:** `ALREADY PROTECTED / VERIFIED WITH TESTS`
- **Severity:** `P1 (Critical)`
- **Component / Endpoints:** All entity lookup and mutation endpoints accepting entity IDs (`pickup_id`, `inventory_id`, `order_id`, `notification_id`).
- **Affected Roles:** All roles
- **Audit Findings:**
  - **Pickups:** `_enforce_request_access` and `_ensure_assigned_collector` ensure Citizen A cannot view/modify Citizen B's pickup, and Collector A cannot modify pickups assigned to Collector B.
  - **Dealer Inventory:** Repository and service queries explicitly include `dealer_id == current_user.id`, returning 404 for unowned inventory items.
  - **Marketplace Orders:** `get_marketplace_order` explicitly enforces `order.dealer_id == dealer.id`.
  - **Notifications:** All notification operations (`get_for_user`, `mark_read`, `delete`) query by `(user_id, notification_id)`.
  - **Admin Endpoints:** All `/admin/*`, `/admin/jobs/*`, `/admin/audit-logs`, `/admin/analytics/*` routes enforce `require_roles("admin")`.
- **Regression Test:** `tests/test_security_boundaries.py::test_collector_a_cannot_mutate_collector_b_assigned_pickup`, `test_collector_cannot_navigate_to_another_collectors_assigned_pickup`, `test_user_cannot_access_other_users_notification`, `test_non_admin_cannot_access_admin_endpoints`.

---

## 5. PII & Data Classification Matrix

| Data Field | Collector (Available Queue) | Collector (Assigned Job) | Citizen (Owner) | Admin | Classification |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `waste_type` | Visible | Visible | Visible | Visible | **Publicly Necessary** |
| `estimated_weight_kg` | Visible | Visible | Visible | Visible | **Publicly Necessary** |
| `preferred_time` | Visible | Visible | Visible | Visible | **Publicly Necessary** |
| `notes` | Visible | Visible | Visible | Visible | **Role-Restricted** |
| `address` | Visible | Visible | Visible | Visible | **Role-Restricted** |
| `latitude` / `longitude` | Visible | Visible | Visible | Visible | **Role-Restricted** |
| `image_url` | Visible | Visible | Visible | Visible | **Role-Restricted** |
| `citizen_name` | Visible | Visible | Visible | Visible | **Role-Restricted** |
| `citizen_phone` | **REDACTED (null)** | **Visible (Temporary until WIQ-V1-047)** | **Visible** | **Visible** | **SENSITIVE PII** |
| `citizen_email` | **Hidden** | **Hidden** | **Visible** | **Visible** | **SENSITIVE PII** |

---

## 6. Remediations Implemented

1. **`backend/app/core/dependencies.py`**:
   - Added `require_verified_user` dependency.
   - Added `require_verified_roles(*roles)` dependency.
2. **`backend/app/services/pickup_requests.py`**:
   - Added `_should_expose_phone()` logic.
   - Updated `_to_schema()`, `_to_nearby_schema()`, and `_to_detail_schema()` to accept `viewer` parameter and redact `citizen_phone` for unassigned viewers.
   - Updated all list, detail, and mutation functions to pass `viewer` accurately.
3. **`backend/app/api/routes/pickup_requests.py`**:
   - Guarded `create_request` with `require_verified_roles("citizen")`.
   - Guarded `patch_request` with `require_verified_user`.
   - Guarded `cancel_request` with `require_verified_roles("citizen")`.
4. **`backend/app/api/routes/collector.py` & `collector_map.py`**:
   - Guarded pickup acceptance, start, collect, complete, and cancel routes with `require_verified_roles("collector")`.
   - Guarded `report_collector_location` with `require_verified_roles("collector")`.
5. **`backend/app/api/routes/dealer.py` & `marketplace.py`**:
   - Guarded dealer profile creation/update/submission with `require_verified_roles("dealer")`.
   - Guarded dealer inventory mutations and marketplace reservations/purchases with `require_verified_roles("dealer")`.
6. **`backend/tests/conftest.py`**:
   - Enhanced user test factories to support `email_verified=True` (default) and `email_verified=False`.
7. **`backend/tests/test_security_boundaries.py`**:
   - Created 14 dedicated security boundary tests covering verification enforcement, PII redaction, IDOR boundaries, and admin access control.

---

## 7. Deferred Items & Dependencies on Downstream Tasks

1. **WIQ-V1-047 (Masked Communication & Virtual Relay):**
   - *Current State:* While unassigned queues are now completely redacted (`citizen_phone = null`), assigned collectors still receive the citizen's raw phone number once a job is accepted.
   - *Downstream Action (WIQ-V1-047):* Replace the assigned collector phone exposure with an in-app messaging proxy or virtual masking service.
2. **WIQ-V1-046 (Weight Verification & Dispute Resolution):**
   - *Current State:* Collector completing a pickup immediately sets the final weight.
   - *Downstream Action (WIQ-V1-046):* Implement `weight_submitted` / `disputed` statuses and citizen verification endpoints.

---

## 8. Test Coverage & Validation Results

### Backend Test Suite
- **Total Tests:** 620 passed (14 new security tests added).
- **Execution Time:** ~7m 16s.
- **Failures:** 0.

### Code Quality & Static Analysis
- **Ruff:** `All checks passed!` (0 lint errors).
- **Black:** Clean (0 formatting discrepancies).
- **Mypy:** `Success: no issues found in 95 source files`.

### Frontend Test Suite & Build
- **Vitest:** 204 passed, 0 failures.
- **Vite Production Build:** `tsc -b && vite build` succeeded in 10.86s.

### Database Migrations
- **Alembic Head:** `20260821_0019` (Single head, zero migrations added/modified).

---

## 9. Remaining Launch Risks

1. **Assigned Contact Exposure:** Unmasked contact for assigned collectors remains until WIQ-V1-047 is completed.
2. **Weight Dispute Liability:** Collectors recording final weights without citizen verification remains until WIQ-V1-046 is implemented.

---
*Report certified by Lead Systems & Security Engineer — Waste-IQ Security Team.*
