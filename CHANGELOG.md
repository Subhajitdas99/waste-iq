# Changelog

All notable changes to Waste-IQ will be documented in this file.

This project adheres to [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **Dealer Profile & Approval Workflow** — full dealer application lifecycle with a four-state `approval_status` enum (`draft → submitted → approved/rejected`): dealers create, update, and submit their business profile via `/dealer/profile*`; admins review a pending queue (`GET /admin/dealers/pending`), approve, or reject with a required reason; every transition is recorded in a new `dealer_profile_events` audit table with actor attribution, surfaced as an approval timeline on the dealer profile page; inventory browsing and management are gated on an approved profile (403 with explanatory detail otherwise); admin review queue now supports inline approve/reject actions with a rejection-reason dialog
- **Collector Pickup Lifecycle** — implemented complete collector workflow from accepting a pickup request through completion. Added robust backend state transitions (pending → accepted → on_the_way → collected → completed), backend APIs, timeline event creation, and comprehensive React frontend dashboards (`CollectorOverviewPage`, `CollectorPickupDetailsPage`) with optimistic updates.
- **AI Analytics Dashboard** — admin-only analytics suite under `/admin/analytics/*` with platform overview KPIs, material distribution, 12-month pickup trends, collector/dealer performance rankings, carbon savings, and deterministic rule-based AI insights (no LLM); served by a dedicated analytics service layer with typed Pydantic v2 schemas and a new React 19 dashboard page (`/admin/analytics`) with reusable chart and card components
- **AI Waste Classification v2** — improved classification confidence scores using updated Cloudinary AI transformations; `confidence` and `category` fields now populated automatically on image upload
- **Municipality Dashboard** — new municipality-scoped admin role with city-level analytics, waste volume trends, and collector performance metrics
- **Push Notification System** — in-app and browser push notifications for pickup status changes (pending → accepted, on_the_way, completed)
- **Rewards & Incentives Module** — citizen reward points system: earn points per kg of recyclables collected, redeem for platform credits
- **Collector Route Optimization** — geospatial clustering of nearby pickup requests to suggest optimal collection routes
- **Audit Log Viewer** — admin UI to browse `inventory_lot_events` and `pickup_request_events` history with full actor attribution
- **Export to CSV** — admin and dealer users can export their data (pickups, lots, transactions) to CSV

### Changed
- **Dealer Verification → Approval Workflow** — the previous two-state `verification_status` (pending/approved/rejected) was replaced by the four-state `DealerApprovalStatus` (`draft`/`submitted`/`approved`/`rejected`) with a strict transition model enforced at both service and API layers; `pincode` renamed to `postal_code` across dealer profile schema, API, and frontend; the admin `GET /admin/dealers` endpoint now returns a paginated envelope (`items/page/page_size/total_items/total_pages`) with filtering, search, and sorting; invalid transitions return HTTP 400
- **Code Quality & Documentation Pass** — consolidated duplicated backend analytics aggregation into shared `app/services/stats.py` helpers; rewrote the pickup-request service with consistent naming and shared helper guards; centralized transaction handling in `inventory_marketplace.py` via a `_commit_or_rollback` context manager; fully type-annotated DI providers in `core/dependencies.py`; removed the debug `/debug/cors` endpoint; merged the duplicate frontend `StatsCard`/`AnalyticsCard` components (all 24 call sites now use `StatsCard` with a `tone` prop), the citizen `SettingsPage` into `RoleSettingsPage`, and extracted the shared `AccountDetailsCard` used by both profile pages; expanded the pytest fixture suite (`make_user`, `auth_headers`, `valid_pickup_payload`, `second_collector_*`) to eliminate duplicated test setup; frontend CI now runs the test suite and no longer repeats the type check that `npm run build` already performs
- **Inventory Marketplace Performance** — optimized SQL queries with additional composite indexes on `(status, visibility, source_city)` for the dealer browse endpoint
- **API Response Envelopes** — standardized error responses to include `error_code` field alongside `detail` for machine-readable error handling
- **Token Expiry UX** — frontend now shows a non-dismissible session expiry banner 5 minutes before JWT expiry, prompting re-login

### Fixed
- *(No fixes yet — coming with the next release)*

---

## [0.2.0] — 2026-06-15

### Added
- **Inventory Lot Marketplace** — full marketplace for verified scrap dealers to browse, filter, reserve (24-hour hold), and purchase inventory lots created from completed pickups
- **Inventory Lot Events Audit Trail** — `inventory_lot_events` table records every state change (created, updated, status_changed, archived, restored, reserved, reservation_expired) with actor attribution and JSON metadata
- **Admin Inventory Management** — admins can create, update, archive, and restore inventory lots; toggle visibility (visible/hidden) per lot
- **Pricing Rules Engine** — admins configure per-kg pricing rules scoped to material category + city; pricing snapshot recorded on lot creation (`unit_price_per_kg_snapshot`, `total_listed_amount`)
- **Material Categories System** — configurable master list of recyclable material categories (code, name, description, display_order, is_active); used for inventory classification and pricing
- **Dealer Profile Verification Workflow** — dealers register a business profile (business_name, owner_name, GST, license, materials_accepted); admins approve or reject; `verification_status` enum (pending → approved/rejected) gates marketplace access
- **Collector Completion Flow** — `POST /collector/complete/{id}` now requires `weight_kg` (positive float); weight is recorded on `CollectorAssignment` and used to calculate `total_listed_amount` when admin creates an inventory lot
- **Lot Reservation Expiry** — `reservation_expires_at` timestamp set to T+24h on reserve; a check at browse/reserve time enforces expiry and emits a `reservation_expired` event
- **Quality Grade Field** — inventory lots support an optional `quality_grade` field (e.g., Grade A/B/C) visible to dealers for informed purchasing decisions
- **Source Address Snapshot** — `source_address_snapshot` on inventory lots captures the citizen's original pickup address for dealer transparency
- **Admin Inventory Pricing Rules API** — CRUD endpoints for pricing rules under `/admin/inventory/pricing-rules`
- **Admin Material Categories API** — CRUD endpoints for material categories under `/admin/inventory/categories`

### Changed
- **Pickup Completion → Inventory Lot** — completing a pickup via `POST /collector/complete/{id}` now transitions the pickup to `completed` status; admins subsequently create the `InventoryLot` linked to the completed `PickupRequest` (one-to-one, CASCADE delete)
- **Collector API Endpoints Reorganized** — status-transition endpoints renamed from `/collector/update-status` to semantic verbs: `/accept/{id}`, `/start/{id}`, `/collect/{id}`, `/complete/{id}` for clarity
- **Dealer Marketplace Gated on Verification** — `require_roles("dealer")` now also enforces `verification_status == approved` for inventory browsing/reservation endpoints
- **InventoryLot.lot_number** — now auto-generated (format: `WIQ-<YYYYMM>-<padded_id>`) by the admin service layer; no longer a required POST body field

### Fixed
- **CORS Middleware Ordering** — `CORSMiddleware` was being added after `include_router()` in `main.py`, causing OPTIONS preflight requests to bypass CORS headers. Fixed by moving all `app.add_middleware()` calls before `app.include_router()`. ([#91](https://github.com/your-org/waste-iq/issues/91))
- **JWT Token Expiry Not Configurable** — token expiry was hardcoded to 30 minutes, ignoring `ACCESS_TOKEN_EXPIRE_MINUTES` env var. Now correctly reads from `settings.access_token_expire_minutes`. ([#84](https://github.com/your-org/waste-iq/issues/84))
- **Duplicate Phone Registration** — a race condition allowed two concurrent registration requests with the same phone number to both succeed. Fixed by catching `IntegrityError` on the `unique` constraint and returning HTTP 400. ([#79](https://github.com/your-org/waste-iq/issues/79))
- **Collector Nearby Endpoint Distance Calculation** — Haversine distance was being calculated in Python on all pending requests. Replaced with a database-side approximation to prevent loading all rows into memory. ([#88](https://github.com/your-org/waste-iq/issues/88))

---

## [0.1.0] — 2026-05-01

### Added
- **Initial Project Setup** — monorepo structure with separate `backend/` and `frontend/` directories, `docker-compose.yml`, and root `pyproject.toml` for linting configuration
- **FastAPI Backend** — FastAPI 0.115 application with Uvicorn, structured using layered architecture (routes → services → repositories → models)
- **PostgreSQL + SQLAlchemy 2.0** — fully typed ORM models with `Mapped[]` annotations; Alembic for schema migrations; SQLite support for local development
- **React 19 Frontend** — Vite + TypeScript + Tailwind CSS + shadcn/ui (Radix UI) component library; Framer Motion for animations; Lucide React for icons
- **User Authentication** — `POST /auth/register`, `POST /auth/login`, `GET /auth/me`; JWT access tokens signed with HS256; bcrypt password hashing via Passlib
- **Role-Based Access Control** — four roles: `citizen`, `collector`, `dealer`, `admin`; FastAPI `Depends` guards enforce role on protected endpoints; admin bootstrapped from environment variable
- **Pickup Request Lifecycle** — full status machine: `pending → accepted → on_the_way → collected → completed/cancelled`; `PickupRequestEvent` audit log records every transition with actor and timestamp
- **Citizen Dashboard** — `GET /pickup-requests/citizen/summary` returns counts by status; `NewPickupPage` with multipart form (waste type, address, GPS coordinates, optional image upload)
- **Collector Dashboard** — available requests list, nearby requests with Haversine distance, accept/start/collect/complete flow, personal summary stats
- **Admin Dashboard** — user list, platform analytics (`total_users`, `total_pickups`, `pickups_by_status`, `total_weight_kg`), dealer management
- **Docker Compose Setup** — `postgres:16-alpine` database service, backend service (builds from `./backend/Dockerfile`), frontend service with Nginx
- **Alembic Migrations** — initial migration creates all tables with proper indexes and constraints; `CMD` in Dockerfile runs `alembic upgrade head` on startup
- **Cloudinary Image Upload** — images uploaded via multipart form; `ImageUploadConfigurationError` and `ImageUploadUnavailableError` custom exceptions with graceful 503/502 responses; upload skipped silently in development if credentials absent
- **GitHub Actions CI** — `backend-ci.yml`: Ruff lint + Black format check + MyPy + Pytest with PostgreSQL service; `frontend-ci.yml`: ESLint + TypeScript check + Vite build
- **Environment Configuration** — Pydantic-settings `Settings` class with full `.env.example` for both backend and frontend; `CORS_ORIGINS` supports comma-separated list parsed at startup

[Unreleased]: https://github.com/your-org/waste-iq/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/your-org/waste-iq/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/your-org/waste-iq/releases/tag/v0.1.0
