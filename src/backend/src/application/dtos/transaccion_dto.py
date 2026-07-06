"""DTO: Transaccion — Datos presentables de una transaccion."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID


@dataclass
class TransaccionDTO:
    """DTO de presentacion para una transaccion."""

    id: UUID
    extracto_id: UUID
    fecha: date | None = None
    comercio: str = ""
    valor: Decimal = Decimal("0.00")
    categoria_id: UUID | None = None
    confidence: Decimal | None = None
    es_cuota: bool = False
    cuotas_restantes: int | None = None
    moneda_original: str | None = None
    valor_moneda_original: Decimal | None = None
