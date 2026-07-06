"""Manejo de errores — Problem Details RFC 7807 + DomainException mapping.

Usa exception handlers nativos de FastAPI (@app.exception_handler)
en lugar de BaseHTTPMiddleware para evitar incompatibilidad con CORSMiddleware.
"""

from __future__ import annotations

import structlog
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.domain.exceptions import (
    DomainException,
    ExtractoDuplicadoException,
)

logger = structlog.get_logger(__name__)

# Mapping de error_code de dominio a HTTP status code
EXCEPTION_STATUS_MAP: dict[str, int] = {
    "EXTRACTO_DUPLICADO": 409,
    "TARJETA_NO_ENCONTRADA": 404,
    "VALIDACION_FALLIDA": 422,
    "NO_AUTENTICADO": 401,
    "PERMISO_DENEGADO": 403,
}


async def handle_domain_exception(request: Request, exc: DomainException) -> JSONResponse:
    """Exception handler nativo de FastAPI para DomainException."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    status_code = EXCEPTION_STATUS_MAP.get(exc.error_code, 400)

    logger.warning(
        "domain_exception",
        error_code=exc.error_code,
        message=str(exc),
        status_code=status_code,
        correlation_id=correlation_id,
        path=request.url.path,
    )

    body: dict = {
        "error": exc.error_code,
        "message": str(exc),
        "detail": str(exc),  # RFC 7807 / compatibilidad con frontend
    }

    # Enriquecer con datos adicionales para casos especificos
    if isinstance(exc, ExtractoDuplicadoException):
        body.update({
            "extracto_id": str(exc.extracto_id) if exc.extracto_id else None,
            "tarjeta_id": str(exc.tarjeta_id) if exc.tarjeta_id else None,
            "periodo_inicio": (
                exc.periodo_inicio.isoformat() if exc.periodo_inicio else None
            ),
            "periodo_fin": (
                exc.periodo_fin.isoformat() if exc.periodo_fin else None
            ),
        })

    return JSONResponse(status_code=status_code, content=body)


async def handle_unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
    """Exception handler nativo de FastAPI para errores no manejados."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")

    logger.error(
        "unhandled_error",
        error=str(exc),
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


# ============================================================
# Deprecated: ErrorHandlerMiddleware (BaseHTTPMiddleware)
# Mantenido para compatibilidad hacia atras.
# Preferir los exception handlers nativos de FastAPI.
# ============================================================


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """[DEPRECATED] Usar handle_domain_exception y handle_unhandled_exception."""

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except DomainException as e:
            return await handle_domain_exception(request, e)
        except Exception as e:
            return await handle_unhandled_exception(request, e)
