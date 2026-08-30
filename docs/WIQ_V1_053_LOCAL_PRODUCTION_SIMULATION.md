# WIQ-V1-053 / WIQ-V1-054 — Local Production Simulation

This document describes the **local production simulation** for Waste-IQ
V1, the `DEPLOYMENT_MODE` security boundary, and the local filesystem
image storage fallback.

The work spans two issues:

- **WIQ-V1-053 — Local Production Simulation.** Hardens the Docker
  Compose stack for a production-like local deployment.
- **WIQ-V1-054 — Local Image Storage Fallback.** Adds the
  `DEPLOYMENT_MODE` security gate and a local filesystem uploader.

---

## 1. Why a Local Production Simulation?

The base `docker-compose.yml` is development-friendly. The local
production simulation closes the configuration gap: it uses the same
image, same migrations, same FastAPI process, and the same `/health`
endpoints -- only the configuration layer changes.

Key differences:

- secrets come from the orchestrating environment, not `backend/.env`;
- PostgreSQL is internal to the compose network;
- required variables fail fast at config-parse time;
- the `uploads_data` named volume persists simulated image uploads;
- the dev-only `agent` service is hidden behind the `dev` profile.

---

## 2. Architecture

Two-file Compose override: `docker-compose.yml` (base) plus
`docker-compose.prod.yml` (override).

```
+-----------------------------------------------------------------+
|        docker-compose.yml  +  docker-compose.prod.yml           |
+-----------------------------------------------------------------+
|                                                                 |
|   +-----------------+        +-------------------------+        |
|   |       db        | -----> |        backend          |        |
|   |  postgres:16-   |        |  (runtime target)      |        |
|   |  alpine         |        |  volume: uploads_data  |        |
|   |  (internal only)|        |    -> /app/uploads     |        |
|   +-----------------+        +-------------------------+        |
|                                                                 |
|   +-------------------------+                                   |
|   |       frontend          |                                   |
|   |  (Nginx, VITE_* baked)|                                   |
|   +-------------------------+                                   |
|                                                                 |
|   dev-only `agent` service: profiles: [dev]                    |
+-----------------------------------------------------------------+
```

| Service    | Image / Build           | Internal port | Host port | Healthcheck                                        |
| ---------- | ----------------------- | ------------- | --------- | ------------------------------------------------- |
| `db`       | `postgres:16-alpine`    | 5432          | none      | `pg_isready -U wasteiq -d wasteiq`                |
| `backend`  | `./backend` (`runtime`) | 8000          | 8000      | HTTP GET `/health/ready` inside container         |
| `frontend` | `./frontend` (Nginx)    | 80            | 8080      | `wget http://127.0.0.1/health`                    |
| `agent`    | `./agent`               | 8001          | 8001      | none (dev-only, profile `dev`)                    |

Startup is health-gated: `db` (healthy) -> `backend` runs
`alembic upgrade head` -> (healthy) -> `frontend`.

---

## 3. Prerequisites

| Tool           | Minimum version | Check command           |
| -------------- | --------------- | ---------------------- |
| Docker Engine  | 24+             | `docker --version`      |
| Docker Compose | v2.24+          | `docker compose version` |

`v2.24+` is required for the `!reset` override syntax.

---

## 4. Environment Configuration

Variables come from the shell environment **or** a project-root `.env`
(git-ignored). Required variables fail fast at config-parse time.

### 4.1 Required variables

```bash
POSTGRES_PASSWORD=<strong random password>        # openssl rand -hex 24
JWT_SECRET_KEY=<strong random secret, >=32 chars>  # openssl rand -hex 32
CORS_ORIGINS=https://your-frontend-domain         # comma-separated, exact match
FRONTEND_URL=https://your-frontend-domain          # used to build verification links
```

### 4.2 Recommended for the local simulation

```bash
DEPLOYMENT_MODE=local-simulation                  # CRITICAL: enables the WIQ-V1-054 fallback
LOCAL_IMAGE_STORAGE_ENABLED=true                 # opt into the local filesystem uploader
LOCAL_IMAGE_STORAGE_DIR=/app/uploads              # default; backed by uploads_data volume
LOCAL_IMAGE_STORAGE_URL_PREFIX=/uploads          # default; served by FastAPI StaticFiles
VITE_API_URL=http://localhost:8000               # baked into the frontend bundle
BACKEND_PORT=8000
FRONTEND_PORT=8080
EMAIL_BACKEND=console                            # writes to logs + in-process outbox
LOG_LEVEL=INFO
```

