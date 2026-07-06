"""Entidad Transaccion — Entidad hija de Extracto.

Representa una transaccion individual dentro de un extracto bancario.
Soporta cuotas, moneda extranjera, clasificacion y nivel de confianza.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4


@dataclass
class Transaccion:
    """Transaccion individual del extracto bancario."""

    id: UUID = field(default_factory=uuid4)
    extracto_id: UUID = field(default_factory=uuid4)
    usuario_id: UUID = field(default_factory=uuid4)
    numero_autorizacion: str | None = None
    fecha: date | None = None
    comercio_original: str = ""
    comercio_traducido: str | None = None
    valor: Decimal = field(default_factory=lambda: Decimal("0.00"))
    numero_cuotas: str | None = None  # Ej: "1/36"
    cuotas_totales: int | None = None
    cuota_actual: int | None = None
    valor_cuota: Decimal = field(default_factory=lambda: Decimal("0.00"))
    interes_mensual_pct: Decimal | None = None
    interes_anual_pct: Decimal | None = None
    saldo_pendiente: Decimal = field(default_factory=lambda: Decimal("0.00"))
    moneda_original: str | None = None  # Codigo ISO: USD, EUR, etc.
    valor_moneda_original: Decimal | None = None
    categoria_id: UUID | None = None
    confidence: Decimal | None = None  # 0-100
    es_abono: bool = False
    es_cuota: bool = False
    parent_transaccion_id: UUID | None = None  # Para sub-filas VR MONEDA ORIG
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        """Deriva flags de abono y cuotas a partir de los datos."""
        if self.valor < 0:
            self.es_abono = True
        if self.cuotas_totales is not None and self.cuotas_totales > 1:
            self.es_cuota = True

    def clasificar(self, categoria_id: UUID, confidence: Decimal) -> list[Any]:
        """Asigna una categoria a la transaccion con su nivel de confianza."""
        from src.domain.events import TransaccionClasificada

        categoria_anterior = self.categoria_id
        self.categoria_id = categoria_id
        self.confidence = confidence

        event = TransaccionClasificada(
            transaction_id=self.id,
            extracto_id=self.extracto_id,
            categoria_id=categoria_id,
            categoria_anterior=categoria_anterior,
            confidence=confidence,
        )
        return [event]

    def corregir_categoria(self, categoria_id: UUID) -> list[Any]:
        """El usuario corrige manualmente la categoria. Dispara evento de aprendizaje."""
        from src.domain.events import CategoriaCorregida

        anterior = self.categoria_id
        self.categoria_id = categoria_id
        self.confidence = Decimal("100.00")

        event = CategoriaCorregida(
            transaction_id=self.id,
            categoria_anterior=anterior,
            categoria_nueva=categoria_id,
            comercio_original=self.comercio_original,
        )
        return [event]

    @property
    def es_confianza_baja(self) -> bool:
        """True si la clasificacion tiene confianza baja (<70%)."""
        return self.confidence is not None and self.confidence < 70

    @property
    def nombre_visible(self) -> str:
        """Nombre amigable del comercio para mostrar al usuario."""
        return self.comercio_traducido or self.comercio_original

    @property
    def es_sub_fila(self) -> bool:
        """True si es una sub-fila VR MONEDA ORIG (tiene parent)."""
        return self.parent_transaccion_id is not None
