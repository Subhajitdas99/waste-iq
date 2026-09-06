"""Structured error response models and exception handlers for WIQ-V1-012.

This module provides:
- Standardized error response models
- Centralized exception handlers for consistent API error responses
- Integration with request ID middleware for traceable errors

All exceptions are logged server-side with full context while responses
contain only safe, user-facing information.
"""

from __future__ import annotations

import logging
import traceback
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from app.core.errors import ErrorCode, code_for_status
from app.core.logging import get_request_id

logger = logging.getLogger(__name__)


class ErrorResponse:
    """Structured error response with metadata.

    The response body structure:
        {
            "error": {
                "code": "ERROR_CODE",
                "message": "User-facing error message",
                "details": null | { ... },
                "request_id": "uuid"
            }
        }
    """

    def __init__(
        self,
        code: ErrorCode | str,
        message: str,
        *,
        details: Any = None,
        request_id: str | None = None,
    ):
        self.code = code if isinstance(code, str) else code.value
        self.message = message
        self.details = details
        self.request_id = request_id or get_request_id()

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
                "request_id": self.request_id,
            },
            "detail": self.message,
        }


def _build_validation_error_detail(errors: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Build a structured details object from Pydantic validation errors.

    Maps FastAPI/Starlette validation errors to field-specific messages.
    """
    if len(errors) == 0:
        return None

    field_errors: dict[str, list[str]] = {}
    general_errors: list[str] = []

    for error in errors:
        loc = tuple(error.get("loc", []))
        msg = error.get("msg", "Validation error")

        if len(loc) == 0:
            general_errors.append(str(msg))
            continue

        field_key = (
            ".".join(str(p) for p in loc[1:]) if len(loc) > 1 else str(loc[0] if loc else "")
        )
        if field_key not in field_errors:
            field_errors[field_key] = []
        field_errors[field_key].append(str(msg))

    result: dict[str, Any] = {}
    if field_errors:
        for field, messages in field_errors.items():
            if len(messages) == 1:
                result[field] = messages[0]
            else:
                result[field] = messages
    if general_errors:
        result["_general"] = general_errors

    return result if result else None


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTPException with structured error response."""
    error_code = code_for_status(exc.status_code)

    response = ErrorResponse(
        code=error_code,
        message=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
        request_id=get_request_id(),
    )

    logger.warning(
        "HTTP error response",
        extra={
            "error": exc.detail,
            "status_code": exc.status_code,
            "error_code": error_code.value,
            "path": request.url.path,
            "method": request.method,
        },
    )

    json_response = JSONResponse(
        status_code=exc.status_code,
        content=response.to_dict(),
    )

    if exc.headers:
        for key, value in exc.headers.items():
            json_response.headers[key] = value

    return json_response


async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors with structured response."""
    errors: list[dict[str, Any]] = []

    for error in exc.errors():
        loc = tuple(error.get("loc", []))
        errors.append(
            {
                "loc": list(loc),
                "msg": error.get("msg", "Validation error"),
                "type": error.get("type", "value_error"),
                "input": error.get("input"),
            }
        )

    error_code = ErrorCode.VALIDATION_ERROR
    details = _build_validation_error_detail(errors)

    field_messages: list[str] = []
    for err in errors:
        loc_path = ".".join(str(p) for p in err.get("loc", []))
        field_messages.append(f"{loc_path}: {err.get('msg', 'error')}")
    message = "; ".join(field_messages)[:200] or "Validation error"

    response = ErrorResponse(
        code=error_code,
        message=message,
        details=details,
        request_id=get_request_id(),
    )

    logger.info(
        "Request validation error",
        extra={
            "errors": errors,
            "path": request.url.path,
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response.to_dict(),
    )


async def http_exception_handler_422(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic ValidationError (from FastAPI body parsing) with structured response."""
    errors: list[dict[str, Any]] = []

    for error in exc.errors():
        loc = tuple(error.get("loc", []))
        errors.append(
            {
                "loc": list(loc),
                "msg": error.get("msg", "Validation error"),
                "type": error.get("type", "value_error"),
                "input": error.get("input"),
            }
        )

    error_code = ErrorCode.VALIDATION_ERROR
    details = _build_validation_error_detail(errors)

    field_messages: list[str] = []
    for err in errors:
        loc_path = ".".join(str(p) for p in err.get("loc", []))
        field_messages.append(f"{loc_path}: {err.get('msg', 'error')}")
    message = "; ".join(field_messages)[:200] or "Validation error"

    response = ErrorResponse(
        code=error_code,
        message=message,
        details=details,
        request_id=get_request_id(),
    )

    logger.info(
        "Pydantic validation error",
        extra={
            "errors": errors,
            "path": request.url.path,
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response.to_dict(),
    )


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """Handle SQLAlchemy IntegrityError with structured conflict response.

    Maps database constraint violations to safe user-facing messages.
    """
    error_code = ErrorCode.CONFLICT
    message = "Resource already exists"

    db_error_message = str(exc.orig).lower() if exc.orig else ""

    if (
        "unique" in db_error_message
        or "duplicate" in db_error_message
        or "already exists" in db_error_message
    ):
        message = "Resource already exists"
    elif "foreign key" in db_error_message:
        message = "Referenced resource does not exist"
    elif "not null" in db_error_message or "required" in db_error_message:
        message = "Required field is missing"
    elif "check" in db_error_message:
        message = "Data validation failed"

    response = ErrorResponse(
        code=error_code,
        message=message,
        request_id=get_request_id(),
    )

    logger.warning(
        "Database integrity error",
        extra={
            "message": str(exc.orig),
            "path": request.url.path,
            "method": request.method,
            "request_id": get_request_id(),
        },
    )

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=response.to_dict(),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with safe client response and full server logging."""
    error_code = ErrorCode.INTERNAL_SERVER_ERROR

    response = ErrorResponse(
        code=error_code,
        message="An unexpected error occurred. Please try again later.",
        request_id=get_request_id(),
    )

    logger.error(
        "Unexpected server error",
        extra={
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "path": request.url.path,
            "method": request.method,
            "request_id": get_request_id(),
            "traceback": traceback.format_exc(),
        },
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.to_dict(),
    )


def register_exception_handlers(app) -> None:
    """Register all exception handlers on the FastAPI app."""
    from fastapi.exceptions import RequestValidationError as FastAPIRequestValidationError

    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    app.add_exception_handler(ValidationError, http_exception_handler_422)
    app.add_exception_handler(FastAPIRequestValidationError, request_validation_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
