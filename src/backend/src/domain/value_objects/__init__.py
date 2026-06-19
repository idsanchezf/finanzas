"""Value Objects del dominio — Inmutables, sin identidad propia."""

from src.domain.value_objects.confianza import ConfianzaClasificacion
from src.domain.value_objects.money import Money
from src.domain.value_objects.periodo_facturacion import PeriodoFacturacion

__all__ = [
    "Money",
    "PeriodoFacturacion",
    "ConfianzaClasificacion",
]
