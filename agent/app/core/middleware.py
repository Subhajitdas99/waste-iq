"""ASGI middleware for request correlation IDs."""

from __future__ import annotations

import uuid

_REQUEST_ID_HEADER = "x-request-id"


class RequestIDMiddleware:
    """Ensures every HTTP response carries a stable x-request-id.

    The ID is read from the inbound header when present (GitHub webhook
    deliveries, API clients) or generated once per request, then mirrored
    onto the response for correlation with review sessions.
    """

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = scope.get("headers") or []
        request_id = next(
            (value.decode("latin-1") for name, value in headers if name == b"x-request-id"), None
        )
        if not request_id:
            request_id = uuid.uuid4().hex
            scope = dict(scope)
            scope["headers"] = headers + [(b"x-request-id", request_id.encode("latin-1"))]

        async def send_wrapper(message) -> None:
            if message["type"] == "http.response.start":
                response_headers = list(message.get("headers") or [])
                response_headers.append((b"x-request-id", request_id.encode("latin-1")))
                message = dict(message)
                message["headers"] = response_headers
            await send(message)

        await self.app(scope, receive, send_wrapper)
