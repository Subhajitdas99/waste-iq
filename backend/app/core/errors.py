"""Standardized error codes for WIQ-V1-012 (Centralized API Error Handling).

Each code maps to an HTTP status code and represents a distinct error condition.
Codes are used in the structured error response format:

    {
        "error": {
            "code": "RESOURCE_NOT_FOUND",
            "message": "The requested resource was not found.",
            "details": null,
            "request_id": "..."
        }
    }
"""

from __future__ import annotations

from enum import Enum


class ErrorCode(str, Enum):
    """Machine-readable error codes for API responses.

    These codes are stable and should never change between API versions
    without a major version bump. Each code maps to a specific HTTP status
    and client-facing scenario.
    """

    VALIDATION_ERROR = "VALIDATION_ERROR"
    """Request body or parameters failed validation (HTTP 422)."""

    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    """Login or authentication credentials are invalid (HTTP 401)."""

    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    """No valid authentication credentials were provided (HTTP 401)."""

    FORBIDDEN = "FORBIDDEN"
    """The authenticated user lacks permission for this action (HTTP 403)."""

    NOT_FOUND = "NOT_FOUND"
    """The requested resource does not exist (HTTP 404)."""

    CONFLICT = "CONFLICT"
    """The request conflicts with the current server state (HTTP 409)."""

    RATE_LIMITED = "RATE_LIMITED"
    """Too many requests; retry after the indicated delay (HTTP 429)."""

    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    """Unexpected server error; check request_id for debugging (HTTP 500)."""

    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    """The service is temporarily unavailable (HTTP 503)."""

    GATEWAY_ERROR = "GATEWAY_ERROR"
    """Upstream service returned an error (HTTP 502)."""

    BAD_REQUEST = "BAD_REQUEST"
    """The request is malformed or invalid (HTTP 400)."""


STATUS_CODE_MAP: dict[int, ErrorCode] = {
    400: ErrorCode.BAD_REQUEST,
    401: ErrorCode.AUTHENTICATION_REQUIRED,
    403: ErrorCode.FORBIDDEN,
    404: ErrorCode.NOT_FOUND,
    409: ErrorCode.CONFLICT,
    422: ErrorCode.VALIDATION_ERROR,
    429: ErrorCode.RATE_LIMITED,
    500: ErrorCode.INTERNAL_SERVER_ERROR,
    502: ErrorCode.GATEWAY_ERROR,
    503: ErrorCode.SERVICE_UNAVAILABLE,
}


def code_for_status(status_code: int) -> ErrorCode:
    """Return the standard error code for an HTTP status code."""
    return STATUS_CODE_MAP.get(status_code, ErrorCode.INTERNAL_SERVER_ERROR)
