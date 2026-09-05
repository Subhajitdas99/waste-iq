"""PostgreSQL-specific conftest for WIQ-V1-053 concurrency verification.

This conftest overrides the parent conftest's SQLite default to point at the
PostgreSQL instance configured through the environment. It is intentionally
opt-in: only tests under ``tests/postgres/`` load this file.
"""

import os

url: str = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL") or ""

if not url.startswith("postgresql"):
    raise RuntimeError("PostgreSQL tests require a PostgreSQL connection string.")

os.environ["DATABASE_URL"] = url
os.environ["ENVIRONMENT"] = "test"
os.environ.setdefault("SENTRY_DSN", "")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")
os.environ.setdefault("ADMIN_REGISTRATION_CODE", "test-admin-code")

from app.core.config import get_settings  # noqa: E402

# ``get_settings`` is wrapped in ``lru_cache``. Clear the cache after updating
# the environment so PostgreSQL tests cannot reuse settings created earlier
# with the SQLite DATABASE_URL.
get_settings.cache_clear()
