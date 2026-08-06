# Waste-IQ AI Engineering Agent

Phase 0 — GitHub App & Webhooks. Receives GitHub webhook events, verifies signatures, and
records every delivery idempotently. No assistants are wired in yet (they arrive in later
increments per `docs/architecture/AI_ENGINEERING_AGENT.md`).

## Manual setup (one-time, documented in architecture §5.1)

1. Create a **GitHub App** at https://github.com/settings/apps/new with:
   - Name: `waste-iq-agent`
   - Webhook URL: `https://<agent-host>/api/webhooks/github`
   - Webhook secret: a strong random value → becomes `AGENT_WEBHOOK_SECRET`
   - Permissions: **Issues** read/write, **Pull requests** read/write, **Contents**
     read (write later, scoped to `agent/*`), **Checks** read, **Metadata** read
   - Subscribe to events: `issues`, `pull_request`, `pull_request_review`,
     `issue_comment`, `push`, `check_run`, `check_suite`, `workflow_run`, `release`
   - Repository access: **Only select repositories** → `waste-iq`
2. Install the app on `Subhajitdas99/waste-iq`; note the **Installation ID** from the
   installation URL.
3. Generate a **private key** in the app settings and store the PEM contents as
   `AGENT_GITHUB_APP_PRIVATE_KEY` (or save to a file and set
   `AGENT_GITHUB_APP_PRIVATE_KEY_PATH`).
4. Copy `agent/.env.example` → `agent/.env` and fill:
   `AGENT_GITHUB_APP_ID`, `AGENT_WEBHOOK_SECRET`, `AGENT_GITHUB_INSTALLATION_ID`,
   plus a strong `AGENT_ADMIN_API_TOKEN`.

## Run locally

```bash
cd agent
python -m pip install -r requirements-dev.txt
uvicorn app.main:app --port 8001
```

Or with Docker Compose from the repo root:

```bash
docker compose up --build agent
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Health + config status |
| POST | `/api/webhooks/github` | GitHub webhook receiver (HMAC-verified) |
| GET | `/api/admin/runs` | Recent processed events (requires `Authorization: Bearer $AGENT_ADMIN_API_TOKEN`) |

## Security invariants (Phase 0)

- Every webhook is verified with HMAC-SHA256 (`X-Hub-Signature-256`).
- Duplicate deliveries (same `X-GitHub-Delivery`) are recorded exactly once.
- The agent holds **no merge capability** and performs zero writes in Phase 0.
- No PATs; the GitHub App uses short-lived installation tokens cached in memory only.

## Quality gates

`ruff check`, `black --check`, `mypy app`, and `pytest --cov=app --cov-fail-under=80`
are enforced by `.github/workflows/agent-ci.yml`.