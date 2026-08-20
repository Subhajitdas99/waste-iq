"""Email delivery abstraction (WIQ-V1-014).

Design notes
------------
- Providers implement :class:`EmailProvider`. The console backend captures
  messages in the in-process ``email_outbox`` (deterministic for tests and
  local development) and logs only a redacted summary — the rendered body,
  which contains the verification link and its token, is never written to
  application logs. The SMTP backend delivers over the network and is
  configured exclusively through environment variables; credentials are
  never logged and never part of raised exceptions.
- Template rendering uses Jinja2 from ``app/services/templates``.
- Tests must not depend on a real external provider: ``EMAIL_BACKEND``
  defaults to ``console``, which is what the test environment uses.
"""

from __future__ import annotations

import logging
import smtplib
import ssl
from abc import ABC, abstractmethod
from dataclasses import dataclass
from email.message import EmailMessage as MimeMessage
from pathlib import Path
from urllib.parse import urlencode

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

_TEMPLATE_ENV = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html"]),
)


class EmailDeliveryError(RuntimeError):
    """Raised when the configured provider cannot deliver an email."""


@dataclass(frozen=True)
class OutgoingEmail:
    to_email: str
    subject: str
    html_body: str
    text_body: str


class EmailProvider(ABC):
    name: str

    @abstractmethod
    def send(self, message: OutgoingEmail) -> None:
        """Deliver ``message`` or raise :class:`EmailDeliveryError`."""


# In-process capture target for the console backend. Tests and local
# development read the last messages from here; production (SMTP) never
# touches it.
email_outbox: list[OutgoingEmail] = []


def clear_email_outbox() -> None:
    email_outbox.clear()


class ConsoleEmailProvider(EmailProvider):
    """Development/test backend: capture into ``email_outbox``.

    Only a redacted summary (recipient + subject) is logged; the body — and
    with it the verification link and its token — never reaches logs.
    """

    name = "console"

    def send(self, message: OutgoingEmail) -> None:
        email_outbox.append(message)
        logger.info(
            "Email delivery (console backend): to=%s subject=%r", message.to_email, message.subject
        )


class SmtpEmailProvider(EmailProvider):
    """SMTP backend for staging/production.

    Credentials come from settings only. The password is never logged and
    never embedded in raised exceptions.
    """

    name = "smtp"

    def __init__(
        self,
        *,
        host: str,
        port: int,
        user: str | None,
        password: str | None,
        use_tls: bool,
        from_email: str,
        from_name: str,
    ) -> None:
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._use_tls = use_tls
        self._from_email = from_email
        self._from_name = from_name

    def send(self, message: OutgoingEmail) -> None:
        mime = MimeMessage()
        mime["Subject"] = message.subject
        mime["From"] = f"{self._from_name} <{self._from_email}>"
        mime["To"] = message.to_email
        mime.set_content(message.text_body)
        mime.add_alternative(message.html_body, subtype="html")

        try:
            with smtplib.SMTP(self._host, self._port, timeout=30) as server:
                if self._use_tls:
                    server.starttls(context=ssl.create_default_context())
                if self._user and self._password:
                    server.login(self._user, self._password)
                server.send_message(mime)
        except (OSError, smtplib.SMTPException) as exc:
            raise EmailDeliveryError(f"Failed to deliver email to {message.to_email}") from exc


def get_email_provider() -> EmailProvider:
    """Return the provider selected by ``EMAIL_BACKEND``.

    The SMTP provider is constructed per call so a misconfiguration raises
    :class:`EmailDeliveryError` at delivery time (caught and logged by
    callers) instead of failing application startup.
    """
    if settings.email_backend == "smtp":
        if not settings.smtp_host or not settings.email_from:
            raise EmailDeliveryError(
                "EMAIL_BACKEND=smtp requires SMTP_HOST and EMAIL_FROM to be configured"
            )
        return SmtpEmailProvider(
            host=settings.smtp_host,
            port=settings.smtp_port,
            user=settings.smtp_user,
            password=settings.smtp_password,
            use_tls=settings.smtp_use_tls,
            from_email=settings.email_from,
            from_name=settings.email_from_name,
        )
    return ConsoleEmailProvider()


def send_email(message: OutgoingEmail) -> None:
    get_email_provider().send(message)


def build_verification_link(token: str) -> str:
    """Absolute link to the frontend's verify-email page."""
    base_url = settings.frontend_url.rstrip("/")
    return f"{base_url}/verify-email?{urlencode({'token': token})}"


def send_verification_email(user: User, token: str) -> None:
    """Render and deliver the verification email for ``user``.

    Raises :class:`EmailDeliveryError` when the configured provider cannot
    deliver; the token is part of the rendered link only and never logged.
    """
    verification_url = build_verification_link(token)
    expires_in_hours = max(1, -(-settings.verification_token_expire_minutes // 60))

    html_body = _TEMPLATE_ENV.get_template("verification_email.html").render(
        name=user.name,
        verification_url=verification_url,
        expires_in_hours=expires_in_hours,
    )
    text_body = (
        f"Hi {user.name},\n\n"
        f"Welcome to Waste-IQ! Verify your email address by opening this link:\n"
        f"{verification_url}\n\n"
        f"The link expires in {expires_in_hours} hour(s). If you did not create "
        "a Waste-IQ account, you can safely ignore this email."
    )

    send_email(
        OutgoingEmail(
            to_email=user.email,
            subject="Verify your Waste-IQ email address",
            html_body=html_body,
            text_body=text_body,
        )
    )
