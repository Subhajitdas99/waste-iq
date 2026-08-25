# ---------------------------------------------------------------------------
# Builder stage: install Python dependencies into an isolated virtualenv.
# All runtime dependencies ship as manylinux wheels (psycopg[binary], bcrypt,
# cryptography, uvloop, httptools), so no compiler toolchain is required.
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .

RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# Runtime stage: slim image without build tooling or pip caches, running as a
# dedicated non-root user.
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

RUN groupadd --gid 1000 wasteiq \
    && useradd --uid 1000 --gid wasteiq --create-home --shell /usr/sbin/nologin wasteiq

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv

# Application code only. Dependencies live in /opt/venv; requirements.txt,
# tests, and local dev artifacts are intentionally not shipped in the image.
COPY --chown=wasteiq:wasteiq alembic.ini ./alembic.ini
COPY --chown=wasteiq:wasteiq alembic ./alembic
COPY --chown=wasteiq:wasteiq app ./app

# Writable directory used by PickupRequestImageService for temporary files
# while processing uploads before they are sent to Cloudinary.
RUN mkdir -p /app/uploads && chown wasteiq:wasteiq /app/uploads

USER wasteiq

EXPOSE 8000

# Migrations run at startup (established deployment pattern), then Uvicorn
# serves the API. PORT is respected for platforms that inject it.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
