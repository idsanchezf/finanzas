"""Value Objects del dominio — Inmutables, sin identidad propia."""

from src.domain.value_objects.money import Money
from src.domain.value_objects.periodo_facturacion import PeriodoFacturacion
from src.domain.value_objects.confianza import ConfianzaClasificacion

__all__ = [
    "Money",
    "PeriodoFacturacion",
    "ConfianzaClasificacion",
]
