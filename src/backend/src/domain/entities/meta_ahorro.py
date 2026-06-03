"""Entidad MetaAhorro — Objetivo de ahorro del usuario."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4


@dataclass
class MetaAhorro:
    """Meta de ahorro con objetivo financiero y fecha deseada."""

    id: UUID = field(default_factory=uuid4)
    usuario_id: UUID = field(default_factory=uuid4)
    nombre: str = ""
    monto_objetivo: Decimal = field(default_factory=lambda: Decimal("0.00"))
    monto_acumulado: Decimal = field(default_factory=lambda: Decimal("0.00"))
    fecha_deseada: date | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def agregar_ahorro(self, monto: Decimal) -> None:
        """Incrementa el monto acumulado."""
        self.monto_acumulado += monto

    def calcular_progreso(self) -> dict:
        """Calcula el progreso hacia la meta."""
        if self.monto_objetivo <= 0:
            return {"porcentaje": Decimal("0"), "faltante": Decimal("0")}

        porcentaje = (self.monto_acumulado / self.monto_objetivo) * 100
        faltante = self.monto_objetivo - self.monto_acumulado

        return {
            "acumulado": self.monto_acumulado,
            "porcentaje": round(porcentaje, 2),
            "faltante": faltante,
        }

    @property
    def completada(self) -> bool:
        """True si ya se alcanzo la meta."""
        return self.monto_acumulado >= self.monto_objetivo
