"""Entidad Extracto — Aggregate Root.

Representa un extracto bancario cargado por el usuario.
Contiene metadatos del periodo de facturacion y el estado de procesamiento.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from src.domain.events import (
    ExtractoCargado,
    ExtractoProcesado,
)


class EstadoExtracto(str, Enum):
    PENDING = "PENDING"
    PARSING = "PARSING"
    CLASSIFYING = "CLASSIFYING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


@dataclass
class Extracto:
    """Extracto bancario mensual cargado por el usuario."""

    id: UUID = field(default_factory=uuid4)
    tarjeta_id: UUID = field(default_factory=uuid4)
    usuario_id: UUID = field(default_factory=uuid4)
    estado: EstadoExtracto = EstadoExtracto.PENDING
    periodo_inicio: date | None = None
    periodo_fin: date | None = None
    fecha_corte: date | None = None
    fecha_limite_pago: date | None = None
    pago_minimo: Decimal = field(default_factory=lambda: Decimal("0.00"))
    pago_total: Decimal = field(default_factory=lambda: Decimal("0.00"))
    cupo_total: Decimal = field(default_factory=lambda: Decimal("0.00"))
    cupo_disponible: Decimal = field(default_factory=lambda: Decimal("0.00"))
    tasas_interes: dict[str, Any] = field(default_factory=dict)
    metadatos: dict[str, Any] = field(default_factory=dict)
    archivo_s3_key: str | None = None
    error_message: str | None = None
    progress_pct: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Transacciones asociadas (lazy loaded por el repositorio)
    transacciones: list[Any] = field(default_factory=list)

    def iniciar_procesamiento(self) -> list[Any]:
        """Marca el extracto como en procesamiento y publica evento."""
        self.estado = EstadoExtracto.PARSING
        self.progress_pct = 10
        event = ExtractoCargado(
            extracto_id=self.id,
            usuario_id=self.usuario_id,
            tarjeta_id=self.tarjeta_id,
            s3_key=self.archivo_s3_key or "",
        )
        return [event]

    def avanzar_parseo(self, progress_pct: int) -> None:
        """Actualiza el progreso durante el parseo."""
        self.estado = EstadoExtracto.PARSING
        self.progress_pct = max(10, min(60, progress_pct))

    def iniciar_clasificacion(self) -> None:
        """Marca el inicio del proceso de clasificacion."""
        self.estado = EstadoExtracto.CLASSIFYING
        self.progress_pct = 70

    def completar(self) -> list[Any]:
        """Marca el extracto como procesado exitosamente."""
        self.estado = EstadoExtracto.COMPLETED
        self.progress_pct = 100
        event = ExtractoProcesado(
            extracto_id=self.id,
            usuario_id=self.usuario_id,
            tarjeta_id=self.tarjeta_id,
            transaction_count=len(self.transacciones),
        )
        return [event]

    def marcar_error(self, mensaje: str) -> None:
        """Marca el extracto con error de procesamiento."""
        self.estado = EstadoExtracto.ERROR
        self.error_message = mensaje

    @property
    def porcentaje_cupo_utilizado(self) -> Decimal:
        """Porcentaje del cupo de credito utilizado."""
        if self.cupo_total and self.cupo_total > 0:
            return (self.pago_total / self.cupo_total) * 100
        return Decimal("0")

    @property
    def dias_para_pago(self) -> int:
        """Dias restantes hasta la fecha limite de pago."""
        if self.fecha_limite_pago:
            delta = self.fecha_limite_pago - date.today()
            return max(0, delta.days)
        return 0