### 4.3 Real production only (leave empty in simulation)

```bash
# Real production only:
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
# (When DEPLOYMENT_MODE=local-simulation + LOCAL_IMAGE_STORAGE_ENABLED=true,
#  Cloudinary is not used and may be empty.)
```

### 4.4 Example project-root `.env`

```bash
# Waste-IQ Local Production Simulation - .env (git-ignored)
# DO NOT COMMIT THIS FILE.

POSTGRES_DB=wasteiq
POSTGRES_USER=wasteiq
POSTGRES_PASSWORD=<openssl rand -hex 24>
JWT_SECRET_KEY=<openssl rand -hex 32>

CORS_ORIGINS=http://localhost:8080
FRONTEND_URL=http://localhost:8080
VITE_API_URL=http://localhost:8000

# WIQ-V1-054 local image storage fallback
DEPLOYMENT_MODE=local-simulation
LOCAL_IMAGE_STORAGE_ENABLED=true

# Email: console backend writes to the backend container logs
EMAIL_BACKEND=console

# Bootstrap admin (optional)
ADMIN_REGISTRATION_CODE=<your-code>
BOOTSTRAP_ADMIN_NAME=Admin
BOOTSTRAP_ADMIN_EMAIL=admin@wasteiq.local
BOOTSTRAP_ADMIN_PASSWORD=<openssl rand -hex 16>
```

### 4.5 Validate the rendered configuration

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml config
```

A successful run prints the resolved YAML and exits 0. A missing
required variable prints something like
`Error: POSTGRES_PASSWORD must be set` and exits non-zero.

---

## 5. Running the Stack

### 5.1 Build the images

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml build
```

### 5.2 Start the stack

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 5.3 Verify all services are healthy

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

Wait until all three services report `(healthy)`:

```
NAME                IMAGE               SERVICE    STATUS                PORTS
wasteiq-db-1        postgres:16-alpine  db         Up (healthy)          5432/tcp
wasteiq-backend-1   wasteiq-backend     backend    Up (healthy)          0.0.0.0:8000->8000/tcp
wasteiq-frontend-1  wasteiq-frontend    frontend   Up (healthy)          0.0.0.0:8080->80/tcp
```

### 5.4 Useful commands

```bash
# Tail backend logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f backend

# Tail PostgreSQL logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f db

# Open a psql shell
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec db \
    psql -U wasteiq -d wasteiq

# Stop the stack (keep volumes)
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# Stop and remove volumes (destructive)
docker compose -f docker-compose.yml -f docker-compose.prod.yml down -v

# Rebuild a single service
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build backend
```

---

## 6. PostgreSQL and Alembic Migration Validation

The backend image runs `alembic upgrade head` automatically before
binding to port 8000:

```dockerfile
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

### 6.1 Inspect the migration history

```bash
# Applied revision
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend \
    alembic current

# Full migration history
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend \
    alembic history --verbose
```

### 6.2 Sanity checks

```bash
# Confirm the database accepts connections
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec db \
    pg_isready -U wasteiq -d wasteiq

# List tables
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec db \
    psql -U wasteiq -d wasteiq -c '\dt'
```

A migration failure causes the backend container to exit. The restart
policy retries it; investigate the underlying cause.

### 6.3 CI coverage

`backend/tests/test_production_config.py` asserts the production
override fails fast at config-parse time when required variables are
missing (`POSTGRES_PASSWORD`, `JWT_SECRET_KEY`, `CORS_ORIGINS`,
`FRONTEND_URL`), validates the rendered `DATABASE_URL` uses
`postgresql+psycopg://` (not `sqlite:///`), and verifies
`CORS_ORIGINS` and `FRONTEND_URL` propagate verbatim.

---

## 7. Health and Readiness

| Probe               | Code path                  | Verifies                                      | Result codes |
| ------------------- | -------------------------- | --------------------------------------------- | ------------ |
| `GET /health`       | `app.main.healthcheck`     | Process is up; reports `cors_origins`         | 200 (always) |
| `GET /health/ready` | `app.main.readiness_check` | Database reachable + image storage configured   | 200 / 503    |

