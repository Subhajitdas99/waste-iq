# System Architecture — Waste-IQ

> This document describes the high-level and detailed architecture of the Waste-IQ platform, covering the frontend, backend, authentication, data flow, and deployment topology.

---

## Table of Contents

1. [Overview](#1-overview)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Frontend Architecture](#3-frontend-architecture)
4. [Backend Architecture](#4-backend-architecture)
5. [Authentication Flow](#5-authentication-flow)
6. [Pickup Request Lifecycle](#6-pickup-request-lifecycle)
7. [Inventory Marketplace Flow](#7-inventory-marketplace-flow)
8. [API Layer](#8-api-layer)
9. [Database Layer](#9-database-layer)
10. [Deployment Architecture](#10-deployment-architecture)
11. [Security](#11-security)
12. [Future AI Modules](#12-future-ai-modules)

---

## 1. Overview

Waste-IQ is a multi-role, API-driven platform that digitizes the recyclable waste supply chain. It connects four primary stakeholders:

| Actor | Role in the System |
|-------|--------------------|
| **Citizen** | Submits pickup requests for recyclable waste |
| **Collector** | Accepts and fulfills pickup requests in the field |
| **Scrap Dealer** | Creates a business profile, awaits approval, then purchases verified inventory lots through the marketplace |
| **Admin** | Manages the platform, reviews and approves/rejects dealer profiles, and creates inventory |

The system consists of a **React single-page application** communicating with a **FastAPI REST API**, backed by a **PostgreSQL relational database**, with **Cloudinary** for image storage.

---

## 2. High-Level Architecture

```mermaid
flowchart TB
    subgraph Users["👥 Stakeholders"]
        U1[🏘️ Citizen]
        U2[🚛 Collector]
        U3[🏭 Dealer]
        U4[🛡️ Admin]
    end

    subgraph FE["⚛️ Frontend — React SPA"]
        direction TB
        REACT["React 19 + TypeScript\nVite • Tailwind CSS • shadcn/ui"]
        QUERY["TanStack Query\n(Server State)"]
        AXIOS["Axios HTTP Client\n(JWT Bearer Tokens)"]
        CTX["Auth Context\n(React Context API)"]
    end

    subgraph BE["🐍 Backend — FastAPI"]
        direction TB
        ROUTES["API Route Handlers\n(FastAPI Routers)"]
        AUTH_MW["JWT Middleware\n(python-jose)"]
        SVC["Service Layer\n(Business Logic)"]
        REPO["Repository Layer\n(Data Access)"]
        ORM["SQLAlchemy ORM\n(Models)"]
    end

    subgraph STORE["💾 Storage"]
        PG[("🐘 PostgreSQL 16\n(or SQLite for dev)")]
        CDN["☁️ Cloudinary\nImage Storage & CDN"]
    end

    subgraph INFRA["🚀 Infrastructure"]
        RENDER["Render.com\n(Backend + Managed DB)"]
        STATIC["Static Site Host\n(Render / Vercel)"]
        GHA["GitHub Actions\n(CI / CD Pipeline)"]
    end

    Users --> FE
    FE --> BE
    BE --> STORE
    AXIOS -.->|"Authorization: Bearer <token>"| ROUTES
    AUTH_MW -.->|validates token| ROUTES
    ORM --> PG
    SVC -.->|"upload images"| CDN
    GHA -.->|"deploy on push to main"| RENDER
    GHA -.->|"deploy frontend dist"| STATIC
```

---

## 3. Frontend Architecture

### Technology Choices

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Framework | React 19 | Concurrent features, stable ecosystem |
| Language | TypeScript (strict) | Type safety, better DX |
| Build Tool | Vite | Fast HMR, optimized builds |
| Styling | Tailwind CSS + shadcn/ui | Utility-first, accessible components |
| Routing | React Router v6 | File-based, nested routes |
| Server State | TanStack Query v5 | Caching, refetching, mutations |
| HTTP | Axios | Interceptors for JWT injection |
| Forms | React Hook Form + Zod | Performant forms with schema validation |
| Animations | Framer Motion | Smooth transitions |
| Icons | Lucide React | Consistent icon set |

### Directory Structure

```
frontend/src/
├── api/           # Axios instance + typed API functions per domain
├── app/           # Root component, providers, global layout
├── assets/        # Static images and SVGs
├── components/    # Shared, reusable UI components (Button, Card, Badge…)
├── context/       # React Context providers (AuthContext, ThemeContext)
├── hooks/         # Custom React hooks (useAuth, usePickup, useCollector…)
├── layouts/       # Page layout shells (DashboardLayout, AuthLayout)
├── lib/           # Utility functions (cn(), formatDate(), formatCurrency()…)
├── pages/
│   ├── auth/      # Login, Register pages
│   ├── dashboard/ # Role-specific dashboard pages
│   └── public/    # Landing page, 404
├── routes/        # Route definitions with role-based guards
├── styles/        # Global CSS, Tailwind base layer overrides
├── types/         # TypeScript interfaces and type definitions
└── main.tsx       # App entry point
```

### State Management Strategy

```mermaid
flowchart LR
    subgraph Global["Global State"]
        AUTH["AuthContext\n(user, token, login(), logout())"]
    end
    subgraph Server["Server State — TanStack Query"]
        PQ["Pickup Queries\nusePickupRequests()"]
        CQ["Collector Queries\nuseAvailableRequests()"]
        DQ["Dealer Queries\nuseInventoryLots()"]
        AQ["Admin Queries\nuseAnalytics()"]
    end
    subgraph Local["Local / Form State"]
        FORM["React Hook Form\n(controlled inputs)"]
        UI["Component State\n(useState, useReducer)"]
    end
    AUTH --> Server
    Server --> Local
```

### Routing & Role Guards

```mermaid
flowchart TD
    START[Navigate to URL] --> CHECK{Token in\nlocalStorage?}
    CHECK -->|No| LOGIN[Redirect to /login]
    CHECK -->|Yes| ROLE{User Role?}
    ROLE -->|citizen| CDASH[/dashboard/citizen]
    ROLE -->|collector| COLDASH[/dashboard/collector]
    ROLE -->|dealer| DDASH[/dashboard/dealer]
    ROLE -->|admin| ADASH[/dashboard/admin]
    CDASH --> CGUARD{Role matches\nrequired role?}
    CGUARD -->|Yes| PAGE[Render Page]
    CGUARD -->|No| DENIED[403 Forbidden]
```

---

## 4. Backend Architecture

### Layered Architecture

```mermaid
flowchart TB
    CLIENT["HTTP Client\n(Browser / Axios)"]

    subgraph API["API Layer — FastAPI"]
        ROUTER["Router\napp/api/router.py"]
        ROUTES["Route Handlers\napp/api/routes/*.py"]
        DEP["Dependencies\nget_db, get_current_user,\nrequire_roles()"]
    end

    subgraph SVC["Service Layer"]
        AUTH_SVC["AuthService\nauthenticate_user, register_user"]
        PICKUP_SVC["PickupService\ncreate, accept, complete…"]
        INVENTORY_SVC["InventoryService\ncreate_lot, reserve, purchase"]
        DEALER_SVC["DealerProfileService\ncreate, update, submit"]
        APPROVAL_SVC["AdminDealerApprovalService\napprove, reject, review queue"]
        ADMIN_SVC["AdminService\nanalytics, user_mgmt"]
        UPLOAD_SVC["UploadService\nCloudinary integration"]
    end

    subgraph REPO["Repository Layer"]
        USER_REPO["UserRepository"]
        PICKUP_REPO["PickupRepository"]
        INVENTORY_REPO["InventoryRepository"]
        DEALER_REPO["DealerRepository"]
    end

    subgraph MODEL["ORM / Model Layer"]
        MODELS["SQLAlchemy Models\napp/models/*.py"]
    end

    DB[("PostgreSQL / SQLite")]

    CLIENT --> ROUTER --> ROUTES
    ROUTES --> DEP
    ROUTES --> SVC
    SVC --> REPO
    REPO --> MODELS
    MODELS --> DB
    SVC -.->|image upload| UPLOAD_SVC
```

### Module Descriptions

| Module | Path | Responsibility |
|--------|------|----------------|
| `main.py` | `app/main.py` | FastAPI application factory, middleware registration, lifespan |
| `config.py` | `app/core/config.py` | Pydantic-settings `Settings` class; reads `.env` |
| `dependencies.py` | `app/core/dependencies.py` | `get_db`, `get_current_user`, `require_roles()` FastAPI deps |
| `security.py` | `app/core/security.py` | JWT encode/decode, bcrypt hashing |
| `router.py` | `app/api/router.py` | Mounts all sub-routers with prefixes and tags |
| `models/` | `app/models/` | SQLAlchemy ORM model classes |
| `schemas/` | `app/schemas/` | Pydantic v2 request/response schemas |
| `services/` | `app/services/` | Business logic; orchestrates repositories and external services |
| `repositories/` | `app/repositories/` | Raw data access queries; returns ORM objects |
| `db/session.py` | `app/db/session.py` | SQLAlchemy engine + `SessionLocal` factory |
| `routes/analytics.py` | `app/api/routes/analytics.py` | Admin AI analytics endpoints (overview, materials, monthly, collectors, dealers, carbon, insights) |
| `services/analytics.py` | `app/services/analytics.py` | Analytics aggregations (SQLAlchemy) and deterministic rule-based insight generation |
| `schemas/analytics.py` | `app/schemas/analytics.py` | Typed Pydantic v2 response models for every analytics endpoint |
| `services/dealer_profiles.py` | `app/services/dealer_profiles.py` | Dealer profile lifecycle: create, update, submit, approval timeline |
| `services/dealer_approval.py` | `app/services/dealer_approval.py` | Approval transition validation, `is_dealer_approved` guard, admin review/approve/reject |
| `repositories/dealer_profiles.py` | `app/repositories/dealer_profiles.py` | Dealer profile & event data access, paginated listing with search/sort/filter |

---

## 5. Authentication Flow

```mermaid
sequenceDiagram
    actor U as User (Browser)
    participant FE as React Frontend
    participant BE as FastAPI Backend
    participant DB as PostgreSQL

    U->>FE: Fill login form (email + password)
    FE->>BE: POST /auth/login {email, password}
    BE->>DB: SELECT user WHERE email = ?
    DB-->>BE: User record
    BE->>BE: bcrypt.verify(password, password_hash)
    alt Invalid credentials
        BE-->>FE: 401 Unauthorized
        FE-->>U: Show error message
    else Valid credentials
        BE->>BE: jose.jwt.encode({sub: user_id, role, exp})
        BE-->>FE: 200 {access_token, token_type, user}
        FE->>FE: Store token in localStorage
        FE->>FE: Set AuthContext (user, token)
        FE-->>U: Redirect to role dashboard
    end

    Note over FE,BE: Subsequent authenticated requests

    U->>FE: Perform protected action
    FE->>FE: Read token from localStorage
    FE->>BE: GET /pickup-requests\nAuthorization: Bearer <token>
    BE->>BE: Extract + validate JWT\n(get_current_user dependency)
    alt Token expired or invalid
        BE-->>FE: 401 Unauthorized
        FE->>FE: Clear AuthContext + localStorage
        FE-->>U: Redirect to /login
    else Token valid
        BE->>DB: Query data for user
        DB-->>BE: Result
        BE-->>FE: 200 Response data
        FE-->>U: Render data
    end
```

---

## 6. Pickup Request Lifecycle

```mermaid
stateDiagram-v2
    direction LR
    [*] --> pending : Citizen submits\nPOST /pickup-requests

    pending --> accepted : Collector accepts\nPOST /collector/accept/{id}
    pending --> cancelled : Citizen cancels\nPOST /pickup-requests/{id}/cancel

    accepted --> on_the_way : Collector starts\nPOST /collector/start/{id}

    on_the_way --> collected : Collector marks collected\nPOST /collector/collect/{id}

    collected --> completed : Collector records weight\nPOST /collector/complete/{id}\n(weight_kg required)

    completed --> [*] : Admin creates InventoryLot\nfrom completed pickup
    cancelled --> [*]

    note right of completed
        InventoryLot is created\nby admin after completion.\nOne-to-one relationship.
    end note
```

Each state transition is recorded as a `PickupRequestEvent` with the actor's user ID and timestamp.

---

## 7. Inventory Marketplace Flow

### Dealer Approval Workflow

```mermaid
stateDiagram-v2
    [*] --> draft: Dealer creates profile
    draft --> submitted: Dealer submits for review
    submitted --> approved: Admin approves
    submitted --> rejected: Admin rejects (with reason)
    approved --> draft: Dealer edits profile
    rejected --> draft: Dealer edits profile
    rejected --> submitted: Dealer resubmits
    approved --> [*]: Marketplace access granted
```

Every transition is persisted in `dealer_profile_events` (actor, status, note,
timestamp) and surfaced as an approval timeline to the dealer and admins.
Inventory browsing/reservation endpoints require `approval_status = approved`
(`403` with an explanatory detail otherwise).

```mermaid
sequenceDiagram
    actor A as Admin
    actor D as Dealer
    participant BE as FastAPI Backend
    participant DB as PostgreSQL

    Note over D,DB: Phase 1 — Lot Creation
    A->>BE: POST /admin/inventory/lots\n{pickup_request_id, material_category_id, weight_kg, quality_grade}
    BE->>DB: Create InventoryLot (status=available, visibility=visible)
    BE->>DB: Record InventoryLotEvent (type=created)
    BE-->>A: InventoryLot created (lot_number, total_listed_amount)

    Note over D,DB: Phase 2 — Dealer Browse & Reserve
    D->>BE: GET /dealer/inventory-lots?city=Mumbai&material_category_id=3
    BE->>DB: SELECT lots WHERE status=available AND visibility=visible
    DB-->>BE: List of available lots
    BE-->>D: [{lot_number, weight_kg, unit_price, source_city, quality_grade}]

    D->>BE: POST /dealer/inventory/lots/{lot_id}/reserve
    BE->>DB: UPDATE lot SET status=reserved,\nreserved_by_dealer_id=?,\nreservation_expires_at=NOW()+24h
    BE->>DB: Record InventoryLotEvent (type=reserved)
    BE-->>D: Lot reserved (expires_at)

    Note over D,DB: Phase 3 — Purchase Confirmation
    D->>BE: POST /dealer/inventory/lots/{lot_id}/purchase
    BE->>DB: CHECK reservation_expires_at > NOW()
    alt Reservation expired
        BE-->>D: 409 Conflict — reservation expired
    else Reservation valid
        BE->>DB: UPDATE lot SET status=sold
        BE->>DB: Record InventoryLotEvent (type=status_changed, new=sold)
        BE-->>D: Purchase confirmed
    end
```

---

## 8. API Layer

The API follows RESTful conventions with JSON request/response bodies (except multipart/form-data for file uploads).

### Router Structure

| Prefix | Tags | Auth Required | Description |
|--------|------|---------------|-------------|
| `/auth` | Authentication | No (register/login) | User registration, login, profile |
| `/pickup-requests` | Pickup Requests | Yes | Full pickup lifecycle |
| `/collector` | Collector | Yes (collector role) | Collector-specific operations |
| `/dealer` | Dealer | Yes (dealer role) | Profile management, submit for approval, approval timeline |
| `/dealer` | Dealer Inventory | Yes (approved dealer) | Marketplace browse, reserve, purchase |
| `/admin` | Admin | Yes (admin role) | Users, analytics, dealer review queue (approve/reject) |
| `/admin/analytics` | Admin Analytics | Yes (admin role) | Overview KPIs, material distribution, monthly trend, collector/dealer performance, carbon savings, rule-based insights |
| `/admin` | Admin Inventory | Yes (admin role) | Lot management, pricing, categories |
| `/health` | health | No | Application health check |

### Dependency Injection Chain

```mermaid
flowchart LR
    REQ[HTTP Request] --> get_db
    get_db --> Session[(DB Session)]
    Session --> get_current_user
    get_current_user --> require_roles
    require_roles --> RouteHandler[Route Handler]
    Session --> RouteHandler
    get_current_user --> RouteHandler
```

---

## 9. Database Layer

### Technology Stack

| Component | Technology |
|-----------|-----------|
| Production DB | PostgreSQL 16 |
| Local Dev DB | SQLite (default) |
| ORM | SQLAlchemy 2.0 (typed `Mapped[]` style) |
| Migrations | Alembic 1.16 |

### Key Design Decisions

- **Schema migrations** are exclusively managed by Alembic — `Base.metadata.create_all()` is never called in application code to prevent migration drift
- **All ORM models** use `from __future__ import annotations` and `Mapped[type]` for fully typed column declarations
- **Cascade deletes** are configured at the ORM level (`cascade="all, delete-orphan"`) matching foreign key `ondelete` actions
- **Audit events** for both pickup requests and inventory lots are stored in separate event tables for full audit trail without modifying the primary record
- **Soft archiving** for inventory lots uses `archived_at` + `archive_reason` fields rather than hard deletion

---

## 10. Deployment Architecture

```mermaid
flowchart TB
    subgraph DEV["🖥️ Developer Workstation"]
        CODE["Source Code\n(git)"]
        DOCKER["docker compose\n(local full-stack)"]
    end

    subgraph GH["🐙 GitHub"]
        REPO["Repository\nmain / develop"]
        GHA["GitHub Actions\nbackend-ci.yml\nfrontend-ci.yml"]
    end

    subgraph PROD["🚀 Production — Render.com"]
        BACK["Web Service\nFastAPI + Uvicorn"]
        DBPROD[("Managed PostgreSQL\nRender DB")]
        FRONT["Static Site\nReact (dist/)"]
    end

    CDN["☁️ Cloudinary\nImage CDN"]

    CODE -->|git push| REPO
    REPO --> GHA
    GHA -->|lint + test pass| PROD
    BACK --> DBPROD
    BACK -.->|uploads| CDN
    FRONT -.->|API calls| BACK
```

### Environment Summary

| Environment | Backend | Frontend | Database |
|-------------|---------|----------|----------|
| Local | Uvicorn (--reload) | Vite dev server | SQLite |
| Docker | Uvicorn (Docker) | Nginx (Docker) | PostgreSQL 16 (Docker) |
| CI/Testing | Pytest (GitHub Actions) | npm build | PostgreSQL 16 (Actions service) |
| Production | Uvicorn (Render Web Service) | Static files (Render/CDN) | Render Managed PostgreSQL |

---

## 11. Security

| Security Control | Implementation | Details |
|-----------------|----------------|---------|
| **Authentication** | JWT (HS256) | Signed tokens; `ACCESS_TOKEN_EXPIRE_MINUTES` configurable |
| **Password Storage** | bcrypt (Passlib) | Cost factor 12; salted hashes |
| **Authorization** | RBAC via `require_roles()` | FastAPI dependency; checked per-endpoint |
| **Input Validation** | Pydantic v2 | All request bodies validated before handler executes |
| **CORS** | FastAPI CORSMiddleware | Allowlist of origins from `CORS_ORIGINS` env var |
| **HTTPS** | Enforced by Render.com | TLS termination at load balancer |
| **Secrets Management** | Environment variables | No secrets in source code; `.env` excluded via `.gitignore` |
| **Image Upload** | Cloudinary signed uploads | Backend handles credentials; URL stored in DB |
| **SQL Injection** | SQLAlchemy ORM + parameterized queries | No raw string interpolation in SQL |
| **Sensitive Logs** | Passwords never logged | FastAPI access logs exclude request bodies |

---

## 12. Future AI Modules

### Current AI Foundation

The database schema already has AI-ready fields:

| Model | Field | Purpose |
|-------|-------|---------|
| `PickupRequest` | `image_url` | Cloudinary URL of the uploaded waste image |
| `PickupRequest` | `category` | Detected material category (null until AI runs) |
| `PickupRequest` | `confidence` | Classification confidence score (0.0–1.0) |

### AI Analytics Dashboard (Implemented — Rule-Based)

The **AI Analytics Dashboard** (`/admin/analytics/*`) delivers dashboard insights without an LLM. All insights are deterministic, server-side rules computed from live aggregates in `app/services/analytics.py`:

| Insight | Rule |
|---------|------|
| Most recycled material | Highest material bucket count from completed pickups |
| Highest performing collector | Most completed jobs (tie-break: completion rate) |
| Highest performing dealer | Most total weight across sold lots |
| Estimated carbon savings | ~0.42 kg CO₂e saved per kg recycled; ~21 kg CO₂ per tree |
| Pickup completion trend | 6-month completion delta vs. the previous 6 months |

### Planned AI Integration

```mermaid
flowchart LR
    IMG["Waste Image\n(Cloudinary URL)"]
    CLASSIFY["AI Classification\nService\n(FastAPI microservice\nor Cloudinary AI)"]
    UPDATE["Update PickupRequest\n{category, confidence}"]
    ADMIN["Admin creates\nInventoryLot\n(pre-filled category)"]

    IMG -->|async job| CLASSIFY
    CLASSIFY --> UPDATE
    UPDATE --> ADMIN
```

| Module | Status | Technology (Planned) |
|--------|--------|----------------------|
| Waste Image Classification | 🔜 Planned | Fine-tuned ResNet / Cloudinary AI |
| Collector Route Optimization | 🔜 Planned | Google OR-Tools / custom Haversine clustering |
| Pricing Demand Forecasting | 💡 Future | Time-series model on InventoryLot transaction data |
| Fraud Detection | 💡 Future | Anomaly detection on pickup patterns |
