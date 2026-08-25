"""WIQ-V1-023 Monitoring & Logging behaviour.

All tests are offline: Sentry is exercised through monkeypatched init calls
and a local transport callable, never against the external service.
"""

import json
import logging
import sys
import uuid

import pytest
import sentry_sdk
from fastapi.testclient import TestClient
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.transport import Transport

from app.core.config import settings
from app.core.logging import (
    JsonFormatter,
    RequestIDFilter,
    get_request_id,
    set_request_id,
    setup_logging,
)
from app.core.middleware import normalize_request_id
from app.main import app as fastapi_app

# ─── Request ID ──────────────────────────────────────────────────────────────


def test_response_contains_x_request_id(client):
    response = client.get("/health")
    request_id = response.headers["x-request-id"]
    assert request_id
    uuid.UUID(request_id)  # generated ids must be valid UUIDs


def test_valid_supplied_request_id_is_echoed(client):
    supplied = "frontend-42.test_run"
    response = client.get("/health", headers={"X-Request-ID": supplied})
    assert response.headers["x-request-id"] == supplied


@pytest.mark.parametrize(
    ("supplied", "label"),
    [
        ("id with spaces", "whitespace"),
        ("bad/slash", "path separator"),
        ("line\nbreak", "control character"),
        ("x" * 65, "oversized"),
        ("", "empty"),
    ],
)
def test_invalid_supplied_request_id_is_replaced(client, supplied, label):
    response = client.get("/health", headers={"X-Request-ID": supplied})
    returned = response.headers["x-request-id"]
    assert returned != supplied, label
    uuid.UUID(returned)  # replaced with a generated UUID4


def test_boundary_length_request_id_is_accepted():
    assert normalize_request_id("a" * 64) == "a" * 64


@pytest.mark.parametrize("value", [None, "", "a" * 65, "with space", "tab\tchar", "\x00byte"])
def test_normalize_request_id_falls_back_to_uuid4(value):
    normalized = normalize_request_id(value)
    assert normalized != value
    uuid.UUID(normalized)


def test_normalize_request_id_accepts_safe_charset():
    assert normalize_request_id("Abc-123_def.456") == "Abc-123_def.456"


# ─── JSON structured logging ────────────────────────────────────────────────


def _make_record(name="app.test", msg="hello %s", args=("world",)):
    record = logging.LogRecord(
        name=name,
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=args,
        exc_info=None,
    )
    record.request_id = "-"
    return record


def test_json_formatter_produces_valid_json_with_required_fields():
    payload = json.loads(JsonFormatter().format(_make_record()))

    assert payload["message"] == "hello world"
    assert payload["level"] == "INFO"
    assert payload["logger"] == "app.test"
    assert payload["request_id"] == "-"
    assert payload["timestamp"]  # ISO-like timestamp present


def test_json_formatter_includes_request_id_from_record():
    record = _make_record()
    record.request_id = "corr-99"

    payload = json.loads(JsonFormatter().format(record))
    assert payload["request_id"] == "corr-99"


def test_json_formatter_keeps_hostile_characters_valid_json():
    message = 'quote " backslash \\ newline \n end'
    record = _make_record(msg=message, args=())

    payload = json.loads(JsonFormatter().format(record))
    assert payload["message"] == message


def test_json_formatter_preserves_extra_fields_and_hides_internals():
    record = _make_record()
    record.request_id = "corr-extra"
    record.pickup_id = 5  # extra field passed via logger.info(..., extra={...})

    payload = json.loads(JsonFormatter().format(record))
    assert payload["pickup_id"] == 5
    assert "pathname" not in payload
    assert "thread" not in payload


def test_json_formatter_includes_exception_traceback():
    try:
        raise RuntimeError("boom")
    except RuntimeError:
        record = _make_record(msg="failed", args=())
        record.exc_info = sys.exc_info()

    payload = json.loads(JsonFormatter().format(record))
    assert "RuntimeError" in payload["exception"]
    assert "boom" in payload["exception"]


def test_json_formatter_structures_uvicorn_access_records():
    record = logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg='%s - "%s %s HTTP/%s" %d',
        args=("127.0.0.1", "GET", "/health/ready", "1.1", 200),
        exc_info=None,
    )
    record.request_id = "access-corr-1"

    payload = json.loads(JsonFormatter().format(record))
    assert payload["event"] == "access"
    assert payload["client_addr"] == "127.0.0.1"
    assert payload["method"] == "GET"
    assert payload["path"] == "/health/ready"
    assert payload["http_version"] == "1.1"
    assert payload["status_code"] == 200
    assert payload["request_id"] == "access-corr-1"


class _CaptureHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.formatted: list[str] = []

    def emit(self, record):
        self.formatted.append(self.format(record))


def test_application_logs_carry_active_request_id():
    set_request_id("ctx-corr-7")
    handler = _CaptureHandler()
    handler.setFormatter(JsonFormatter())
    handler.addFilter(RequestIDFilter())
    logger = logging.getLogger("app.monitoring.test_correlation")
    logger.addHandler(handler)
    previous_propagate = logger.propagate
    logger.propagate = False
    try:
        logger.info("correlated message")
        payload = json.loads(handler.formatted[-1])
        assert payload["request_id"] == "ctx-corr-7"
        assert get_request_id() == "ctx-corr-7"
    finally:
        logger.removeHandler(handler)
        logger.propagate = previous_propagate
        set_request_id("-")