### 7.1 `/health`

```bash
curl -fsS http://localhost:8000/health
# {"status":"ok","app":"Waste-IQ API","cors_origins":["http://localhost:8080"]}
```

Always returns `200`. Suitable for liveness probes.

### 7.2 `/health/ready`

```bash
curl -fsS http://localhost:8000/health/ready
# {"status":"ready","app":"Waste-IQ API"}
```

Returns `200` only when:

1. The database is reachable (`SELECT 1` succeeds).
2. `cloudinary_required` is satisfied. In the local simulation,
   `DEPLOYMENT_MODE=local-simulation` makes `cloudinary_required`
   `False`, so the probe passes without Cloudinary credentials when
   `LOCAL_IMAGE_STORAGE_ENABLED=true`.

Returns `503` in these cases:

| Reason                      | Trigger                                                |
| --------------------------- | ------------------------------------------------------ |
| `database_unreachable`      | `SELECT 1` raises any exception                        |
| `cloudinary_not_configured` | `deployment_mode=production` with no Cloudinary config  |
| (implicit) uploader missing | Any uncaught exception during readiness                 |

### 7.3 Docker healthcheck

The Compose `healthcheck` for `backend` hits `/health/ready`
**inside** the container:

```yaml
test: ["CMD", "python", "-c",
       "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/ready', timeout=5)"]
```

`/health/ready` covers both process liveness and database connectivity,
so `docker compose ps` correctly reports `Up (healthy)` only when
both succeed.

---

## 8. Production Smoke-Test Checklist

Run after every stack bring-up. Use a **throwaway account**.

```bash
API=http://localhost:8000

# 1. Liveness
curl -fsS "$API/health"

# 2. Readiness
curl -fsS "$API/health/ready"

# 3. Registration
curl -fsS -X POST "$API/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"name":"Smoke Test","email":"smoke-test@example.com","phone":"+10000000000","password":"Str0ngPassw0rd!","role":"citizen"}'

# 4. Login
curl -fsS -X POST "$API/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"smoke-test@example.com","password":"Str0ngPassw0rd!"}'
```

| # | Check                                         | Expected                  | Result  |
| - | --------------------------------------------- | ------------------------- | ------- |
| 1 | Liveness                                      | `200 {"status":"ok"}`     | [PASS]  |
| 2 | Readiness                                     | `200 {"status":"ready"}`  | [PASS]  |
| 3 | Register a throwaway citizen                  | `201` + tokens            | [PASS]  |
| 4 | Log in as the throwaway citizen               | `200` + tokens            | [PASS]  |
| 5 | Create a pickup request with a waste photo    | `201` + `image_url`       | [PASS]  |
| 6 | Fetch the photo at the returned URL           | `200`, image bytes        | [PASS]  |
| 7 | Cancel the pickup                             | `200`, image removed      | [PASS]  |
| 8 | Re-fetch the photo URL                        | `404` (idempotent)        | [PASS]  |

---

## 9. Email Testing (Console Backend)

The simulation defaults to `EMAIL_BACKEND=console`, which writes a
**redacted delivery summary** to the backend container logs.

### 9.1 What is captured

```json
{"timestamp":"...","level":"INFO","logger":"app.services.email",
 "message":"Email delivered (console backend)",
 "request_id":"...","event":"email_console",
 "to":"s*****@example.com","subject":"Verify your Waste-IQ email",
 "template":"email_verification","outbox_size":1}
```

The `to` field is **always redacted**; the full address is never logged.

### 9.2 Inspect the outbox

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs backend | \
    grep '"event":"email_console"'
```

### 9.3 Switching to real SMTP

```bash
EMAIL_BACKEND=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=<app-password>
SMTP_USE_TLS=true
EMAIL_FROM=your-email@gmail.com
EMAIL_FROM_NAME="Waste-IQ"
```

Verification emails are dispatched as FastAPI `BackgroundTasks`, so
SMTP I/O never blocks request handlers.

---

## 10. PostgreSQL Backup and Restore

### 10.1 Manual backup

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T db \
    pg_dump -U wasteiq -d wasteiq \
    > "backup_$(date +%Y%m%d_%H%M%S).sql"

gzip "backup_$(date +%Y%m%d_%H%M%S).sql"
```

