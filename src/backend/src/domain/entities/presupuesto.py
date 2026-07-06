"""Entidad Presupuesto — Limite de gasto por categoria."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4


@dataclass
class Presupuesto:
    """Presupuesto mensual por categoria de gasto."""

    id: UUID = field(default_factory=uuid4)
    usuario_id: UUID = field(default_factory=uuid4)
    categoria_id: UUID = field(default_factory=uuid4)
    limite_mensual: Decimal = field(default_factory=lambda: Decimal("0.00"))
    alerta_80pct: bool = True
    alerta_100pct: bool = True
    activo: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)

    def calcular_progreso(self, gastado: Decimal) -> dict:
        """Calcula el progreso del presupuesto en el periodo actual.

        Returns:
            Dict con: limite, gastado, porcentaje, zona (green/yellow/orange/red),
            dias_restantes, proyeccion.
        """
        if self.limite_mensual <= 0:
            return {"porcentaje": Decimal("0"), "zona": "green"}

        porcentaje = (gastado / self.limite_mensual) * 100

        if porcentaje >= 100:
            zona = "red"
        elif porcentaje >= 80:
            zona = "orange"
        elif porcentaje >= 50:
            zona = "yellow"
        else:
            zona = "green"

        return {
            "limite": self.limite_mensual,
            "gastado": gastado,
            "porcentaje": round(porcentaje, 2),
            "zona": zona,
        }

    def verificar_alertas(self, gastado: Decimal) -> list[str]:
        """Verifica si se deben disparar alertas (80% o 100%)."""
        alertas = []
        if self.limite_mensual <= 0:
            return alertas

        porcentaje = (gastado / self.limite_mensual) * 100

        if self.alerta_80pct and porcentaje >= 80 and porcentaje < 100:
            alertas.append("80pct")
        if self.alerta_100pct and porcentaje >= 100:
            alertas.append("100pct")

        return alertas

    def desactivar(self) -> None:
        """Desactiva el presupuesto sin eliminarlo."""
        self.activo = False

    def actualizar_limite(self, nuevo_limite: Decimal) -> None:
        """Actualiza el limite mensual del presupuesto."""
        if nuevo_limite < 0:
            raise ValueError("El limite mensual no puede ser negativo")
        self.limite_mensual = nuevo_limite