def test_setup_logging_applies_log_level_to_root_and_uvicorn():
    setup_logging(settings.log_level)  # baseline for the restore below
    try:
        setup_logging("WARNING")

        root = logging.getLogger()
        assert root.level == logging.WARNING
        assert any(isinstance(f, RequestIDFilter) for h in root.handlers for f in h.filters)

        for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
            uvicorn_logger = logging.getLogger(name)
            assert uvicorn_logger.level == logging.WARNING, name
            assert uvicorn_logger.propagate is False, name
            assert uvicorn_logger.handlers, name
            for handler in uvicorn_logger.handlers:
                assert isinstance(handler.formatter, JsonFormatter), name
    finally:
        setup_logging(settings.log_level)


def test_setup_logging_does_not_duplicate_handlers():
    setup_logging(settings.log_level)
    setup_logging(settings.log_level)

    assert len(logging.getLogger("uvicorn.access").handlers) == 1
    assert len(logging.getLogger().handlers) == 1


# ─── Sentry ──────────────────────────────────────────────────────────────────


def test_sentry_not_initialized_without_dsn(monkeypatch):
    calls = []
    monkeypatch.setattr(sentry_sdk, "init", lambda **kwargs: calls.append(kwargs))
    monkeypatch.setattr(settings, "sentry_dsn", None)

    from app.core.sentry_sdk import init_sentry

    init_sentry()

    assert calls == []


def test_sentry_initialized_with_environment_release_and_integrations(monkeypatch):
    calls = []
    monkeypatch.setattr(sentry_sdk, "init", lambda **kwargs: calls.append(kwargs))
    monkeypatch.setattr(settings, "sentry_dsn", "https://public@sentry.example.com/1")

    from app.core.sentry_sdk import init_sentry

    init_sentry()

    kwargs = calls[0]
    assert kwargs["dsn"] == "https://public@sentry.example.com/1"
    assert kwargs["environment"] == settings.environment
    assert kwargs["release"] == settings.release
    integration_types = {type(integration) for integration in kwargs["integrations"]}
    assert FastApiIntegration in integration_types
    assert StarletteIntegration in integration_types


def test_set_sentry_user_attaches_stringified_id(monkeypatch):
    captured = []
    monkeypatch.setattr(sentry_sdk, "set_user", lambda user: captured.append(user))
    monkeypatch.setattr(settings, "sentry_dsn", "https://public@sentry.example.com/1")

    from app.core.sentry_sdk import set_sentry_user

    set_sentry_user(42)

    assert captured == [{"id": "42"}]


def test_set_sentry_user_is_noop_when_sentry_disabled(monkeypatch):
    captured = []
    monkeypatch.setattr(sentry_sdk, "set_user", lambda user: captured.append(user))
    monkeypatch.setattr(settings, "sentry_dsn", None)

    from app.core.sentry_sdk import set_sentry_user

    set_sentry_user(42)

    assert captured == []


def test_set_sentry_user_is_noop_for_anonymous_requests(monkeypatch):
    captured = []
    monkeypatch.setattr(sentry_sdk, "set_user", lambda user: captured.append(user))
    monkeypatch.setattr(settings, "sentry_dsn", "https://public@sentry.example.com/1")

    from app.core.sentry_sdk import set_sentry_user

    set_sentry_user(None)

    assert captured == []


class _LocalTransport(Transport):
    """In-process Sentry transport: captures events synchronously, no network."""

    def __init__(self, sink):
        self.sink = sink

    def capture_envelope(self, envelope):
        # SDK 2.x delivers error events wrapped in envelopes.
        event = envelope.get_event()
        if event is not None:
            self.sink(event)

    def capture_event(self, event):
        self.sink(event)


def test_route_exceptions_are_captured_by_sentry_offline(monkeypatch):
    """End-to-end offline proof that route exceptions reach Sentry.

    A real ``sentry_sdk.init`` runs with an in-process transport instead of a
    network DSN target, so the event is captured locally only.
    """

    events = []
    real_init = sentry_sdk.init

    def init_with_local_transport(**kwargs):
        kwargs.pop("transport", None)
        return real_init(transport=_LocalTransport(events.append), **kwargs)

    monkeypatch.setattr(sentry_sdk, "init", init_with_local_transport)
    monkeypatch.setattr(settings, "sentry_dsn", "https://public@sentry.example.com/1")

    from app.core.sentry_sdk import init_sentry as real_init_sentry

    real_init_sentry()

    client_options = sentry_sdk.get_client().options
    # PII capture must never be enabled by our initialization.
    assert client_options.get("send_default_pii") is not True

    boom_route = "/_test/sentry-boom"

    def _boom() -> None:
        raise RuntimeError("boom-for-sentry-test")

    fastapi_app.add_api_route(boom_route, _boom, methods=["GET"])
    try:
        test_client = TestClient(fastapi_app, raise_server_exceptions=False)
        response = test_client.get(boom_route, headers={"X-Request-ID": "sentry-e2e"})
        assert response.status_code == 500
    finally:
        fastapi_app.router.routes = [
            route
            for route in fastapi_app.router.routes
            if getattr(route, "path", None) != boom_route
        ]

    assert events, "expected the route exception to be captured by Sentry"
    exception_values = events[-1].get("exception", {}).get("values", [])
    assert any(value.get("type") == "RuntimeError" for value in exception_values)
    assert any("boom-for-sentry-test" in value.get("value", "") for value in exception_values)

    # Leave the global hub disabled so no later test can emit anywhere.
    real_init()


# ─── Readiness: production Cloudinary requirement lives in test_health.py ────
