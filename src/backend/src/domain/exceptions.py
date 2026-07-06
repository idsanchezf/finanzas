"""Excepciones de dominio — Mapeo semantico de errores de negocio.

Cada excepcion extiende DomainException con un error_code semantico.
El middleware DomainExceptionMiddleware en la capa API las convierte
automaticamente en respuestas HTTP con el status code adecuado.

Mapping:
    EXTRACTO_DUPLICADO       -> 409 Conflict
    TARJETA_NO_ENCONTRADA    -> 404 Not Found
    VALIDACION_FALLIDA       -> 422 Unprocessable Entity
    NO_AUTENTICADO           -> 401 Unauthorized
    PERMISO_DENEGADO         -> 403 Forbidden
"""

from __future__ import annotations

from datetime import date
from uuid import UUID


class DomainException(Exception):
    """Excepcion base del dominio con codigo de error semantico."""

    def __init__(self, message: str, error_code: str = "DOMAIN_ERROR") -> None:
        self.error_code = error_code
        super().__init__(message)


# ============================================================
# Extracto
# ============================================================


class ExtractoDuplicadoException(DomainException):
    """Se lanza cuando se detecta que un extracto ya existe
    para la misma tarjeta + periodo.

    Dos casos de uso:
    1. Pre-flight check (95%): detectado en capa de aplicacion
       -> extracto_id, tarjeta_id, periodo_inicio, periodo_fin conocidos
    2. Race condition safety net (5%): detectado por constraint BD
       -> extracto_id = None (no se sabe cual gano la race)
    """

    def __init__(
        self,
        extracto_id_existente: UUID | None = None,
        tarjeta_id: UUID | None = None,
        periodo_inicio: date | None = None,
        periodo_fin: date | None = None,
        message: str | None = None,
    ) -> None:
        self.extracto_id = extracto_id_existente
        self.tarjeta_id = tarjeta_id
        self.periodo_inicio = periodo_inicio
        self.periodo_fin = periodo_fin

        if message is None and tarjeta_id and periodo_inicio and periodo_fin:
            # Duplicado detectado por periodo (pre-flight completo)
            message = (
                f"Este extracto ya fue cargado anteriormente. "
                f"Tarjeta: {tarjeta_id}, "
                f"Periodo: {periodo_inicio} a {periodo_fin}."
            )
        elif message is None and tarjeta_id and extracto_id_existente:
            # Duplicado detectado por hash (sin periodo conocido)
            message = (
                "Este archivo ya fue cargado anteriormente para esta tarjeta. "
                "No es posible cargar el mismo extracto dos veces."
            )
        elif message is None:
            # Race condition (safety net de BD)
            message = (
                "Conflicto de concurrencia: el extracto fue creado "
                "por otra solicitud simultanea. Intente nuevamente."
            )

        super().__init__(message, error_code="EXTRACTO_DUPLICADO")


class ValidacionFallidaException(DomainException):
    """Error de validacion del archivo Excel (formato no reconocible)."""

    def __init__(self, message: str, detalles: dict | None = None) -> None:
        self.detalles = detalles or {}
        super().__init__(message, error_code="VALIDACION_FALLIDA")


# ============================================================
# Tarjeta
# ============================================================


class TarjetaNoEncontradaException(DomainException):
    """No se pudo identificar la tarjeta a partir del extracto."""

    def __init__(
        self, ultimos_4_digitos: str = "", banco: str = "", message: str | None = None
    ) -> None:
        self.ultimos_4_digitos = ultimos_4_digitos
        self.banco = banco
        if message is None:
            message = (
                f"No se pudo identificar la tarjeta con ultimos 4 digitos "
                f"'{ultimos_4_digitos}' para el banco '{banco}'"
            )
        super().__init__(message, error_code="TARJETA_NO_ENCONTRADA")


# ============================================================
# Auth
# ============================================================


class NoAutenticadoException(DomainException):
    """Token JWT invalido, expirado o no proporcionado."""

    def __init__(self, message: str = "Token JWT invalido o expirado") -> None:
        super().__init__(message, error_code="NO_AUTENTICADO")


class PermisoDenegadoException(DomainException):
    """El usuario no tiene permisos para realizar la operacion."""

    def __init__(self, message: str = "No tienes permisos para realizar esta operacion") -> None:
        super().__init__(message, error_code="PERMISO_DENEGADO")
