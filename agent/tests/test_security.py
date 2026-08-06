from app.core.security import compute_webhook_signature, verify_webhook_signature


def test_valid_signature_passes():
    secret = "s3cret"
    payload = b'{"action": "opened"}'
    signature = compute_webhook_signature(payload, secret)
    assert verify_webhook_signature(payload, signature, secret)


def test_tampered_payload_fails():
    secret = "s3cret"
    payload = b'{"action": "opened"}'
    signature = compute_webhook_signature(payload, secret)
    assert not verify_webhook_signature(b'{"action": "deleted"}', signature, secret)


def test_wrong_secret_fails():
    payload = b'{"action": "opened"}'
    signature = compute_webhook_signature(payload, "s3cret")
    assert not verify_webhook_signature(payload, signature, "other-secret")


def test_missing_header_fails():
    assert not verify_webhook_signature(b"x", None, "s3cret")


def test_wrong_prefix_fails():
    assert not verify_webhook_signature(b"x", "sha1=whatever", "s3cret")


def test_empty_secret_fails():
    assert not verify_webhook_signature(b"x", "sha256=whatever", "")
