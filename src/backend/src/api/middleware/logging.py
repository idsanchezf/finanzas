"""Middleware de logging estructurado con correlation ID."""

from __future__ import annotations

import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware que registra cada request con correlation ID.

    Agrega:
    - X-Correlation-ID header (genera si no existe)
    - Logging estructurado de cada request con duracion, status code, etc.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Generar o propagar correlation ID
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

        # Agregar al contexto de structlog
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown",
        )

        # Agregar header a la request para que los endpoints lo lean
        request.state.correlation_id = correlation_id

        start_time = time.monotonic()

        try:
            response = await call_next(request)
            duration_ms = (time.monotonic() - start_time) * 1000

            logger.info(
                "Request completado",
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )

            # Agregar correlation ID a la respuesta
            response.headers["X-Correlation-ID"] = correlation_id

            return response

        except Exception as e:
            duration_ms = (time.monotonic() - start_time) * 1000
            logger.error(
                "Request fallido",
                error=str(e),
                duration_ms=round(duration_ms, 2),
                exc_info=True,
            )
            raise

        finally:
            structlog.contextvars.unbind_contextvars(
                "correlation_id", "method", "path", "client_ip"
            )
