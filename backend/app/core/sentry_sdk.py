import sentry_sdk

from app.core.config import settings


def init_sentry() -> None:
    """Initialize Sentry only if a DSN is configured."""

    dsn = getattr(settings, "sentry_dsn", None)

    if not dsn:
        return

    sentry_sdk.init(
        dsn=dsn,
        environment=getattr(settings, "environment", "development"),
        release=getattr(settings, "release", None),
    )