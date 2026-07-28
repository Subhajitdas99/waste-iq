# Business Requirements — Waste-IQ

> This document defines the business context, user needs, functional requirements, and success metrics for the Waste-IQ platform. It serves as the authoritative reference for product decisions and sprint planning.

---

## Table of Contents

1. [Vision](#1-vision)
2. [Mission](#2-mission)
3. [Problem Statement](#3-problem-statement)
4. [User Personas](#4-user-personas)
5. [Functional Requirements](#5-functional-requirements)
6. [Non-Functional Requirements](#6-non-functional-requirements)
7. [Business Rules](#7-business-rules)
8. [Success Metrics](#8-success-metrics)
9. [MVP Scope](#9-mvp-scope)
10. [Future Roadmap](#10-future-roadmap)

---

## 1. Vision

> **To become India's leading digital infrastructure for recyclable waste management — creating a transparent, efficient, and inclusive circular economy that connects every link of the waste supply chain.**

Waste-IQ envisions a future where no recyclable material goes to a landfill due to inefficiency or lack of access. By digitizing the informal waste sector, the platform empowers citizens to act, gives collectors modern tools to earn more, and provides dealers reliable access to quality material supply — all while giving municipalities and administrators the data they need to measure and improve environmental outcomes.

---

## 2. Mission

> **Digitize and optimize the recyclable waste supply chain through technology, making waste collection accessible, transparent, and economically rewarding for all stakeholders.**

Waste-IQ achieves this mission by:

- Replacing informal, ad-hoc collection with a structured, trackable digital workflow
- Creating market transparency through verified inventory listings and published pricing
- Empowering field collectors with mobile-first tools that reduce idle time
- Providing scrap dealers with a reliable, curated supply of verified recyclable material
- Giving administrators the real-time analytics needed to improve urban waste management

---

## 3. Problem Statement

India generates over **62 million tonnes** of solid waste annually, of which a significant portion is recyclable but ends up in landfills due to a fragmented, informal collection chain. The core problems are:

| # | Problem | Impact |
|---|---------|--------|
| 1 | **No digital tracking** of pickup requests — citizens have no visibility into status | Citizens lose trust; pickups are missed |
| 2 | **Collectors work ad-hoc** with no tools to manage jobs, routes, or earnings | High idle time, poor earnings, no records |
| 3 | **Scrap dealers lack a structured marketplace** to source materials | Dealers rely on informal relationships; inconsistent supply |
| 4 | **Pricing opacity** — citizens don't know the market value of their recyclables | Exploitation by informal middlemen |
| 5 | **No data for municipalities** — waste management decisions are made without data | Inefficient resource allocation |
| 6 | **No accountability layer** — no way to verify that waste was actually collected and processed | Greenwashing risk; no audit trail |
| 7 | **Environmental loss** — recyclables going to landfill because the collection chain breaks down | Increased carbon footprint, resource waste |

---

## 4. User Personas

### Persona 1 — Citizen (Waste Generator)

| Attribute | Detail |
|-----------|--------|
| **Name** | Riya Sharma |
| **Age** | 32 |
| **Occupation** | Software Engineer |
| **Location** | Andheri West, Mumbai |
| **Tech Comfort** | High — uses apps daily |
| **Goals** | Schedule hassle-free pickup · Know her recyclables are properly handled · Track status without calling anyone |
| **Pain Points** | Has to call the kabadiwala and hope they show up · No confirmation or receipt · Doesn't know if waste was recycled or dumped · No predictable pricing |
| **Motivation** | Environmental responsibility + convenience |

---

### Persona 2 — Collector (Field Worker)

| Attribute | Detail |
|-----------|--------|
| **Name** | Mohan Kumar |
| **Age** | 27 |
| **Occupation** | Independent waste collector |
| **Location** | Covers Bandra and Khar, Mumbai |
| **Tech Comfort** | Medium — uses WhatsApp and basic apps |
| **Goals** | Maximize daily pickups · Know exactly where to go and when · Get paid fairly for the weight collected |
| **Pain Points** | Wastes time going to locations where no waste is ready · No formal records of his work · Doesn't know which areas have demand · No digital proof of pickup |
| **Motivation** | Higher earnings, professional recognition |

---

### Persona 3 — Scrap Dealer (Recycling Business)

| Attribute | Detail |
|-----------|--------|
| **Name** | Priya Menon |
| **Age** | 41 |
| **Occupation** | Owner, GreenCycle Scrap Pvt. Ltd. |
| **Location** | Thane, Mumbai |
| **Tech Comfort** | Medium — uses accounting software |
| **Goals** | Reliable, consistent supply of quality material · Reduce time spent sourcing from multiple informal channels · Know material quality and weight before buying |
| **Pain Points** | Inconsistent supply from informal collectors · No way to verify material quality in advance · Middlemen inflate prices · High transaction costs in informal markets |
| **Motivation** | Profitability, supply chain reliability |

---

### Persona 4 — Municipal Officer (Government Stakeholder)

| Attribute | Detail |
|-----------|--------|
| **Name** | Arvind Nair |
| **Age** | 48 |
| **Occupation** | Deputy Commissioner, Solid Waste Management, MCGM |
| **Location** | Mumbai |
| **Tech Comfort** | Low-medium — uses dashboards and reports |
| **Goals** | Reduce recyclable waste going to landfill · Demonstrate measurable ESG outcomes · Monitor collector activity in their jurisdiction |
| **Pain Points** | No real-time data on what's being collected and from where · Cannot measure the impact of waste management programs · Manual, paper-based reporting |
| **Motivation** | Policy compliance, environmental targets, public accountability |

---

### Persona 5 — Platform Administrator

| Attribute | Detail |
|-----------|--------|
| **Name** | Platform Admin (Internal Role) |
| **Age** | — |
| **Occupation** | Waste-IQ Operations Team |
| **Tech Comfort** | High |
| **Goals** | Keep platform healthy · Verify dealer legitimacy · Ensure inventory quality · Monitor for fraud or abuse |
| **Pain Points** | Manual verification process without tooling · No analytics to spot anomalies |
| **Motivation** | Platform integrity, business growth |

---

## 5. Functional Requirements

### 5.1 Citizen Requirements

| ID | Requirement | Priority | User Story |
|----|-------------|----------|-----------|
| FR-CIT-001 | Register a new account with name, email, phone, and password | **High** | As a citizen, I want to create an account so I can access the platform |
| FR-CIT-002 | Log in with email and password | **High** | As a citizen, I want to log in securely to access my dashboard |
| FR-CIT-003 | Submit a pickup request with waste type, address, GPS coordinates, and optional photo | **High** | As a citizen, I want to schedule a pickup so a collector can come to my location |
| FR-CIT-004 | View the status of my active pickup requests in real-time | **High** | As a citizen, I want to track my request so I know when to expect the collector |
| FR-CIT-005 | View a history of all my past pickup requests | **High** | As a citizen, I want to see my history so I can track my recycling contributions |
| FR-CIT-006 | Cancel a pickup request that is still in `pending` status | **High** | As a citizen, I want to cancel a request if my plans change |
| FR-CIT-007 | View a personal dashboard with aggregate metrics (total requests, completions) | **Medium** | As a citizen, I want to see my impact stats so I feel motivated to recycle more |
| FR-CIT-008 | Update my profile information | **Medium** | As a citizen, I want to update my contact details when they change |

---

### 5.2 Collector Requirements

| ID | Requirement | Priority | User Story |
|----|-------------|----------|-----------|
| FR-COL-001 | Register as a collector and log in | **High** | As a collector, I want to join the platform to access pickup jobs |
| FR-COL-002 | View all available (pending) pickup requests on the platform | **High** | As a collector, I want to see all open jobs so I can choose which to accept |
| FR-COL-003 | View nearby pickup requests filtered by my GPS location and a configurable radius | **High** | As a collector, I want to see requests close to me so I can optimize my route |
| FR-COL-004 | Accept a pickup request, exclusively assigning it to myself | **High** | As a collector, I want to claim a request before another collector takes it |
| FR-COL-005 | Update request status to "on the way" when I depart for the pickup | **High** | As a collector, I want to signal I'm en route so the citizen knows to expect me |
| FR-COL-006 | Mark a request as "collected" upon physical pickup | **High** | As a collector, I want to record that I've collected the waste |
| FR-COL-007 | Complete a pickup by recording the waste weight in kilograms | **High** | As a collector, I want to log the weight so earnings can be calculated |
| FR-COL-008 | View a personal dashboard with my performance stats and completed pickups | **Medium** | As a collector, I want to track my earnings and performance |

---

### 5.3 Dealer Requirements

| ID | Requirement | Priority | User Story |
|----|-------------|----------|-----------|
| FR-DEA-001 | Register a business profile with GST, license, and accepted material types | **High** | As a dealer, I want to register my business to access the inventory marketplace |
| FR-DEA-002 | View my verification status (pending / approved / rejected) | **High** | As a dealer, I want to know if I'm approved to use the marketplace |
| FR-DEA-003 | Browse available inventory lots on the marketplace | **High** | As a dealer, I want to see what material is available so I can plan purchases |
| FR-DEA-004 | Filter inventory lots by city, material category, quality grade, and weight range | **High** | As a dealer, I want to filter lots to find material relevant to my business |
| FR-DEA-005 | Reserve an inventory lot for 24 hours | **High** | As a dealer, I want to place a hold on a lot while I arrange payment/logistics |
| FR-DEA-006 | Confirm purchase of a reserved lot | **High** | As a dealer, I want to confirm my purchase to secure the material |
| FR-DEA-007 | View my own profile and update business details | **Medium** | As a dealer, I want to keep my business information current |

---

### 5.4 Admin Requirements

| ID | Requirement | Priority | User Story |
|----|-------------|----------|-----------|
| FR-ADM-001 | View platform-wide analytics (users, pickups, weight, revenue) | **High** | As an admin, I want to see KPIs so I can monitor platform health |
| FR-ADM-002 | View and manage all registered users | **High** | As an admin, I want a full user list to manage access and investigate issues |
| FR-ADM-003 | Approve or reject dealer profiles | **High** | As an admin, I want to vet dealers before granting marketplace access |
| FR-ADM-004 | Create inventory lots from completed pickup requests | **High** | As an admin, I want to list material on the marketplace once a pickup is done |
| FR-ADM-005 | Manage material categories (create, update, activate/deactivate) | **High** | As an admin, I want to define the material types the platform supports |
| FR-ADM-006 | Create and manage pricing rules by city and material category | **High** | As an admin, I want to set fair market prices for each material type and city |
| FR-ADM-007 | Archive or restore inventory lots | **Medium** | As an admin, I want to remove substandard lots from the marketplace |
| FR-ADM-008 | Toggle visibility of inventory lots | **Medium** | As an admin, I want to hide a lot temporarily without archiving it |

---

## 6. Non-Functional Requirements

| ID | Category | Requirement | Target / Measure |
|----|----------|-------------|-----------------|
| NFR-001 | **Performance** | API response time (p95) under normal load | < 500ms |
| NFR-002 | **Performance** | Frontend initial page load (LCP) | < 3 seconds on 4G |
| NFR-003 | **Performance** | Frontend Time to Interactive (TTI) | < 5 seconds on 4G |
| NFR-004 | **Scalability** | Concurrent active users supported | 10,000 (Phase 1 target) |
| NFR-005 | **Availability** | Uptime SLA | ≥ 99.5% monthly |
| NFR-006 | **Security** | All API traffic encrypted | HTTPS enforced, TLS 1.2+ |
| NFR-007 | **Security** | Password storage | bcrypt with cost factor ≥ 12 |
| NFR-008 | **Security** | Authentication | JWT; tokens expire in 24 hours |
| NFR-009 | **Security** | No secrets in source code | All secrets via environment variables |
| NFR-010 | **Maintainability** | Backend test coverage | ≥ 80% on `app/` module |
| NFR-011 | **Maintainability** | Linting and type-checking pass | Ruff + Black + MyPy (backend); ESLint + tsc (frontend) |
| NFR-012 | **Accessibility** | WCAG compliance | 2.1 Level AA |
| NFR-013 | **Compatibility** | Supported browsers | Chrome 120+, Firefox 120+, Safari 17+, Edge 120+ |
| NFR-014 | **Compatibility** | Supported screen sizes | 360px wide (minimum) to 2560px wide |
| NFR-015 | **Observability** | Health check endpoint | `GET /health` returns 200 with app metadata |
| NFR-016 | **Data Integrity** | Database migrations managed exclusively by Alembic | No manual schema changes |
| NFR-017 | **Auditability** | All state changes on pickup requests and inventory lots recorded | `*_events` tables with actor attribution |

---

## 7. Business Rules

The following rules are hard constraints that govern platform behaviour. Any code or feature that violates these rules must be treated as a bug.

| # | Rule | Enforced In |
|---|------|------------|
| BR-001 | Only users with `role = citizen` can create pickup requests | API route guard |
| BR-002 | Only users with `role = collector` can accept pickup requests | API route guard |
| BR-003 | A pickup request can only be accepted by **one** collector (unique constraint on `collector_assignments.request_id`) | DB constraint + service layer |
| BR-004 | Once a pickup request is accepted, it cannot be cancelled by the citizen | Service layer validation |
| BR-005 | A collector must provide `weight_kg > 0` to complete a pickup | Pydantic schema validation |
| BR-006 | Completing a pickup (status → completed) is a prerequisite for creating an InventoryLot | Service layer validation |
| BR-007 | There is exactly one InventoryLot per completed PickupRequest (unique FK + constraint) | DB constraint |
| BR-008 | Only users with `role = dealer` AND `verification_status = approved` can browse, reserve, or purchase inventory lots | API dependency guard |
| BR-009 | Inventory lot reservations expire exactly 24 hours after `reserved_at` | Service layer + `reservation_expires_at` field |
| BR-010 | Only the dealer who holds an active, unexpired reservation may confirm a purchase | Service layer validation |
| BR-011 | Pricing rules are scoped to a specific `(material_category_id, city)` combination | PricingRule model |
| BR-012 | The `total_listed_amount` on an InventoryLot is computed as `weight_kg × unit_price_per_kg_snapshot` and **snapshotted** at creation — it does not change if the pricing rule changes | Service layer computation |
| BR-013 | Only users with `role = admin` can create inventory lots, manage categories, set pricing rules, and approve/reject dealers | API route guard |
| BR-014 | The initial admin account is bootstrapped from environment variables at application startup | Bootstrap service |
| BR-015 | `image_url` may be null if Cloudinary is not configured or if no image is uploaded | Service layer + nullable schema field |

---

## 8. Success Metrics

| Metric | Baseline | 3-Month Target | 12-Month Target | Measurement |
|--------|----------|----------------|-----------------|-------------|
| **Monthly Active Users** | 0 | 1,000 | 10,000 | Platform analytics |
| **Pickup Completion Rate** | — | > 75% | > 85% | `completed / total` |
| **Average Request Response Time** | — | < 4 hours | < 2 hours | `accepted_at - created_at` |
| **Total Weight Collected (kg/month)** | 0 | 5,000 kg | 50,000 kg | Sum of `weight_kg` |
| **Registered Dealers** | 0 | 25 | 200 | User count by role |
| **Dealer Approval Rate** | — | > 70% | > 80% | `approved / total` |
| **Inventory Lot Purchase Rate** | — | > 50% | > 70% | `sold / created` |
| **Platform Uptime** | — | ≥ 99.5% | ≥ 99.9% | Uptime monitoring |
| **API p95 Latency** | — | < 500ms | < 300ms | Render metrics |
| **User Satisfaction (NPS)** | — | > 30 | > 50 | In-app survey |

---

## 9. MVP Scope

The MVP (Minimum Viable Product) delivers the complete core pickup lifecycle and inventory marketplace.

### ✅ In Scope (MVP)

| Feature Area | Included |
|---|---|
| User registration & login (all 4 roles) | ✅ |
| JWT authentication with RBAC | ✅ |
| Citizen: create, view, cancel pickup requests | ✅ |
| Citizen: upload waste image to Cloudinary | ✅ |
| Collector: available, nearby, assigned request lists | ✅ |
| Collector: full pickup lifecycle (accept → start → collect → complete + weight) | ✅ |
| Dealer: business profile registration and verification workflow | ✅ |
| Admin: user management and analytics dashboard | ✅ |
| Admin: dealer verification (approve / reject) | ✅ |
| Admin: inventory lot creation and management | ✅ |
| Admin: material categories and pricing rules | ✅ |
| Dealer: inventory marketplace browse, reserve, purchase | ✅ |
| Inventory lot audit trail (events) | ✅ |
| Docker Compose for local development | ✅ |
| GitHub Actions CI for backend and frontend | ✅ |
| Production deployment on Render.com | ✅ |
| Full documentation suite | ✅ |

### ❌ Out of Scope (MVP — Planned for Future)

| Feature | Reason Deferred |
|---------|----------------|
| Push notifications (browser / mobile) | Requires additional infrastructure (WebSocket or FCM) |
| Mobile application (iOS / Android) | Post-MVP, after web platform is validated |
| AI waste classification (auto-populate category + confidence) | Model training and inference pipeline not yet built |
| Municipality-scoped analytics and reporting | Requires municipality user role |
| Collector route optimization | Complex geospatial feature |
| Citizen reward points system | Requires payments/credits integration |
| In-app messaging | Requires real-time infrastructure |
| Bulk import / export | Admin convenience feature |
| Multi-language support | Localization effort deferred |

---

## 10. Future Roadmap

| Phase | Name | Key Features | Timeline |
|-------|------|-------------|----------|
| **Phase 2** | Enhanced Operations | Push notifications (status changes), Enhanced admin analytics with charts, Municipality user role + city-level dashboard, Collector route suggestions, Export to CSV/PDF | Q3 2026 |
| **Phase 3** | AI & Rewards | AI waste image classification (auto-fill category + confidence), Citizen rewards/points system (earn per kg), Gamification elements (badges, leaderboards), Automated pricing recommendations from market data | Q4 2026 |
| **Phase 4** | Mobile & Scale | React Native mobile app (iOS + Android), Real-time status push notifications, Offline mode for collectors, Bulk operations in admin panel, API rate limiting and advanced security | Q1 2027 |
| **Phase 5** | Marketplace Expansion | B2B bulk material contracts, Secondary marketplace (dealer-to-dealer transfers), Third-party API for municipality integrations, Carbon credit tracking and reporting, Multi-city pricing automation | Q2–Q3 2027 |
| **Phase 6** | Intelligence Platform | Demand forecasting for dealers, Predictive route optimization for collectors, Fraud detection system, Automated compliance reporting for municipalities, ESG dashboard for corporate clients | Q4 2027 |
