# Deployment Guide — Waste-IQ

> This guide covers every deployment scenario: local development (without Docker), Docker Compose (full-stack), and production deployment to Render.com. It also documents the environment variable reference, migration workflow, monitoring strategy, backup, and troubleshooting.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Local Development Setup (Without Docker)](#2-local-development-setup-without-docker)
3. [Docker Setup](#3-docker-setup)
4. [Environment Variables Reference](#4-environment-variables-reference)
5. [Database Migrations](#5-database-migrations)
6. [Production Deployment on Render.com](#6-production-deployment-on-rendercom)
7. [Production Checklist](#7-production-checklist)
8. [Monitoring & Logging](#8-monitoring--logging)
9. [Backup Strategy](#9-backup-strategy)
10. [Rollback Strategy](#10-rollback-strategy)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Prerequisites

Install these tools before following any deployment path:

| Tool | Minimum Version | Check Command | Install |
|------|----------------|---------------|---------|
| **Git** | 2.40+ | `git --version` | [git-scm.com](https://git-scm.com) |
| **Python** | 3.12+ | `python --version` | [python.org](https://python.org) |
| **Node.js** | 20+ | `node --version` | [nodejs.org](https://nodejs.org) |
| **npm** | 10+ | `npm --version` | Bundled with Node.js |
| **Docker** *(optional)* | 24+ | `docker --version` | [docs.docker.com](https://docs.docker.com/get-docker/) |
| **Docker Compose** *(optional)* | v2+ | `docker compose version` | Bundled with Docker Desktop |

> **PostgreSQL** is only needed as a separate install for production-like local setups. The default local dev configuration uses **SQLite** (no additional install required).

---

## 2. Local Development Setup (Without Docker)

### Step 1 — Clone the Repository

```bash
git clone https://github.com/your-org/waste-iq.git
cd waste-iq
```

### Step 2 — Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate — Windows (PowerShell)
.venv\Scripts\activate

# Activate — macOS / Linux
source .venv/bin/activate

# Install all dependencies including dev tools
pip install -r requirements.txt -r requirements-dev.txt

# Copy environment configuration
cp .env.example .env
```

Edit `backend/.env` — see [Environment Variables Reference](#4-environment-variables-reference).

For local development, the defaults in `.env.example` are sufficient:
- `DATABASE_URL=sqlite:///wasteiq.db` (no PostgreSQL needed)
- `JWT_SECRET_KEY=dev_secret_key_change_me` (change this even locally)
- Cloudinary fields can be left blank

```bash
# Run all Alembic migrations (creates wasteiq.db)
alembic upgrade head

# Start the backend with auto-reload
uvicorn app.main:app --reload --port 8000
```

✅ Backend available at **http://localhost:8000**  
✅ Swagger UI at **http://localhost:8000/docs**  
✅ Health check at **http://localhost:8000/health**

---

### Step 3 — Frontend Setup

Open a **new terminal** window:

```bash
cd frontend

# Install npm dependencies
npm install

# Copy environment configuration
cp .env.example .env
```

Edit `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

```bash
# Start Vite dev server with HMR
npm run dev
```

✅ Frontend available at **http://localhost:5173**

---

### Step 4 — Verify Setup

1. Open http://localhost:5173
2. Click **Register** and create a citizen account
3. Log in and verify the dashboard loads
4. Open http://localhost:8000/docs to verify all API endpoints are listed

---

## 3. Docker Setup

Docker Compose runs the complete stack (PostgreSQL, FastAPI backend, and React frontend via Nginx) with a single command.

### Step 1 — Configure Backend Environment

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` and set the database URL to use the Docker PostgreSQL container:

```env
DATABASE_URL=postgresql://wasteiq:wasteiq@db:5432/wasteiq
ENVIRONMENT=development
JWT_SECRET_KEY=change-this-to-a-strong-random-secret
ACCESS_TOKEN_EXPIRE_MINUTES=1440
CORS_ORIGINS=http://localhost:5173
```

### Step 2 — Build and Start All Services

```bash
# From the repository root
docker compose up --build
```

This will:
1. Pull `postgres:16-alpine` and start the database
2. Build the backend image from `./backend/Dockerfile`
3. Run `alembic upgrade head` automatically (see Dockerfile CMD)
4. Start Uvicorn on port 8000
5. Build the frontend image and serve it on port 5173 via Nginx

### Step 3 — Verify Services

| Service | URL | Expected Response |
|---------|-----|-------------------|
| Backend health | http://localhost:8000/health | `{"status":"ok"}` |
| API docs | http://localhost:8000/docs | Swagger UI |
| Frontend | http://localhost:5173 | React app |
| Database | `localhost:5432` | PostgreSQL (use psql or DBeaver) |

### Useful Docker Commands

```bash
# View logs for a specific service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db

# Run migrations inside the container
docker compose exec backend alembic upgrade head

# Open a PostgreSQL shell
docker compose exec db psql -U wasteiq -d wasteiq

# Open a bash shell in the backend container
docker compose exec backend bash

# Rebuild a specific service after code change
docker compose up --build backend

# Stop all services (preserves data volumes)
docker compose down

# Stop and remove all data (full clean slate)
docker compose down -v --remove-orphans

# List running containers
docker compose ps
```

### Production-Oriented Full-Stack Container Deployment

For a self-contained production deployment (single host or VM), the repository ships a hardened production override: `docker-compose.prod.yml`. It layers on top of the base Compose file:

```bash
export COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml   # optional convenience
# …or pass both files explicitly on every command:
docker compose -f docker-compose.yml -f docker-compose.prod.yml <command>
```

**What the production override changes compared to the base file:**

| Area | Base (`docker-compose.yml`) | Production override |
|------|------------------------------|---------------------|
| Restart policy | none (manual dev lifecycle) | `unless-stopped` on db/backend/frontend |
| Database exposure | `localhost:5432` | not published (compose network only) |
| Backend secrets | `backend/.env` file | environment variables only (`${VAR:?}` fail-fast) |
| Backend port | fixed `8000:8000` | `${BACKEND_PORT:-8000}:8000` |
| Frontend port | fixed `5173:80` | `${FRONTEND_PORT:-8080}:80` |
| Frontend API URL | build-time default `http://localhost:8000` | build arg `VITE_API_URL` |
| Upload temp dir | ephemeral container fs | named volume `uploads_data:/app/uploads` |
| Dev-only `agent` service | started with the stack | excluded via Compose profile |

#### Prerequisites

| Tool | Minimum Version | Check Command |
|------|-----------------|---------------|
| Docker Engine | 24+ (with Compose V2 built in) | `docker --version` |
| Docker Compose | v2.24+ (required for `!reset` override syntax) | `docker compose version` |

#### Required Production Environment Variables

Compose interpolates variables from your shell environment **or** a project-root `.env` file (git-ignored — verify with `git check-ignore .env`). Required variables fail fast at config-parse time if missing:

```bash
POSTGRES_PASSWORD=<strong random password>        # openssl rand -hex 24
JWT_SECRET_KEY=<strong random secret, ≥32 chars>  # openssl rand -hex 32
CORS_ORIGINS=https://your-frontend-domain         # comma-separated, exact match
FRONTEND_URL=https://your-frontend-domain          # used to build verification links
VITE_API_URL=https://api.your-domain               # baked into the frontend bundle at build time
```

Optional but recommended in production:

```bash
ENVIRONMENT=production                     # implied by the override
ADMIN_REGISTRATION_CODE=…                  # enables admin sign-up
BOOTSTRAP_ADMIN_NAME=… / BOOTSTRAP_ADMIN_EMAIL=… / BOOTSTRAP_ADMIN_PHONE=… / BOOTSTRAP_ADMIN_PASSWORD=…
CLOUDINARY_CLOUD_NAME=… / CLOUDINARY_API_KEY=… / CLOUDINARY_API_SECRET=…   # required for uploads when ENVIRONMENT=production (503 otherwise)
EMAIL_BACKEND=smtp / SMTP_HOST=… / SMTP_USER=… / SMTP_PASSWORD=… / EMAIL_FROM=…
SENTRY_DSN=… / RELEASE=vX.Y.Z
BACKEND_PORT=8000 / FRONTEND_PORT=8080     # host-side ports
```

> ⚠️ **Never commit these values.** Generate secrets with `openssl rand -hex 32`; rotate `JWT_SECRET_KEY` only with an awareness that all issued access tokens are invalidated (refresh tokens remain valid because they are stored server-side).

#### Secret Configuration Summary

- **Backend image:** no secrets are copied into the image; configuration is injected at runtime through the Compose `environment:` mapping.
- **Frontend image:** only public values (`VITE_*`) are baked in at build time — they are visible in the shipped JS bundle by design and must never contain secrets.
- **Database password:** provided once via `POSTGRES_PASSWORD` and referenced internally; PostgreSQL is never exposed on the host.
- **JWT secret:** provided via `JWT_SECRET_KEY`; the Compose config fails fast when it is unset.

#### Building Images

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml build
```

CI validates that both images build on every relevant PR (see `.github/workflows/docker-ci.yml`); images are not pushed by CI.

#### Starting the Stack

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

Startup order is health-gated: **db → (healthy) → backend runs `alembic upgrade head`, then serves traffic → (healthy) → frontend**. Migrations run automatically inside the backend container before Uvicorn binds its port (established startup pattern preserved from the original Dockerfile CMD).

#### Checking Container Health

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

Wait until all three services report `(healthy)`:

| Service | Healthcheck | Meaning |
|---------|-------------|---------|
| `db` | `pg_isready -U $POSTGRES_USER -d $POSTGRES_DB` | PostgreSQL accepts connections |
| `backend` | HTTP GET `/health/ready` inside the container | process up **and** database reachable |
| `frontend` | HTTP GET `/health` against Nginx | static server responding |

#### Database Readiness

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec db pg_isready -U wasteiq -d wasteiq
```

#### Backend Readiness

```bash
curl -fsS http://localhost:8000/health        # {"status":"ok", …}
curl -fsS http://localhost:8000/health/ready  # {"status":"ready", …}
```

`/health/ready` returns `503` while the database is unreachable — use it for load-balancer readiness probes.

#### Frontend Availability

```bash
curl -fsS http://localhost:8080/health   # ok (Nginx static server)
```

Then open `http://localhost:8080` (or your configured domain) in a browser.

#### Logs

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f db
```

Watch for `Application startup complete.` and `Scheduler started` in backend logs; migration errors appear here and cause the backend container to exit (the restart policy retries it, so fix the underlying issue rather than restarting blindly).

### Monitoring & Logging (WIQ-V1-023)

#### JSON Structured Logging

Every log line — application **and** Uvicorn access/error logs — is a single-line JSON object emitted by `app.core.logging.setup_logging`:

```json
{"timestamp": "2026-08-25T12:00:00+0000", "level": "INFO", "logger": "uvicorn.access", "message": "127.0.0.1 - \"GET /health/ready HTTP/1.1\" 200", "request_id": "7f9c24e2-...", "event": "access", "method": "GET", "path": "/health/ready", "status_code": 200, "client_addr": "127.0.0.1", "http_version": "1.1"}
```

Fields: `timestamp`, `level`, `logger`, `message`, `request_id`, plus structured access fields (`method`, `path`, `status_code`, …) on Uvicorn access records, `extra` fields passed by application code, and an `exception` string with tracebacks.

#### Request IDs

`RequestIDMiddleware` assigns every request a correlation ID, returned in the `X-Request-ID` response header and attached to every log line of that request. A client-supplied `X-Request-ID` is trusted only when it is ≤ 64 characters and uses `A–Z a–z 0–9 . _ -`; anything else (missing, oversized, whitespace/control characters) is replaced with a generated UUID4.

#### LOG_LEVEL

`LOG_LEVEL` (`DEBUG`, `INFO`, default `WARNING`, `ERROR`, `CRITICAL`) controls the effective level of root/application logging and all Uvicorn loggers. At levels above `INFO`, access logs are suppressed.

#### Sentry Error Tracking

Sentry is active only when `SENTRY_DSN` is set — with no DSN the SDK stays completely disabled and makes no network calls:

| Variable | Purpose |
|----------|---------|
| `SENTRY_DSN` | Enables Sentry when set; leave empty to disable |
| `ENVIRONMENT` | Reported as the Sentry environment tag (`development`/`staging`/`production`) |
| `RELEASE` | Reported as the Sentry release tag (e.g. `v1.2.3`; defaults to `local`) |

Behavior: FastAPI/Starlette integrations are enabled so unhandled route exceptions are captured; the authenticated user's numeric id is attached as user context (id only — never tokens, emails or other PII); `send_default_pii` remains off so request bodies/cookies are not reported. Tests and CI never contact Sentry (`SENTRY_DSN` is pinned empty in the test environment).

#### Readiness Endpoint

`GET /health/ready` verifies database connectivity (503 `database_unreachable` while down). When `ENVIRONMENT=production` it additionally requires Cloudinary configuration to be present — returning 503 `cloudinary_not_configured` if `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY` or `CLOUDINARY_API_SECRET` are missing. The check inspects configuration only and never calls Cloudinary, so probes stay fast and deterministic. Non-production environments are unaffected by the Cloudinary requirement.

#### Prometheus Metrics — Deferred

Prometheus `/metrics` (`prometheus-fastapi-instrumentator`) is intentionally **deferred**: Render.com already exposes CPU/memory/request metrics in its dashboard, and no scraper infrastructure exists yet. Revisit when self-hosted monitoring (Grafana) or multi-instance alerting is introduced.

#### Restart Behavior

All production services use `restart: unless-stopped`: containers come back automatically after crashes or daemon/host restarts, but stay stopped if you explicitly run `stop`. A failing backend (e.g., bad migration) will be retried by Docker — check logs instead of assuming transient failure.

#### Stopping the Stack

```bash
# Stop, keep data volumes
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# Stop AND remove database/upload data (destructive!)
docker compose -f docker-compose.yml -f docker-compose.prod.yml down -v
```

#### Updating / Rebuilding Images

```bash
git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml build
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

New migrations are applied automatically by the backend's startup command. Take a database backup first (see [Backup Strategy](#9-backup-strategy)).

#### Smoke Test

Run after every deployment. Use a **throwaway account** and remember the rate limits (registration: 10 requests per IP per window; login: 10 per IP and 5 per account per window — see `LOGIN_RATE_LIMIT_MAX`, `REGISTER_RATE_LIMIT_MAX`, `RATE_LIMIT_WINDOW_SECONDS`):

```bash
API=http://localhost:8000

# 1. Liveness
curl -fsS "$API/health"

# 2. Readiness (database connectivity)
curl -fsS "$API/health/ready"

# 3. Registration (returns 201 with access + refresh tokens)
curl -fsS -X POST "$API/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"name":"Smoke Test","email":"smoke-test@example.com","phone":"+10000000000","password":"Str0ngPassw0rd!","role":"citizen"}'

# 4. Login (returns 200 with fresh tokens)
curl -fsS -X POST "$API/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"smoke-test@example.com","password":"Str0ngPassw0rd!"}'
```

All four commands must succeed without 5xx responses. Do not reuse real credentials in scripts or shell history.

#### Background Jobs (Single-Instance Assumption)

APScheduler runs **in-process** inside the backend container (`reservation sweep`, `aging pickup alerts`). This is safe for exactly one backend replica — do **not** scale the backend service horizontally (`--scale backend=N` duplicates scheduled work). For multi-instance deployments set `ENABLE_BACKGROUND_JOBS=false` on web instances and move scheduling to Celery Beat (see [Monitoring & Logging](#8-monitoring--logging)).

---

## 4. Environment Variables Reference

### Backend (`backend/.env`)

| Variable | Required | Default | Description | Example |
|----------|----------|---------|-------------|---------|
| `DATABASE_URL` | ✅ | `sqlite:///wasteiq.db` | Database connection string. Use `postgresql://` in production | `postgresql://wasteiq:password@localhost:5432/wasteiq` |
| `ENVIRONMENT` | ✅ | `development` | App environment. Affects behaviour of some services | `production` |
| `JWT_SECRET_KEY` | ✅ | — | Secret used to sign JWTs. Must be strong and random in production | `openssl rand -hex 32` |
| `JWT_ALGORITHM` | ❌ | `HS256` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | ❌ | `1440` | JWT token lifetime in minutes (1440 = 24 hours) | `1440` |
| `CORS_ORIGINS` | ✅ | `http://localhost:5173` | Comma-separated list of allowed CORS origins | `https://app.waste-iq.dev,http://localhost:5173` |
| `CLOUDINARY_CLOUD_NAME` | ✅ prod | — | Cloudinary cloud name. Optional in development (uploads are skipped) | `my-cloud-name` |
| `CLOUDINARY_API_KEY` | ✅ prod | — | Cloudinary API key | `123456789012345` |
| `CLOUDINARY_API_SECRET` | ✅ prod | — | Cloudinary API secret. Never logged, never exposed in API responses | `abcdefghijklmnopqrstuvwxyz` |
| `ENABLE_BACKGROUND_JOBS` | ❌ | `true` | Run the in-process APScheduler jobs inside the FastAPI lifespan. Set to `false` to run scheduled work externally (e.g. a Celery worker). Always `false` in the test environment | `true` |
| `RESERVATION_SWEEP_INTERVAL_MINUTES` | ❌ | `1` | How often the expired-reservation sweep runs (minutes, > 0) | `1` |
| `AGING_PICKUP_INTERVAL_MINUTES` | ❌ | `5` | How often the aging-pickup alert check runs (minutes, > 0) | `5` |
| `AGING_PICKUP_THRESHOLD_DAYS` | ❌ | `2` | Age (days) after which a `pending`/`accepted` pickup alerts admins | `2` |

> ⚠️ **In production:** `CLOUDINARY_*` variables are **required** for image uploads. If they are missing, an upload attempt returns `503` (`Image upload service is not configured`); if Cloudinary is unreachable or rejects the request, it returns `502` (`Image upload service unavailable`). Uploads are never silently dropped in production. In development, if they are not set, image uploads are skipped and `image_url` is stored as `NULL` — the explicit, documented development fallback.

> **Upload storage convention (WIQ-V1-020):** every uploaded waste photo is stored under `pickups/{user_id}/{uuid}` (e.g. `pickups/42/9f8c1a2b…`). The path uses only the numeric user ID and a random 32-hex UUID — never email addresses, usernames, or other identifying strings. The Cloudinary `public_id` is persisted in `pickup_requests.image_public_id` (server-side only, never exposed in API responses) so the exact stored asset can be deleted when the request is cancelled.

> ⚠️ **In production:** `JWT_SECRET_KEY` must be a cryptographically random string of at least 32 characters. Generate one with: `openssl rand -hex 32`

### Frontend (`frontend/.env`)

| Variable | Required | Default | Description | Example |
|----------|----------|---------|-------------|---------|
| `VITE_API_URL` | ✅ | `http://localhost:8000` | Base URL of the FastAPI backend | `https://api.waste-iq.dev` |

---

## 5. Database Migrations

Waste-IQ uses **Alembic** exclusively for all database schema changes. Never run `Base.metadata.create_all()` or modify the schema manually in production.

### Apply All Pending Migrations

```bash
cd backend
alembic upgrade head
```

### Create a New Migration (After Model Changes)

```bash
# Autogenerate from model changes
alembic revision --autogenerate -m "add user notification preferences"

# Always review the generated file in alembic/versions/ before applying!
alembic upgrade head
```

### Downgrade by One Revision

```bash
# Revert the most recent migration
alembic downgrade -1

# Revert to a specific revision
alembic downgrade <revision_id>
```

> ⚠️ **Never run `alembic downgrade` in production without a database backup.** Data may be permanently lost.

### View Migration History

```bash
# Show all migration steps
alembic history --verbose

# Show current applied revision
alembic current
```

### Migrations in Docker

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend alembic history
```

### Production Migration (Automatic)

The backend `Dockerfile` runs migrations automatically on container startup:

```dockerfile
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

This means every time Render.com deploys a new version, migrations run before traffic is served. Ensure all migrations are backward-compatible or use blue-green deployment for breaking changes.

---

## 6. Production Deployment on Render.com

### Architecture on Render

```
GitHub (main branch)
    ↓ push triggers
GitHub Actions (CI passes)
    ↓ webhook
Render.com
    ├── Web Service (FastAPI)  ←→  Render PostgreSQL (Managed DB)
    └── Static Site (React dist/)
```

### 6.1 Backend — Web Service

1. **Create a new Web Service** on [Render Dashboard](https://dashboard.render.com).
2. Connect your **GitHub repository**.
3. Set the following:

   | Setting | Value |
   |---------|-------|
   | **Root Directory** | `backend` |
   | **Environment** | `Python 3` |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
   | **Plan** | Starter (or higher for production) |

4. **Add Environment Variables** in the Render dashboard (do not commit secrets to the repo):

   | Variable | Value |
   |----------|-------|
   | `DATABASE_URL` | Render Internal Database URL (from your Render PostgreSQL instance) |
   | `ENVIRONMENT` | `production` |
   | `JWT_SECRET_KEY` | `<generate with openssl rand -hex 32>` |
   | `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` |
   | `CORS_ORIGINS` | `https://your-frontend-url.onrender.com` |
   | `CLOUDINARY_CLOUD_NAME` | `<your cloud name>` |
   | `CLOUDINARY_API_KEY` | `<your api key>` |
   | `CLOUDINARY_API_SECRET` | `<your api secret>` |

5. Click **Deploy**. Render will install dependencies, run migrations, and start Uvicorn.

---

### 6.2 Database — Render PostgreSQL

1. In Render, go to **New → PostgreSQL**.
2. Name: `waste-iq-db` | Plan: Starter.
3. Copy the **Internal Database URL** into the backend service's `DATABASE_URL` env var.
4. The backend's `CMD` will run `alembic upgrade head` automatically on first start.

---

### 6.3 Frontend — Static Site

1. **Create a new Static Site** on Render.
2. Connect your **GitHub repository**.
3. Set the following:

   | Setting | Value |
   |---------|-------|
   | **Root Directory** | `frontend` |
   | **Build Command** | `npm install && npm run build` |
   | **Publish Directory** | `dist` |

4. **Add Environment Variables:**

   | Variable | Value |
   |----------|-------|
   | `VITE_API_URL` | `https://your-backend.onrender.com` |

5. Click **Deploy**.

---

### 6.4 Render Auto-Deploy Configuration (`render.yaml`)

The repository includes a `render.yaml` at the project root for infrastructure-as-code configuration:

```yaml
# render.yaml — Infrastructure as code for Render.com
services:
  - type: web
    name: waste-iq-backend
    env: python
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: waste-iq-db
          property: connectionString
      - key: ENVIRONMENT
        value: production

  - type: static
    name: waste-iq-frontend
    rootDir: frontend
    buildCommand: npm install && npm run build
    staticPublishPath: dist

databases:
  - name: waste-iq-db
    databaseName: wasteiq
    plan: starter
```

---

## 7. Production Checklist

Run through this checklist before every production deployment:

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | `DATABASE_URL` points to production PostgreSQL | ☐ | Never use SQLite in production |
| 2 | `JWT_SECRET_KEY` is a strong random string (≥ 32 chars) | ☐ | `openssl rand -hex 32` |
| 3 | `ENVIRONMENT=production` is set | ☐ | Enables production-only behaviour |
| 4 | `CORS_ORIGINS` includes only the production frontend URL | ☐ | No `localhost` in production CORS |
| 5 | Cloudinary credentials are configured and tested | ☐ | Test image upload in staging first |
| 6 | `alembic upgrade head` ran successfully | ☐ | Check backend startup logs |
| 7 | `GET /health` returns `200 OK` in production | ☐ | `curl https://api.waste-iq.dev/health` |
| 8 | HTTPS is enforced (no HTTP redirect) | ☐ | Render provides this automatically |
| 9 | Admin user bootstrapped and credentials secured | ☐ | Log in once and verify |
| 10 | Database backup is scheduled | ☐ | Render Starter: daily backups |
| 11 | Uptime monitoring alert configured | ☐ | UptimeRobot or Better Uptime on `/health` |
| 12 | `CHANGELOG.md` updated and version tag pushed | ☐ | `git tag v0.2.0 && git push --tags` |
| 13 | Frontend `VITE_API_URL` points to production backend | ☐ | Not a localhost URL |
| 14 | No debug endpoints (`/debug/*`) reachable in production | ☐ | Remove or guard behind admin check |

---

## 8. Monitoring & Logging

### Log Access

**Render.com** captures all `stdout` / `stderr` output from Uvicorn:

```bash
# Via Render Dashboard: Service → Logs tab
# Via Render CLI:
render logs --tail --service waste-iq-backend
```

**Important log messages to monitor:**

| Log Pattern | Meaning | Action |
|-------------|---------|--------|
| `INFO: Application startup complete.` | Backend started successfully | None |
| `ERROR: Could not connect to database` | Database connection failed | Check `DATABASE_URL` and DB service health |
| `WARNING: CORS blocked request from` | CORS misconfiguration | Check `CORS_ORIGINS` env var |
| `CRITICAL: alembic upgrade failed` | Migration error on startup | Check migration file for conflicts |
| `503: Image upload service is not configured` | Cloudinary not set up | Set `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` in production (`ENVIRONMENT=production`) |
| `502: Image upload service unavailable` | Cloudinary is unreachable or rejected the request | Check [status.cloudinary.com](https://status.cloudinary.com) and the Cloudinary credentials |
| `INFO: Scheduler started` | APScheduler background jobs are running | None. If absent, check `ENABLE_BACKGROUND_JOBS` (`false` → jobs run externally) |
| `INFO: Released N expired reservation(s)` | Reservation-expiry sweep ran | None — expected periodic output |
| `INFO: Found N aging pickup(s)` | Aging-pickup alert check ran | Investigate if count > 0 |

### Background Jobs (WIQ-V1-021)

Scheduled work (expired-reservation sweep, aging-pickup admin alerts) runs in-process via APScheduler inside the FastAPI lifespan. Verification emails are dispatched as FastAPI `BackgroundTasks` after the response, so SMTP I/O never blocks request handlers.

| Topic | Detail |
|-------|--------|
| Last-run visibility | `GET /admin/jobs/status` (admin-only) returns the last successful run timestamps for `reservation_sweep` and `aging_pickups` |
| Disabling | Set `ENABLE_BACKGROUND_JOBS=false` (always off in the `test` environment) |
| Tuning | Intervals and thresholds via `RESERVATION_SWEEP_INTERVAL_MINUTES`, `AGING_PICKUP_INTERVAL_MINUTES`, `AGING_PICKUP_THRESHOLD_DAYS` |
| Multi-instance (Celery + Redis) | Each instance runs its own scheduler, which duplicates work on horizontal scale. For N-instance deployments, run scheduled work in a **Celery worker with Celery Beat** (broker: Redis) and set `ENABLE_BACKGROUND_JOBS=false` on the web instances. The job functions are already standalone and idempotent (guarded `UPDATE`s + notification metadata de-duplication), so they can be wrapped as Celery tasks without domain changes; Redis can later also back the in-memory rate limiter. See `docs/SYSTEM_ARCHITECTURE.md §6.9` |

### Uptime Monitoring

Configure an external uptime monitor on the health endpoint:

| Service | Free Tier | Check Interval | Setup |
|---------|-----------|----------------|-------|
| [UptimeRobot](https://uptimerobot.com) | ✅ Up to 50 monitors | 5 minutes | HTTP(S) monitor → `https://api.waste-iq.dev/health` |
| [Better Uptime](https://betteruptime.com) | ✅ 10 monitors | 3 minutes | Same URL |
| [Freshping](https://freshping.io) | ✅ 50 checks | 1 minute | Same URL |

**Alert criteria:**
- HTTP status ≠ 200 → immediate alert
- Response time > 5s → warning alert

### Performance Monitoring

Render.com provides built-in CPU, memory, and request metrics in the dashboard.

**Sentry** (error tracking) is integrated — set `SENTRY_DSN`, `ENVIRONMENT` and `RELEASE` to activate it (see [Monitoring & Logging](#monitoring--logging-wiq-v1-023)).

**Prometheus + Grafana** (metrics): deferred. `prometheus-fastapi-instrumentator` is not installed; the `/metrics` endpoint does not exist by design (see [Monitoring & Logging](#monitoring--logging-wiq-v1-023)).

---

## 9. Backup Strategy

### Automated Backups (Render PostgreSQL)

| Render Plan | Backup Retention | Recovery Type |
|-------------|-----------------|---------------|
| Starter | 7 days daily | Manual restore via Render Dashboard |
| Standard | 30 days daily | Point-in-time recovery |
| Pro | 90 days | Point-in-time recovery |

Access backups: **Render Dashboard → your-database → Backups tab**.

### Manual Backup

Take a manual backup before any major migration or release:

```bash
# Export the full database
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Compress the backup
gzip backup_$(date +%Y%m%d_%H%M%S).sql

# Example with explicit connection string
pg_dump "postgresql://wasteiq:password@db.render.com:5432/wasteiq" > backup_pre_v0.2.0.sql
```

### Manual Restore

```bash
# Restore from a SQL dump
psql $DATABASE_URL < backup_pre_v0.2.0.sql

# If the database has existing data, you may need to drop and recreate first
psql $DATABASE_URL -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
psql $DATABASE_URL < backup_pre_v0.2.0.sql
```

### Backup Frequency Recommendations

| Scenario | Frequency | Method |
|----------|-----------|--------|
| Active production | Daily | Render automatic |
| Before any release | Manual | `pg_dump` |
| Before a major migration | Manual | `pg_dump` |
| Before a destructive data operation | Manual | `pg_dump` |

---

## 10. Rollback Strategy

### Code Rollback

If a deployment breaks production:

```bash
# 1. Identify the last good commit
git log --oneline -10

# 2. Create a revert commit (preferred — keeps history clean)
git revert <bad-commit-sha>
git push origin main

# OR: Hard reset to the last good tag (use with caution)
git reset --hard v0.1.0
git push origin main --force  # ⚠️ Only if you own the main branch exclusively
```

On Render.com, you can also use the **"Rollback to previous deploy"** button in the dashboard without touching Git.

### Database Rollback

```bash
# 1. ALWAYS take a backup first
pg_dump $DATABASE_URL > pre_rollback_backup_$(date +%Y%m%d).sql

# 2. Downgrade one Alembic revision
cd backend
alembic downgrade -1

# 3. Verify the database state
alembic current
```

### Decision Framework

| Situation | Action |
|-----------|--------|
| Code bug (no schema change) | Revert commit or use Render rollback |
| Schema change that is backward-compatible | Forward-fix in a new migration |
| Schema change that broke data integrity | Restore from backup, then forward-fix |
| Critical security vulnerability | Hotfix branch → PR → merge → deploy immediately |
| External service outage (Cloudinary) | App degrades gracefully in development (image_url=null); in production the upload fails with 502 and the request is not created; cancellation cleanup logs and continues without failing the cancellation |

---

## 11. Troubleshooting

### Common Issues

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| **Port 8000 already in use** | Another process is using the port | `lsof -ti:8000 \| xargs kill` (Mac/Linux) or change `--port` in uvicorn command |
| **CORS error in browser** | `CORS_ORIGINS` doesn't exactly match the frontend URL | Check for trailing slash, http vs https, and port mismatches in `CORS_ORIGINS` |
| **401 Unauthorized on all requests** | JWT_SECRET_KEY mismatch between services or token expired | Ensure the same `JWT_SECRET_KEY` is used consistently; check token expiry |
| **Cannot connect to database** | `DATABASE_URL` is wrong or DB is not running | Verify connection string; run `pg_isready -h localhost` |
| **`alembic upgrade head` fails** | Data in the database conflicts with the migration | Review the migration file; may require manual data fixes |
| **Cloudinary upload fails (502)** | Cloudinary service is temporarily unavailable or rejected credentials | Check [status.cloudinary.com](https://status.cloudinary.com) and the Cloudinary credentials; the app returns 502 and the request is not created |
| **Cloudinary upload fails (503)** | Cloudinary credentials not configured in production | Set `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` in production (`ENVIRONMENT=production`) |
| **Frontend blank page after build** | `VITE_API_URL` not set or set to wrong URL | Verify `frontend/.env` or Render environment variable |
| **`npm install` fails** | Node.js version too old or corrupted `node_modules` | Run `node --version` (must be ≥ 20); delete `node_modules` and `package-lock.json`, then `npm install` |
| **`ImportError` on Python startup** | Virtual environment not activated or dependencies not installed | Run `source .venv/bin/activate` then `pip install -r requirements.txt` |
| **`ModuleNotFoundError: app`** | Running uvicorn from the wrong directory | Always run `uvicorn app.main:app` from inside the `backend/` directory |
| **Docker: `port already allocated`** | A container from a previous run is still using the port | `docker compose down` to stop all containers before `docker compose up` |
| **Docker: backend can't reach database** | `DATABASE_URL` uses `localhost` instead of `db` (the Docker service name) | Set `DATABASE_URL=postgresql://wasteiq:wasteiq@db:5432/wasteiq` (note: `@db:` not `@localhost:`) |
| **Admin login doesn't work** | Admin credentials not bootstrapped | Check `backend/.env` for admin email/password settings; check startup logs for bootstrap messages |
| **`alembic current` shows no revision** | Migrations haven't been run yet | Run `alembic upgrade head` |
| **TypeScript errors in frontend** | Types outdated after API changes | Update types in `frontend/src/types/` to match new API schema |

### Getting More Help

1. Check the [GitHub Issues](https://github.com/your-org/waste-iq/issues) for known problems.
2. Search the `backend/` logs (`docker compose logs backend`) for stack traces.
3. Open a new [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md) with the full error output and your environment details.
4. Join the team discussion channel for real-time help.