### 10.2 Manual restore

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml stop backend

gunzip -c backup_20260828_120000.sql.gz | \
    docker compose -f docker-compose.yml -f docker-compose.prod.yml exec -T db \
        psql -U wasteiq -d wasteiq

docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## 11. Troubleshooting

| Problem                                                 | Likely cause                                              | Resolution                                                                   |
| ------------------------------------------------------- | --------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `compose config` exits non-zero                         | Required env var missing                                  | Re-render with `docker compose ... config`; supply the missing variable        |
| `db` stays `(health: starting)`                         | `POSTGRES_PASSWORD` is empty / placeholder                | Set a real password via `openssl rand -hex 24`                                |
| `backend` restart loop on startup                       | Migration failure (`alembic upgrade head` errored)          | Read backend logs; restore from backup if needed                               |
| `/health/ready` returns 503 `cloudinary_not_configured` | `DEPLOYMENT_MODE=production` with no Cloudinary in env    | For simulation: `DEPLOYMENT_MODE=local-simulation` + enable local fallback; for production: set `CLOUDINARY_*` |
| Browser shows CORS error                                | `CORS_ORIGINS` does not exactly match `FRONTEND_URL`     | Compare trailing slash, scheme, and port                                      |
| 401 on `/auth/login` for a freshly registered user      | User email not yet verified                               | Simulation console backend shows the verification link; real SMTP for production |
| Image upload returns 503                                | Simulation without `LOCAL_IMAGE_STORAGE_ENABLED=true` + no Cloudinary | Set `LOCAL_IMAGE_STORAGE_ENABLED=true` in `.env` and rebuild  |
| Frontend bundle hits wrong backend                      | `VITE_API_URL` was wrong at build time                    | Rebuild the frontend (`docker compose ... build frontend`)                     |
| `uploads_data` volume grows unbounded                   | Local simulation stores every upload                        | Prune with `docker volume rm wasteiq_uploads_data` between runs               |

### 11.1 Inspecting the running configuration

```bash
# Rendered Compose config (env vars resolved)
docker compose -f docker-compose.yml -f docker-compose.prod.yml config

# Environment seen by the backend container
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend env
```

---

## 12. Limitations of the Local Simulation

- **No TLS.** The frontend talks to the backend over plain HTTP.
- **No horizontal scaling.** APScheduler runs in-process; `--scale backend=N`
  duplicates scheduled work.
- **No SMTP relay by default.** Messages are lost on container restart.
- **Local filesystem image storage is not durable.** `uploads_data` is a
  single-host Docker volume. Real production uses Cloudinary.
- **No observability stack.** Logs must be read with `docker compose logs`.
- **Single-region, single-host.** Real production spans at least two
  availability zones.

---

## 13. Future Real Deployment (Railway / Render / Vercel)

The local simulation is the rehearsal; the real deployment is the show.
The configuration shape is identical; only the secret sources and the
deployment surface change.

### 13.1 Railway (recommended target)

- One **PostgreSQL** service (managed).
- One **backend** service (`./backend/Dockerfile`, `target: runtime`).
- One **frontend** service (Vite build args baked in).
- Environment variables:
  - `DEPLOYMENT_MODE=production` (CRITICAL).
  - `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`,
    `CLOUDINARY_API_SECRET` -- all three required.
  - `LOCAL_IMAGE_STORAGE_ENABLED` -- **leave at the default `false`**.
  - `DATABASE_URL` -- Railway injects from the PostgreSQL service.
  - `JWT_SECRET_KEY`, `POSTGRES_PASSWORD`, `CORS_ORIGINS`,
    `FRONTEND_URL`, `EMAIL_BACKEND`, `SMTP_*`, `SENTRY_DSN`, etc.
- Remove the `uploads_data` volume mount; Cloudinary is the durable
  image store in production.
- Set up a managed PostgreSQL backup schedule.

### 13.2 Render

Same shape as Railway. `render.yaml` at the project root captures the
infrastructure-as-code. Never run more than one backend replica with
`ENABLE_BACKGROUND_JOBS=true`.

