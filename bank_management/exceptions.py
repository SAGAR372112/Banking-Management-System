"""Custom exception handling for consistent API error responses."""
import logging
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger("bank")


def custom_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """
    Custom exception handler that returns consistent error response format.

    All errors return: {"error": {"code": str, "message": str, "details": any}}
    """
    # Call DRF's default handler first
    response = exception_handler(exc, context)

    if response is not None:
        error_payload = {
            "error": {
                "code": _get_error_code(exc),
                "message": _get_error_message(response.data),
                "details": response.data,
            }
        }
        response.data = error_payload
        return response

    # Handle Django exceptions not caught by DRF
    if isinstance(exc, Http404):
        return Response(
            {"error": {"code": "NOT_FOUND", "message": "Resource not found.", "details": {}}},
            status=status.HTTP_404_NOT_FOUND,
        )

    if isinstance(exc, PermissionDenied):
        return Response(
            {"error": {"code": "PERMISSION_DENIED", "message": "You do not have permission.", "details": {}}},
            status=status.HTTP_403_FORBIDDEN,
        )

    if isinstance(exc, ValidationError):
        return Response(
            {"error": {"code": "VALIDATION_ERROR", "message": "Validation failed.", "details": exc.message_dict}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Log unexpected errors
    logger.exception("Unexpected error: %s", exc)
    return Response(
        {"error": {"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred.", "details": {}}},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _get_error_code(exc: Exception) -> str:
    """Map exception type to error code string."""
    from rest_framework import exceptions

    mapping = {
        exceptions.AuthenticationFailed: "AUTHENTICATION_FAILED",
        exceptions.NotAuthenticated: "NOT_AUTHENTICATED",
        exceptions.PermissionDenied: "PERMISSION_DENIED",
        exceptions.NotFound: "NOT_FOUND",
        exceptions.ValidationError: "VALIDATION_ERROR",
        exceptions.Throttled: "RATE_LIMIT_EXCEEDED",
        exceptions.MethodNotAllowed: "METHOD_NOT_ALLOWED",
    }
    return mapping.get(type(exc), "API_ERROR")


def _get_error_message(data: Any) -> str:
    """Extract a human-readable message from DRF error data."""
    if isinstance(data, dict):
        if "detail" in data:
            return str(data["detail"])
        # Return first field error
        for value in data.values():
            if isinstance(value, list) and value:
                return str(value[0])
    if isinstance(data, list) and data:
        return str(data[0])
    return str(data)
