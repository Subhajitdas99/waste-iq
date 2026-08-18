import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import set_request_id
from app.core.request_context import set_request_metadata


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

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

        response.headers["X-Request-ID"] = request_id
        return response