### 13.3 Vercel (frontend only)

Build the frontend with `npm run build`; publish `dist/` as a static
site. `VITE_API_URL` must point at the production backend domain.
CORS on the backend must allow the Vercel origin.

### 13.4 The single most important switch

When moving from the simulation to real production:

```bash
DEPLOYMENT_MODE=production
```

This is the **security gate** from WIQ-V1-054. With this value:

- `LOCAL_IMAGE_STORAGE_ENABLED=true` is **ignored**.
- `cloudinary_required` returns `True`; `/health/ready` returns 503
  unless `CLOUDINARY_*` are set.
- The `/uploads` StaticFiles mount is **not** created.
- Cloudinary is the only image storage path.

---

## 14. WIQ-V1-054 Local Image Storage Fallback

The fallback lets the local production simulation accept image uploads
without a Cloudinary account. It is opt-in, gated, and **never usable
in real production**.

### 14.1 The `DEPLOYMENT_MODE` security boundary

`DEPLOYMENT_MODE` is separate from `ENVIRONMENT`. It is the explicit
answer to "what kind of deployment is this?":

| `DEPLOYMENT_MODE`  | Meaning                                                      | Cloudinary          | Local fallback |
| ------------------ | ------------------------------------------------------------ | ------------------- | -------------- |
| `development`      | Local development without Docker.                             | Optional            | Always off     |
| `local-simulation` | Docker Compose stack shipped with the repo (this simulation). | Optional            | Opt-in         |
| `production`       | Real production (Railway, Render, own host, etc.).          | **Mandatory**       | **Ignored**    |

The boundary is enforced in code, not by convention:

```python
@property
def cloudinary_required(self) -> bool:
    return self.deployment_mode == "production"

@property
def local_image_storage_active(self) -> bool:
    if self.deployment_mode != "local-simulation":
        return False
    if not self.local_image_storage_enabled:
        return False
    if self.cloudinary_configured:
        return False
    return True
```

### 14.2 Behaviour matrix

Enforced by `backend/tests/test_local_image_storage_config.py` and
`backend/tests/test_health.py`:

| `DEPLOYMENT_MODE`  | `LOCAL_IMAGE_STORAGE_ENABLED` | `CLOUDINARY_*` set? | `cloudinary_required` | `local_image_storage_active` | `/health/ready`     | Selected uploader          |
| ------------------ | ----------------------------- | ------------------- | --------------------- | ---------------------------- | ------------------- | -------------------------- |
| `production`       | `true`                        | no                  | `True`                | `False`                      | 503                 | n/a (not ready)            |
| `production`       | `true`                        | yes                 | `True`                | `False`                      | 200                 | CloudinaryUploader         |
| `production`       | `false`                       | no                  | `True`                | `False`                      | 503                 | n/a (not ready)            |
| `production`       | `false`                       | yes                 | `True`                | `False`                      | 200                 | CloudinaryUploader         |
| `local-simulation` | `true`                        | no                  | `False`               | `True`                       | 200                 | LocalFileUploader          |
| `local-simulation` | `true`                        | yes                 | `False`               | `False`                      | 200                 | CloudinaryUploader (wins)  |
| `local-simulation` | `false`                       | no                  | `False`               | `False`                      | 200                 | n/a (uploader skipped)     |
| `development`      | `true`                        | no                  | `False`               | `False`                      | 200                 | n/a (uploader skipped)     |
| `development`      | `false`                       | no                  | `False`               | `False`                      | 200                 | n/a (uploader skipped)     |

### 14.3 Cloudinary precedence

When both Cloudinary and the local fallback are configured, **Cloudinary
always wins**. The selection in `app.core.dependencies.get_image_uploader`:

```
1. Cloudinary (if configured)
2. LocalFileUploader (only when local_image_storage_active is True)
3. Cloudinary uploader with no credentials (raises on upload if required)
```

A developer with a Cloudinary account can run the simulation stack
without disabling their account.

### 14.4 Production Cloudinary requirement

`DEPLOYMENT_MODE=production` makes Cloudinary mandatory:

- `cloudinary_required` returns `True`.
- `/health/ready` returns `503 {"reason":"cloudinary_not_configured"}`
  unless all three `CLOUDINARY_*` variables are set.
