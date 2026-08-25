import logging

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from app.core.config import settings

logger = logging.getLogger(__name__)


def init_sentry() -> None:
    """Initialize Sentry only if a DSN is configured.

    Without ``SENTRY_DSN`` the SDK stays completely disabled and no network
    calls are possible. ``send_default_pii`` remains off, so request bodies,
    cookies and user emails are never reported; only the authenticated user's
    opaque numeric id is attached as context (see :func:`set_sentry_user`).
    """

    if not settings.sentry_enabled:
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        release=settings.release,
        # Explicit so route exceptions are captured even if default
        # integrations ever change; both ship with sentry-sdk[fastapi].
        integrations=[StarletteIntegration(), FastApiIntegration()],
    )
    logger.info(
        "Sentry initialized (environment=%s release=%s)",
        settings.environment,
        settings.release,
    )


def set_sentry_user(user_id: int | None) -> None:
    """Attach the authenticated user's id to the current Sentry scope.

    Safe no-op when Sentry is disabled or when no user resolved. Only the
    stringified id is reported — never tokens, emails or other PII.
    """

    if not settings.sentry_enabled or user_id is None:
        return

    sentry_sdk.set_user({"id": str(user_id)})
