import re
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import set_request_id
from app.core.request_context import set_request_metadata

_REQUEST_ID_HEADER = "X-Request-ID"

# Client-supplied request IDs are only trusted when they are short and built
# from a conservative character set. Anything else — missing, oversized,
# whitespace, control characters — is replaced with a generated UUID4 so a
# forged or malformed value can never reach log files or response headers.
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def normalize_request_id(value: str | None) -> str:
    """Return a safe correlation id for the request."""

    if value is not None and _REQUEST_ID_PATTERN.fullmatch(value):
        return value
    return str(uuid.uuid4())


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = normalize_request_id(request.headers.get(_REQUEST_ID_HEADER))

        set_request_id(request_id)
        request.state.request_id = request_id

        # Request metadata for audit logging. The client IP comes from the
        # direct connection only: X-Forwarded-For is not trusted because the
        # application has no proxy-aware IP handling.
        client = request.client
        set_request_metadata(
            ip_address=client.host if client is not None else None,
            user_agent=request.headers.get("user-agent"),
        )

        response = await call_next(request)

        response.headers[_REQUEST_ID_HEADER] = request_id
        return response