- The `/uploads` StaticFiles mount is **never** created.
- `LocalFileUploader` is **never** instantiated.
- An upload attempt with no Cloudinary raises
  `ImageUploadConfigurationError` (rendered as `503`), not silent
  fallback.

`LOCAL_IMAGE_STORAGE_ENABLED=true` does **not** weaken this. The
production-mode override is a hard gate.

### 14.5 Local simulation behavior

When running with `DEPLOYMENT_MODE=local-simulation` and
`LOCAL_IMAGE_STORAGE_ENABLED=true`:

- `cloudinary_required` is `False`.
- `local_image_storage_active` is `True` (unless Cloudinary is also
  configured).
- `/health/ready` returns 200 without Cloudinary.
- Uploads go to `LocalFileUploader`, which moves the file into
  `LOCAL_IMAGE_STORAGE_DIR` (default `/app/uploads`) under
  `pickups/{user_id}/{uuid}.{ext}`.
- The returned `image_url` is a relative URL such as
  `/uploads/pickups/42/9f8c1a2b...png`. The frontend renders it
  directly because the same backend serves it through
  `app.mount("/uploads", StaticFiles(...))`.
- The persisted `image_public_id` matches the Cloudinary format
  (`pickups/{user_id}/{uuid}`), so the database reference is
  interchangeable across providers.
- Cancellation deletes the file from the volume via
  `LocalFileUploader.delete_image`, with the same idempotent
  semantics as Cloudinary.

### 14.6 The `uploads_data` Docker volume

`docker-compose.prod.yml` mounts the named volume `uploads_data` at
`/app/uploads`:

```yaml
volumes:
  - uploads_data:/app/uploads
```

Files written to `/app/uploads` are stored on the named volume, not
the container writable layer. Container replacement preserves in-flight
uploads.

To inspect volume contents:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend \
    ls -la /app/uploads/pickups
```

To reset the volume:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml down -v
docker volume rm wasteiq_uploads_data
```

### 14.7 Backend wiring

| Concern                              | Where                                                          |
| ------------------------------------ | -------------------------------------------------------------- |
| `DEPLOYMENT_MODE` field              | `backend/app/core/config.py` (`Settings.deployment_mode`)       |
| `cloudinary_required` property       | `backend/app/core/config.py`                                   |
| `local_image_storage_active` property | `backend/app/core/config.py`                                   |
| Uploader selection                   | `backend/app/core/dependencies.py` (`get_image_uploader`)     |
| StaticFiles mount                    | `backend/app/main.py` (conditional on `local_image_storage_active`) |
| Readiness check                      | `backend/app/main.py` (`/health/ready`)                        |
| LocalFileUploader class              | `backend/app/services/upload.py`                               |
| Production config tests               | `backend/tests/test_production_config.py`                       |
| Local storage config tests            | `backend/tests/test_local_image_storage_config.py`               |
| Health + boundary tests              | `backend/tests/test_health.py`                                 |
| Pickup upload tests                  | `backend/tests/test_pickup_request_uploads.py`                  |

---

## 15. Validation Results

### 15.1 Test suite

| Test file                            | What it covers                                                               |
| ------------------------------------ | ----------------------------------------------------------------------------- |
| `test_production_config.py`           | Fail-fast at config-parse time; PostgreSQL URL; CORS; FRONTEND_URL            |
| `test_local_image_storage_config.py`  | `cloudinary_required` and `local_image_storage_active` in all 9 modes        |
| `test_health.py`                     | `/health`, `/health/ready` with DB down, Cloudinary required, local fallback  |
| `test_pickup_request_uploads.py`     | Full pickup image lifecycle with `LocalFileUploader` (upload, serve, cancel)   |
| `test_pickup_request_image_service.py`| Image service orchestration; CloudinaryUploader unit; cleanup idempotency     |

### 15.2 Core security boundary assertions

