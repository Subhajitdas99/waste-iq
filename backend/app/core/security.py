from datetime import datetime, timedelta, timezone
from hashlib import sha256
from secrets import token_urlsafe
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_TOKEN_TYPE = "access"
VERIFICATION_TOKEN_PURPOSE = "email_verify"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": subject, "type": ACCESS_TOKEN_TYPE, "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc

    subject = payload.get("sub")
    if not subject or payload.get("type") != ACCESS_TOKEN_TYPE:
        raise ValueError("Malformed token")
    return str(subject)


def create_verification_token(subject: str) -> str:
    """Signed, expiring, single-purpose verification token (WIQ-V1-014).

    The token is a JWT signed with the application secret carrying the
    ``purpose`` claim ``"email_verify"`` so tokens cannot be reused for any
    other purpose (e.g. password reset). A random ``jti`` makes every issued
    token unique material. Nothing is stored server-side: single-use
    semantics come from the account state transition it performs
    (``email_verified_at``), after which the token is useless.
    """
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.verification_token_expire_minutes
    )
    payload = {
        "sub": subject,
        "purpose": VERIFICATION_TOKEN_PURPOSE,
        "jti": uuid4().hex,
        "exp": expires_at,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_verification_token(token: str) -> str:
    """Return the subject of a valid, unexpired verification token.

    Raises :class:`ValueError` for malformed, expired, or mis-purposed
    tokens so callers can surface one generic failure response.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Invalid or expired verification token") from exc

    subject = payload.get("sub")
    if not subject or payload.get("purpose") != VERIFICATION_TOKEN_PURPOSE:
        raise ValueError("Invalid or expired verification token")
    return str(subject)


def generate_refresh_token() -> str:
    """Opaque refresh-token secret, issued to the client exactly once.

    384 bits of entropy via ``secrets``; only its SHA-256 digest is stored
    server-side, so a database leak does not expose usable tokens.
    """
    return token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()
