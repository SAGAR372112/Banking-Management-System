"""Custom middleware: correlation IDs and structured request logging."""
import time
import uuid
from typing import Callable

from django.http import HttpRequest, HttpResponse
from loguru import logger


class CorrelationIdMiddleware:
    """
    Attach a unique correlation ID to every request.
    Passes it through as X-Correlation-ID response header.
    """

    HEADER = "HTTP_X_CORRELATION_ID"
    RESPONSE_HEADER = "X-Correlation-ID"

    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        correlation_id = request.META.get(self.HEADER, str(uuid.uuid4()))
        request.correlation_id = correlation_id  # type: ignore[attr-defined]
        response = self.get_response(request)
        response[self.RESPONSE_HEADER] = correlation_id
        return response


class RequestLoggingMiddleware:
    """
    Log every inbound request and outbound response with structured metadata.
    """

    SENSITIVE_PATHS = {"/api/users/register/", "/api/token/"}

    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        start = time.perf_counter()
        correlation_id = getattr(request, "correlation_id", "-")
        user_id = getattr(getattr(request, "user", None), "id", None)
        is_sensitive = request.path in self.SENSITIVE_PATHS

        logger.info(
            "REQUEST  method={method} path={path} user={user} cid={cid}",
            method=request.method,
            path=request.path,
            user=user_id,
            cid=correlation_id,
        )

        response = self.get_response(request)

        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "RESPONSE method={method} path={path} status={status} duration_ms={duration:.1f} cid={cid}",
            method=request.method,
            path=request.path if not is_sensitive else "[REDACTED]",
            status=response.status_code,
            duration=duration_ms,
            cid=correlation_id,
        )
        return response