| Assertion                                                                  | Test                                                         |
| ------------------------------------------------------------------------- | ------------------------------------------------------------ |
| `deployment_mode=production` always requires Cloudinary                   | `test_production_cloudinary_required`                        |
| `deployment_mode=production` ignores `LOCAL_IMAGE_STORAGE_ENABLED=true`   | `test_production_cloudinary_required_even_with_fallback_flag` |
| `deployment_mode=local-simulation` with fallback enabled passes readiness | `test_local_simulation_cloudinary_not_required`              |
| Cloudinary always wins when configured (even in simulation)               | `test_local_simulation_cloudinary_wins_over_fallback`        |
| `/health/ready` returns 503 when `production` without Cloudinary          | `test_readiness_production_fails_without_cloudinary`         |
| `/health/ready` returns 200 when `local-simulation` + fallback + no cloud | `test_readiness_local_simulation_ready_when_fallback_enabled` |
| `development` never activates local storage                               | `test_development_fallback_flag_ignored`                      |
| LocalFileUploader stores files in `pickups/{user_id}/{uuid}.{ext}`        | `test_upload_image_stores_file_and_returns_url`              |
| LocalFileUploader.delete_image is idempotent for missing files             | `test_delete_image_idempotent_for_missing_file`               |
| Cancellation removes the stored file                                       | `test_local_storage_cancel_deletes_local_file`                |

### 15.3 Expected CI result

```
backend/tests/test_production_config.py        ::test_compose_config_succeeds_with_required_vars           [PASS]
backend/tests/test_production_config.py        ::test_compose_config_fails_without_postgres_password     [PASS]
backend/tests/test_production_config.py        ::test_compose_config_fails_without_jwt_secret            [PASS]
backend/tests/test_production_config.py        ::test_compose_config_fails_without_cors_origins         [PASS]
backend/tests/test_production_config.py        ::test_compose_config_fails_without_frontend_url          [PASS]
backend/tests/test_production_config.py        ::test_compose_config_validates_postgresql_database_url   [PASS]
backend/tests/test_local_image_storage_config.py ::test_production_cloudinary_required                  [PASS]
backend/tests/test_local_image_storage_config.py ::test_production_cloudinary_required_even_with_fallback_flag [PASS]
backend/tests/test_local_image_storage_config.py ::test_local_simulation_cloudinary_not_required          [PASS]
backend/tests/test_local_image_storage_config.py ::test_local_simulation_local_storage_active_when_fallback_enabled [PASS]
backend/tests/test_local_image_storage_config.py ::test_local_simulation_cloudinary_wins_over_fallback   [PASS]
backend/tests/test_local_image_storage_config.py ::test_cloudinary_configured_requires_all_three_fields [PASS]
backend/tests/test_health.py ::test_health_returns_200                                          [PASS]
backend/tests/test_health.py ::test_health_response_shape                                       [PASS]
backend/tests/test_health.py ::test_readiness_returns_200_when_database_is_available            [PASS]
backend/tests/test_health.py ::test_readiness_returns_503_when_database_is_unavailable           [PASS]
backend/tests/test_health.py ::test_readiness_production_ready_when_cloudinary_configured       [PASS]
backend/tests/test_health.py ::test_readiness_production_fails_without_cloudinary_configuration [PASS]
backend/tests/test_health.py ::test_readiness_local_simulation_ready_when_fallback_enabled       [PASS]
backend/tests/test_health.py ::test_readiness_production_never_ready_with_fallback              [PASS]
backend/tests/test_pickup_request_uploads.py ::test_local_storage_simulation_ready_health        [PASS]
backend/tests/test_pickup_request_uploads.py ::test_local_storage_fallback_is_ignored           [PASS]
backend/tests/test_pickup_request_uploads.py ::test_local_storage_upload_returns_local_url      [PASS]
backend/tests/test_pickup_request_uploads.py ::test_local_storage_upload_without_user_succeeds  [PASS]
backend/tests/test_pickup_request_uploads.py ::test_local_storage_cancel_deletes_local_file      [PASS]
backend/tests/test_pickup_request_uploads.py ::test_production_without_fallback_still_requires_cloudinary [PASS]
```

### 15.4 Markdown and encoding

- All characters are UTF-8.
- No mojibake sequences (`ΓÇ`, `â€`, `â”`, `âœ`, `âŒ`, `Γ£`).
- ASCII-safe diagrams: `+---+` boxes, `| |` columns, `->` arrows.
- Status indicators: `[PASS]`, `[FAIL]`, `[WARN]` only.
- Em dash avoided in code/paths; `--` used for CLI flags.
- Ellipsis replaced with `...`.
