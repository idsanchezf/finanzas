"""DTO: Extracto — Datos presentables de un extracto."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID


@dataclass
class ExtractoDTO:
    """DTO de presentacion para un extracto bancario."""

    id: UUID
    tarjeta_id: UUID
    estado: str
    periodo_inicio: date | None = None
    periodo_fin: date | None = None
    fecha_corte: date | None = None
    fecha_limite_pago: date | None = None
    pago_minimo: Decimal = Decimal("0.00")
    pago_total: Decimal = Decimal("0.00")
    cupo_total: Decimal = Decimal("0.00")
    cupo_disponible: Decimal = Decimal("0.00")
    progress_pct: int = 0
    created_at: datetime | None = None

    @classmethod
    def from_entity(cls, extracto: Any) -> ExtractoDTO:
        return cls(
            id=extracto.id,
            tarjeta_id=extracto.tarjeta_id,
            estado=extracto.estado.value if hasattr(extracto.estado, "value") else str(extracto.estado),
            periodo_inicio=extracto.periodo_inicio,
            periodo_fin=extracto.periodo_fin,
            fecha_corte=extracto.fecha_corte,
            fecha_limite_pago=extracto.fecha_limite_pago,
            pago_minimo=extracto.pago_minimo,
            pago_total=extracto.pago_total,
            cupo_total=extracto.cupo_total,
            cupo_disponible=extracto.cupo_disponible,
            progress_pct=extracto.progress_pct,
            created_at=extracto.created_at,
        )
