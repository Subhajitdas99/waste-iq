# Waste-IQ

Platform digitizing the recyclable-waste supply chain â€” connecting citizens, collectors, and scrap dealers through a transparent, role-based marketplace with verifiable inventory tracking.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js-20+-brightgreen?logo=node.js)](https://nodejs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61dafb?logo=react)](https://react.dev)
[![Coverage](https://img.shields.io/badge/coverage-80%25+-brightgreen)](https://github.com/Subhajitdas99/waste-iq/actions)
[![CI](https://github.com/Subhajitdas99/waste-iq/actions/workflows/pr-gate.yml/badge.svg)](https://github.com/Subhajitdas99/waste-iq/actions)

> **Note:** This repository also includes a standalone **AI Engineering Agent** (`/agent/`) â€” a GitHub App-based automation service. See its [README](agent/README.md) for details.

---

## Table of Contents

- [Overview](#overview)
- [User Roles](#user-roles)
- [End-to-End Workflow](#end-to-end-workflow)
- [Core Features](#core-features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Quick Start (Docker)](#quick-start-docker)
- [Local Development](#local-development)
- [Environment Variables](#environment-variables)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [CI/CD](#cicd)
- [Screenshots](#screenshots)
- [Contributing](#contributing)
- [Changelog](#changelog)
- [License](#license)

---

## Overview

Waste-IQ is a full-stack application that digitizes the recyclable-waste supply chain. Citizens submit pickup requests with location and photo data; collectors accept and fulfill requests, recording verified weights; admins convert completed pickups into tracked inventory lots; and approved scrap dealers browse, reserve, and purchase those lots through a verified marketplace.

Every state transition â€” from pickup request to inventory sale â€” is recorded with actor attribution and timestamping for full auditability.

---

## User Roles

| Role | Description |
|------|-------------|
| **Citizen** | Submits pickup requests, tracks status, confirms weight, cancels pending requests |
| **Collector** | Accepts assignments, navigates to pickup locations, records collected weight, completes pickups |
| **Dealer / Recycler** | Registers a business profile, browses approved inventory, reserves and purchases lots |
| **Administrator** | Manages users, approves/rejects dealer profiles, creates inventory lots, views platform analytics |

All endpoints are protected by JWT-based authentication and role-based access control. Dealer inventory and collector workflows additionally require **email-verified** accounts.

---

## End-to-End Workflow

```
Citizen                    Collector                    Admin / System              Dealer / Recycler
  â”‚                          â”‚                              â”‚                          â”‚
  â”‚  Submit pickup request   â”‚                              â”‚                          â”‚
  â”‚  (waste type, address,   â”‚                              â”‚                          â”‚
  â”‚   GPS coordinates, photo)â”‚                              â”‚                          â”‚
  â”‚  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–ºâ”‚                              â”‚                          â”‚
  â”‚                          â”‚                              â”‚                          â”‚
  â”‚                          â”‚  Accept assignment           â”‚                          â”‚
  â”‚                          â”‚  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–ºâ”‚                          â”‚
  â”‚                          â”‚                              â”‚                          â”‚
  â”‚                          â”‚  Start collection            â”‚                          â”‚
  â”‚                          â”‚  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–ºâ”‚                          â”‚
  â”‚                          â”‚                              â”‚                          â”‚
  â”‚                          â”‚  Collect waste               â”‚                          â”‚
  â”‚                          â”‚  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–ºâ”‚                          â”‚
  â”‚                          â”‚                              â”‚                          â”‚
  â”‚                          â”‚  Record weight               â”‚                          â”‚
  â”‚                          â”‚  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–ºâ”‚                          â”‚
  â”‚                          â”‚                              â”‚                          â”‚
  â”‚                          â”‚  Complete pickup             â”‚                          â”‚
  â”‚                          â”‚  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–ºâ”‚                          â”‚
  â”‚                          â”‚                              â”‚                          â”‚
  â”‚                          â”‚                              â”‚  Create InventoryLot    â”‚
  â”‚                          â”‚                              â”‚  (from completed pickup)â”‚
  â”‚                          â”‚                              â”‚  â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–ºâ”‚
  â”‚                          â”‚                              â”‚                          â”‚
  â”‚                          â”‚                              â”‚                          â”‚  Browse marketplace
  â”‚                          â”‚                              â”‚                          â”‚  Reserve lot (24h)
  â”‚                          â”‚                              â”‚                          â”‚  Purchase â†’ MarketplaceOrder
  â”‚                          â”‚                              â”‚                          â”‚  â”€â”€â”€â”€â”€â”€â”€â”€â—„â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
```

**Detailed steps:**

1. **Citizen** submits a pickup request via a multipart form (waste type, address, GPS coordinates, optional photo upload). The request enters the `pending` state.
2. **Collector** browses available requests or uses the live map interface, accepts an assignment (â†’ `accepted`), starts transit (â†’ `on_the_way`), marks as collected (â†’ `collected`), and records the verified weight (â†’ `completed`).
3. **System** emits lifecycle notifications throughout (to citizen and collector).
4. **Admin** creates an `InventoryLot` from a completed pickup â€” one-to-one relationship, with pricing snapshot from active pricing rules.
5. **Dealer** (approved only) browses the inventory marketplace, filters lots, reserves a lot (24-hour hold with auto-expiry), and completes a purchase, which creates a `MarketplaceOrder` and a `MarketplaceTransaction` ledger entry.

---

## Core Features

### Authentication & Account Security

- **JWT-based authentication** â€” short-lived access tokens (HS256) + opaque, rotated refresh tokens stored as SHA-256 digests
- **Email verification** â€” signed one-time verification links (`POST /auth/verify-email`, `POST /auth/resend-verification`); provider-based email service (`console` for development, `SMTP` for production) with background-task delivery
- **Password reset** â€” enumeration-safe forgot/reset flow with signed short-lived JWTs (`POST /auth/forgot-password`, `POST /auth/reset-password`)
- **Password change** â€” authenticated endpoint that revokes all refresh sessions (`POST /auth/change-password`)
- **Account lockout** â€” per-account lockout after configurable failed-attempt threshold with cooldown period
- **Rate limiting** â€” per-IP limits on registration, login, forgot-password, and resend-verification; per-account limits on login attempts
- **Login history** â€” paginated audit trail of login attempts (`GET /auth/login-history` for users, `GET /admin/login-history` for admins)
- **Session management** â€” logout revokes individual refresh tokens; logout-all revokes every session

### Citizen Pickup Management

- Submit pickup requests with waste type, address, GPS coordinates, optional image upload, and preferred collection time
- Real-time status tracking through the pickup lifecycle (`pending â†’ accepted â†’ on_the_way â†’ collected â†’ completed`)
- Cancel pending requests (with automated image cleanup on cancellation)
- Personal dashboard with pickup summaries and metrics
- Weight verification â€” citizens can confirm or dispute recorded weights (`POST /pickup-requests/{id}/weight/confirm`, `POST /pickup-requests/{id}/weight/dispute`)

### Collector Operations

- Dashboard with assigned and available pickup lists
- Accept, start, collect, and complete pickup assignments with dedicated API endpoints
- Record verified weight on completion
- Personal summary statistics (completions, earnings proxy, active assignments)
- **Collector live map** â€” dependency-free SVG map with equirectangular projection, pickup markers, browser-geolocation position reporting, sequenced nearest-neighbour route, and nearby-pickup discovery with Haversine distance
- Masked communication â€” initiate anonymized contact sessions with citizens (`POST /pickup-requests/{id}/contact`)

### Dealer / Recycler Marketplace

- **Dealer profile workflow** â€” four-state approval lifecycle (`draft â†’ submitted â†’ approved/rejected`); profile includes business name, owner name, GST, license, and accepted materials
- **Admin approval queue** â€” `GET /admin/dealers/pending` with search and pagination; approve/reject with required reason; full approval-event timeline
- **Inventory browsing** â€” paginated, searchable, sortable, filterable marketplace of inventory lots with quality-grade and source-address snapshots
- **Reserve & purchase** â€” 24-hour reservations with auto-expiry enforcement; row-lock-guarded purchases creating `MarketplaceOrder` + `MarketplaceTransaction` ledger entries
- **Order & transaction history** â€” dealers can review reservation, cancellation, and purchase records

### Administration & Analytics

- **Platform analytics** â€” KPIs (total users, total pickups, total weight, pickups by status), material distribution, 12-month pickup trends, collector/dealer performance rankings, carbon savings estimates
- **Admin inventory management** â€” create, update, archive, restore, and toggle visibility of inventory lots; auto-generated lot numbers (`WIQ-<YYYYMM>-<id>`)
- **Pricing rules engine** â€” per-kg pricing rules scoped by material category + city; snapshots recorded on lot creation
- **Material categories** â€” configurable master list with code, name, description, display order, and active flag
- **User management** â€” list all users; admin login history with actor attribution and date-range filtering
- **Weight dispute resolution** â€” admin review and resolution of citizen disputes

### Notifications & Communication

- Database-backed in-app notification system for all four roles
- **Pickup lifecycle events** â€” `pickup_created`, `pickup_accepted`, `pickup_started`, `pickup_collected`, `pickup_completed`
- **Dealer lifecycle events** â€” `profile_submitted`, `profile_approved`, `profile_rejected`
- **Inventory events** â€” `lot_created`, `lot_reserved`, `lot_reservation_expired`, `lot_purchased`
- **Admin broadcasts** â€” `POST /admin/notifications/broadcast` to targeted roles
- Full API surface: `GET /notifications` (paginated + status filter), `GET /notifications/unread`, `GET /notifications/unread/count`, `POST /notifications/{id}/read`, `POST /notifications/read-all`, `DELETE /notifications/{id}`

### Inventory & Material Lots

- One-to-one linkage from completed `PickupRequest` to `InventoryLot`
- State-change audit trail (`inventory_lot_events`) with actor attribution and JSON metadata
- Composite indexes on `(status, visibility, source_city)` for performant dealer browsing
- Archiving and restoration for retired lots

### Waste Images / Media

- Multi-part form uploads via Cloudinary (production) with automatic deletion on pickup cancellation using persisted `image_public_id`
- Local filesystem storage fallback for development and local-simulation deployments (`DEPLOYMENT_MODE=local-simulation`)
- Graceful degradation â€” uploads skipped (URL stored as NULL) when Cloudinary credentials are absent in development

### Auditability / Traceability

- Comprehensive `audit_log` table recording every authenticated action with actor, resource, outcome, and before/after snapshots
- Specialized event tables: `pickup_request_event`, `inventory_lot_event`, `dealer_profile_event`, `refresh_token`
- Audit events never store token material, passwords, or hashes
- Dedicated audit log route for administrators (`GET /admin/audit-logs`)

### Background Jobs

- In-process APScheduler triggered via FastAPI lifespan
- **Reservation sweep** â€” periodically checks for expired reservations and records `reservation_expired` transactions
- **Aging pickup check** â€” flags stale pending/accepted pickups after configurable threshold

---

## Architecture

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                          Clients                                         â”‚
â”‚                                                                      â”‚
â”‚   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”‚
â”‚   â”‚  Citizen â”‚   â”‚   Collector  â”‚   â”‚    Dealer  â”‚   â”‚    Admin   â”‚ â”‚
â”‚   â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”˜   â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜   â””â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜   â””â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜ â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
         â”‚                â”‚                 â”‚                â”‚
         â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”
                     â”‚                 â”‚                â”‚        â”‚
   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”            â”‚        â”‚
   â”‚  Frontend â€” React 19 SPA            â”‚            â”‚        â”‚
   â”‚  (Vite + TypeScript + Tailwind)    â”‚            â”‚        â”‚
   â”‚  Axios + TanStack Query            â”‚            â”‚        â”‚
   â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜            â”‚        â”‚
                          â”‚                           â”‚        â”‚
   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”â”‚        â”‚
   â”‚ Backend â€” FastAPI                                 â”‚â”‚        â”‚
   â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”          â”‚â”‚        â”‚
   â”‚  â”‚  Routes  â”‚â†’â”‚ Services â”‚â†’â”‚Repos.   â”‚â†’â”‚  Models   â”‚        â”‚
   â”‚  â”‚  (jwt +  â”‚  â”‚ (businessâ”‚  â”‚ (query â”‚  â”‚(SQLAlchemy)â”‚       â”‚
   â”‚  â”‚  role    â”‚  â”‚  logic)  â”‚  â”‚ logic) â”‚  â”‚           â”‚       â”‚
   â”‚  â”‚  guard)  â”‚  â”‚          â”‚  â”‚        â”‚  â”‚           â”‚       â”‚
   â”‚  â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”¬â”€â”€â”€â”˜          â”‚        â”‚
   â”‚       â”‚            â”‚            â”‚               â”‚        â”‚
   â”‚       â”‚    â”Œâ”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”            â”‚        â”‚
   â”‚       â”‚    â”‚  Core: config, security,â”‚            â”‚        â”‚
   â”‚       â”‚    â”‚  rate-limit, middleware â”‚             â”‚        â”‚
   â”‚       â”‚    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜            â”‚        â”‚
   â”‚       â”‚                                           â”‚        â”‚
   â”‚       â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â†’ PostgreSQL (primary)         â”‚        â”‚
   â”‚       â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â†’ Redis (optional cache/session)â”‚         â”‚
   â”‚       â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â†’ Cloudinary (image storage)    â”‚        â”‚
   â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜        â”‚
                                                               â”‚
   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”       â”‚
   â”‚ Agent â€” FastAPI (GitHub App automation)          â”‚       â”‚
   â”‚  Webhook receiver, issue/PR sync, reviews        â”‚       â”‚
   â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜       â”‚
                                                               â”‚
   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”       â”‚
   â”‚ CI/CD â€” GitHub Actions                           â”‚       â”‚
   â”‚  Backend CI Â· Frontend CI Â· Agent CI Â·            â”‚       â”‚
   â”‚  Docker CI Â· PR Gate                              â”‚       â”‚
   â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜       â”‚
                                                               â”‚
   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â” â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”         â”‚
   â”‚   Render.com â”‚ â”‚ Docker       â”‚ â”‚ Development  â”‚        â”‚
   â”‚   (prod)     â”‚ â”‚ Compose      â”‚ â”‚  (local)     â”‚        â”‚
   â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜ â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜        â”‚
```

**Pickup Request Lifecycle:**

```mermaid
stateDiagram-v2
    [*] --> pending: Citizen submits request
    pending --> accepted: Collector accepts
    pending --> cancelled: Citizen cancels
    accepted --> on_the_way: Collector starts
    collected --> completed: Collector records weight
    completed --> archived: Inventory lot created
    collected --> disputed: Citizen disputes weight
    disputed --> resolved: Admin resolves dispute
    cancelled --> [*]
```

**Key design principles:**
- **Layered architecture** â€” Routes â†’ Services â†’ Repositories â†’ Models, each with single-responsibility separation
- **Role-based access control** â€” enforced at both route (FastAPI `Depends`) and service layers
- **Email-verified accounts** required for collector, dealer, and admin roles (citizens can register without verification but cannot submit pickups until verified)
- **Audit-first** â€” every state-changing action is recorded with actor attribution before the response is sent
- **Fail-safe defaults** â€” missing Cloudinary credentials in development never crash the app; they degrade gracefully

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, TypeScript 5.5, Vite 5 |
| **Frontend Styling** | Tailwind CSS 3.4, shadcn/ui (Radix UI) |
| **Frontend State** | TanStack Query 5, React Hook Form + Zod |
| **Backend** | Python 3.12, FastAPI 0.115, Uvicorn 0.34 |
| **Database** | PostgreSQL 16 (primary), SQLite (local dev) |
| **ORM** | SQLAlchemy 2.0 with `Mapped[]` annotations |
| **Migrations** | Alembic 1.16 |
| **Validation** | Pydantic v2 |
| **Authentication** | python-jose (JWT HS256), bcrypt |
| **Image Storage** | Cloudinary (1.44); local filesystem fallback for dev |
| **Rate Limiting** | In-memory per-process sliding window |
| **Background Jobs** | APScheduler (via FastAPI lifespan) |
| **Frontend Testing** | Vitest, React Testing Library, MSW |
| **Backend Testing** | Pytest, httpx AsyncClient, coverage |
| **Linting & Types** | Ruff, Black, MyPy (Python); ESLint, tsc (TypeScript) |
| **Containerization** | Docker + Docker Compose |
| **CI/CD** | GitHub Actions (backend, frontend, agent, docker, PR gate) |
| **Deployment** | Render.com, Docker Compose |

---

## Prerequisites

| Tool | Minimum Version |
|------|----------------|
| Python | 3.12+ |
| Node.js | 20+ |
| Git | 2.40+ |
| Docker *(recommended)* | 24+ |

> PostgreSQL is only required for production. Local development uses SQLite by default. Cloudinary credentials are optional in development (uploads are skipped with a NULL URL when absent).

---

## Quick Start (Docker)

The fastest way to run the full stack locally is with Docker Compose.

```bash
# 1. Clone and enter the repository
git clone https://github.com/Subhajitdas99/waste-iq.git
cd waste-iq

# 2. Configure backend environment
cp backend/.env.example backend/.env
# (SQLite is the default in .env.example â€” no edits required for first run)

# 3. Build and start all services
docker compose up --build

# 4. Apply database migrations (first run only)
docker compose exec backend alembic upgrade head
```

| Service | Port | URL |
|---------|------|-----|
| Backend API | 8000 | http://localhost:8000 |
| API Docs (Swagger) | 8000 | http://localhost:8000/docs |
| Frontend | 5173 | http://localhost:5173 |
| PostgreSQL | 5432 | â€” (internal) |

---

## Local Development

### Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Configure environment
cp .env.example .env

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Set VITE_API_URL=http://localhost:8000

# Start development server
npm run dev
```

**Frontend available at http://localhost:5173.**

### Development Commands

```bash
# Backend
ruff check app tests              # Lint
black --check app tests           # Format check
mypy app                          # Type check
pytest tests -v --cov=app         # Run tests with coverage

# Frontend
npm run lint                      # Lint
npx tsc --noEmit                  # Type check
npm test                          # Run tests
```

---

## Environment Variables

> **Security:** `.env` files contain secrets and must never be committed. They are listed in `.gitignore`. Always use `.env.example` as a template and fill in your own values.

### Backend (`backend/.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | `sqlite:///wasteiq.db` | Database connection string |
| `DEPLOYMENT_MODE` | Yes | `development` | `development`, `local-simulation`, or `production` |
| `ENVIRONMENT` | Yes | `development` | `development`, `testing`, or `production` |
| `JWT_SECRET_KEY` | Yes | â€” | Strong random secret for JWT signing |
| `JWT_ALGORITHM` | No | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `30` | Refresh token lifetime |
| `CORS_ORIGINS` | Yes | `http://localhost:5173` | Comma-separated allowed CORS origins |
| `CLOUDINARY_CLOUD_NAME` | No (prod: yes) | â€” | Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | No (prod: yes) | â€” | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | No (prod: yes) | â€” | Cloudinary API secret |
| `LOCAL_IMAGE_STORAGE_ENABLED` | No | `false` | Local storage fallback (simulation only) |
| `EMAIL_BACKEND` | No | `console` | `console` (dev) or `smtp` (production) |
| `SMTP_HOST` | No | â€” | SMTP server host |
| `SMTP_PORT` | No | `587` | SMTP server port |
| `SMTP_USER` | No | â€” | SMTP username |
| `SMTP_PASSWORD` | No | â€” | SMTP password (app-specific) |
| `EMAIL_FROM` | No | â€” | Sender email address |
| `FRONTEND_URL` | No | `http://localhost:5173` | Frontend base URL for links in emails |
| `VERIFICATION_TOKEN_EXPIRE_MINUTES` | No | `1440` | Email verification token TTL |
| `PASSWORD_RESET_TOKEN_EXPIRE_MINUTES` | No | `30` | Password reset token TTL |
| `LOGIN_RATE_LIMIT_MAX` | No | `10` | Max login attempts per IP per window |
| `LOCKOUT_FAILED_ATTEMPT_THRESHOLD` | No | `5` | Failed logins before lockout |
| `LOCKOUT_COOLDOWN_MINUTES` | No | `15` | Lockout duration |
| `SENTRY_DSN` | No | â€” | Sentry DSN (leave empty to disable) |

**Example `.env` for production deployment:**

```env
DEPLOYMENT_MODE=production
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DB
JWT_SECRET_KEY=YOUR_SECURE_RANDOM_SECRET
ENVIRONMENT=production
CORS_ORIGINS=https://waste-iq.app
CLOUDINARY_CLOUD_NAME=your-cloud
CLOUDINARY_API_KEY=your-key
CLOUDINARY_API_SECRET=your-secret
EMAIL_BACKEND=smtp
SMTP_HOST=smtp.sendgrid.net
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
EMAIL_FROM=no-reply@waste-iq.app
FRONTEND_URL=https://waste-iq.app
```

### Frontend (`frontend/.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_URL` | Yes | `http://localhost:8000` | Backend API base URL |
| `VITE_APP_NAME` | No | `Waste-IQ` | Application name (used in SEO/meta tags) |
| `VITE_SITE_URL` | No | `http://localhost:5173` | Site URL for SEO (production should match `FRONTEND_URL`) |

---

## API Documentation

- **Swagger UI** (interactive): http://localhost:8000/docs
- **ReDoc** (readable): http://localhost:8000/redoc
- **OpenAPI schema**: http://localhost:8000/openapi.json

### Key API Routes

| Module | Routes |
|--------|--------|
| **Authentication** | `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `POST /auth/logout-all`, `POST /auth/verify-email`, `POST /auth/resend-verification`, `POST /auth/forgot-password`, `POST /auth/reset-password`, `POST /auth/change-password`, `GET /auth/me`, `GET /auth/login-history` |
| **Pickup Requests** | `POST /pickup-requests`, `GET /pickup-requests`, `GET /pickup-requests/{id}`, `PATCH /pickup-requests/{id}`, `POST /pickup-requests/{id}/cancel`, `POST /pickup-requests/{id}/contact`, `POST /pickup-requests/{id}/weight/confirm`, `POST /pickup-requests/{id}/weight/dispute`, `GET /pickup-requests/citizen/summary` |
| **Collector** | `GET /collector/summary`, `GET /collector/pickups/available`, `GET /collector/pickups/assigned`, `POST /collector/pickups/{id}/accept`, `POST /collector/pickups/{id}/start`, `POST /collector/pickups/{id}/collect`, `POST /collector/pickups/{id}/complete`, `POST /collector/pickups/{id}/cancel`, `GET /collector/nearby-pickups`, `GET /collector/route`, `GET /collector/map` |
| **Dealer** | `POST /dealer/profile`, `GET /dealer/profile`, `PUT /dealer/profile`, `POST /dealer/profile/submit`, `GET /dealer/profile/timeline`, `GET /dealer/inventory`, `GET /dealer/inventory/{id}`, `POST /dealer/inventory`, `PUT /dealer/inventory/{id}`, `DELETE /dealer/inventory/{id}`, `POST /dealer/inventory/{id}/reserve`, `POST /dealer/inventory/{id}/release`, `POST /dealer/inventory/{id}/mark-sold` |
| **Inventory** | `GET /inventory/lots`, `GET /inventory/lots/{id}`, `POST /inventory/lots`, `PATCH /inventory/lots/{id}`, `POST /inventory/lots/{id}/archive`, `POST /inventory/lots/{id}/restore`, `GET /inventory/categories`, `GET /inventory/pricing-rules` |
| **Admin** | `GET /admin/users`, `GET /admin/analytics`, `GET /admin/dealers`, `GET /admin/dealers/pending`, `GET /admin/dealers/{id}`, `POST /admin/dealers/{id}/approve`, `POST /admin/dealers/{id}/reject`, `POST /admin/notifications/broadcast`, `GET /admin/login-history`, `GET /admin/disputes/pickups`, `POST /admin/disputes/pickups/{id}/resolve`, `GET /admin/audit-logs` |
| **Notifications** | `GET /notifications`, `GET /notifications/unread`, `GET /notifications/unread/count`, `GET /notifications/{id}`, `POST /notifications/{id}/read`, `POST /notifications/read-all`, `DELETE /notifications/{id}`, `DELETE /notifications/read` |

---

## Testing

### Backend

```bash
cd backend

# Full test suite
pytest tests -v

# With coverage (CI requires 80%+)
pytest tests --cov=app --cov-report=term-missing

# Specific test file
pytest tests/test_auth.py -v

# Filter by keyword
pytest tests -k "pickup" -v
```

Backend tests use `pytest` with `httpx.AsyncClient` for API route tests, a dedicated SQLite test database, and `unittest.mock.patch` for external services (e.g., Cloudinary, email providers). Test fixtures live in `backend/tests/conftest.py`.

### Frontend

```bash
cd frontend

# Run all tests
npm test

# Run in watch mode
npm run test:watch

# Coverage report
npm run test:coverage
```

Frontend tests use `Vitest`, `React Testing Library`, and `MSW` (Mock Service Worker) for API mocking.

**Test suites include:** authentication, email verification, password reset, pickup lifecycle, collector workflows, dealer approval, marketplace, reservations, notifications, analytics, rate limiting, permissions, CORS, security boundaries, masked communication, collector map, audit logging, and end-to-end workflow tests.

---

## CI/CD

Waste-IQ uses GitHub Actions with path-filtered, specialized workflows plus an always-running **PR Gate** aggregator:

| Workflow | Trigger | What it does |
|----------|---------|--------------|
| `backend-ci.yml` | `backend/**`, `pyproject.toml` | Ruff, Black, MyPy, Pytest with PostgreSQL service, coverage upload |
| `frontend-ci.yml` | `frontend/**` | ESLint, TypeScript check, Vitest, production build |
| `agent-ci.yml` | `agent/**` | Ruff, Black, MyPy, Pytest for the AI agent |
| `docker-ci.yml` | Docker files | Validation of Docker configurations |
| `pr-gate.yml` | All PRs | Always runs; requires all *relevant* specialized workflows to pass |

Branch protection on `main` and `develop` requires: PR, 1+ maintainer approval, conversation resolution, and a green PR Gate. See [CONTRIBUTING.md](CONTRIBUTING.md) for full workflow and commit conventions.

### Deployment

- **Production**: Backend and database deployed on Render.com
- **Local simulation**: `docker-compose.yml` spins up backend, frontend, and PostgreSQL
- **Agent**: Standalone service deployable via `docker compose up agent` or directly with `uvicorn`

---

## Screenshots

Screenshots are located in [`docs/screenshots/`](docs/screenshots/).

| Screen |
|--------|
| [Citizen Dashboard](docs/screenshots/citizen-dashboard.png) |
| [Collector Dashboard](docs/screenshots/collector-dashboard.png) |
| [Admin Dashboard](docs/screenshots/admin-dashboard.png) |
| [Login Page](docs/screenshots/login-page.png) |
| [Register Page](docs/screenshots/register-page.png) |

---

## Contributing

Contributions are welcome! Please read:

- **[Contributing Guide](CONTRIBUTING.md)** â€” branch naming, commit conventions, PR process
- **[Code of Conduct](CODE_OF_CONDUCT.md)** â€” community standards
- **[Changelog](CHANGELOG.md)** â€” release history

### Quick Start

```bash
git clone https://github.com/Subhajitdas99/waste-iq.git
git checkout -b feat/your-feature-name
# ... make changes, write tests, run lint/typecheck ...
git commit -m "feat(scope): your feature"
git push origin feat/your-feature-name
```

Open a PR against `develop`. All PRs must pass the CI pipeline and PR Gate.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history and development progress. The project follows [Keep a Changelog](https://keepachangelog.com/) and [Semantic Versioning](https://semver.org/).

---

## License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

---

## Links

- **Repository**: https://github.com/Subhajitdas99/waste-iq
- **Issues**: https://github.com/Subhajitdas99/waste-iq/issues
- **Documentation**: [docs/](docs/)
- **AI Engineering Agent**: [agent/README.md](agent/README.md)
