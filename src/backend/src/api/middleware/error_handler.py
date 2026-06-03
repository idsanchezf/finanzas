"""Middleware de manejo de errores — Problem Details RFC 7807."""

from __future__ import annotations

import structlog
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware que captura excepciones no manejadas y las convierte a RFC 7807.

    Problem Details (RFC 7807):
    {
        "type": "about:blank",
        "title": "Internal Server Error",
        "status": 500,
        "detail": "An unexpected error occurred",
        "instance": "/api/v1/extracts/123"
    }
    """

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            correlation_id = getattr(request.state, "correlation_id", "unknown")

            logger.error(
                "Error no manejado",
                error=str(e),
                correlation_id=correlation_id,
                path=request.url.path,
                exc_info=True,
            )

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "type": "about:blank",
                    "title": "Internal Server Error",
                    "status": 500,
                    "detail": "An unexpected error occurred. Please try again later.",
                    "instance": request.url.path,
                    "correlation_id": correlation_id,
                },
            )
