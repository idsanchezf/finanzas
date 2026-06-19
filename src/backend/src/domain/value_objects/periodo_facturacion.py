"""Value Object PeriodoFacturacion — Rango de fechas del ciclo de facturacion."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class PeriodoFacturacion:
    """Periodo de facturacion con fechas de inicio, fin y corte."""

    fecha_inicio: date
    fecha_fin: date
    fecha_corte: date | None = None
    fecha_limite_pago: date | None = None

    def __post_init__(self) -> None:
        if self.fecha_inicio > self.fecha_fin:
            raise ValueError(
                f"fecha_inicio ({self.fecha_inicio}) debe ser anterior a "
                f"fecha_fin ({self.fecha_fin})"
            )

    @property
    def duracion_dias(self) -> int:
        """Duracion del periodo en dias."""
        return (self.fecha_fin - self.fecha_inicio).days

    @property
    def dias_restantes(self) -> int:
        """Dias restantes hasta el final del periodo."""
        delta = self.fecha_fin - date.today()
        return max(0, delta.days)

    @property
    def dias_para_corte(self) -> int | None:
        """Dias restantes hasta la fecha de corte."""
        if self.fecha_corte:
            delta = self.fecha_corte - date.today()
            return max(0, delta.days)
        return None

    @property
    def dias_para_pago(self) -> int | None:
        """Dias restantes hasta la fecha limite de pago."""
        if self.fecha_limite_pago:
            delta = self.fecha_limite_pago - date.today()
            return max(0, delta.days)
        return None

    def contiene(self, d: date) -> bool:
        """Verifica si una fecha esta dentro del periodo."""
        return self.fecha_inicio <= d <= self.fecha_fin

    @property
    def etiqueta(self) -> str:
        """Etiqueta legible: 'Jun 2026'."""
        meses = [
            "Ene", "Feb", "Mar", "Abr", "May", "Jun",
            "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
        ]
        mes = meses[self.fecha_inicio.month - 1]
        return f"{mes} {self.fecha_inicio.year}"
