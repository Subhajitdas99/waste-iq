import sentry_sdk

from app.core.config import settings


def init_sentry() -> None:
    """Initialize Sentry only if a DSN is configured."""

    if not settings.sentry_enabled:
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        release=settings.release,
    )
