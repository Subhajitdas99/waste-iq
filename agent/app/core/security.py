import hashlib
import hmac

_SHA256_PREFIX = "sha256="


def verify_webhook_signature(payload: bytes, signature_header: str | None, secret: str) -> bool:
    """Verify the GitHub webhook HMAC-SHA256 signature (X-Hub-Signature-256)."""
    if not signature_header or not secret:
        return False
    if not signature_header.lower().startswith(_SHA256_PREFIX):
        return False
    received = signature_header[len(_SHA256_PREFIX) :]
    expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(received, expected)


def compute_webhook_signature(payload: bytes, secret: str) -> str:
    """Compute the signature header value for a payload (used in tests)."""
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return f"{_SHA256_PREFIX}{digest}"
