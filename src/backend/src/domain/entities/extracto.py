"""Entidad Extracto — Aggregate Root.

Representa un extracto bancario cargado por el usuario.
Contiene metadatos del periodo de facturacion y el estado de procesamiento.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from src.domain.events import (
    ExtractoCargado,
    ExtractoProcesado,
)
from src.domain.value_objects.money import Money


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
    pago_minimo: Money = field(default_factory=lambda: Money.zero("COP"))
    pago_total: Money = field(default_factory=lambda: Money.zero("COP"))
    cupo_total: Money = field(default_factory=lambda: Money.zero("COP"))
    cupo_disponible: Money = field(default_factory=lambda: Money.zero("COP"))
    tasas_interes: dict[str, Any] = field(default_factory=dict)
    metadatos: dict[str, Any] = field(default_factory=dict)
    archivo_s3_key: str | None = None
    error_message: str | None = None
    progress_pct: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Transacciones asociadas (lazy loaded por el repositorio)
    transacciones: list[Any] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Valida invariantes de negocio: periodo_inicio < periodo_fin."""
        if self.periodo_inicio is not None and self.periodo_fin is not None:
            if self.periodo_inicio > self.periodo_fin:
                raise ValueError(
                    f"periodo_inicio ({self.periodo_inicio}) debe ser anterior a "
                    f"periodo_fin ({self.periodo_fin})"
                )

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

    # ============================================================
    # Propiedades calculadas
    # ============================================================

    @property
    def porcentaje_cupo_utilizado(self) -> Decimal:
        """Porcentaje del cupo de credito utilizado: (pago_total / cupo_total) * 100."""
        if self.cupo_total is not None and not self.cupo_total.is_zero:
            return (self.pago_total.amount / self.cupo_total.amount) * 100
        return Decimal("0")

    @property
    def dias_para_pago(self) -> int:
        """Dias restantes hasta la fecha limite de pago (desde hoy)."""
        if self.fecha_limite_pago:
            delta = self.fecha_limite_pago - date.today()
            return max(0, delta.days)
        return 0

    @property
    def dias_entre_corte_y_pago(self) -> int | None:
        """Dias entre fecha_corte y fecha_limite_pago (due_date - cutoff_date)."""
        if self.fecha_corte is not None and self.fecha_limite_pago is not None:
            return (self.fecha_limite_pago - self.fecha_corte).days
        return None

    @property
    def duracion_periodo(self) -> int | None:
        """Duracion en dias del periodo de facturacion."""
        if self.periodo_inicio is not None and self.periodo_fin is not None:
            return (self.periodo_fin - self.periodo_inicio).days
        return None
