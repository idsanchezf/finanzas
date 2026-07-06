"""Capa de dominio — Entidades, Value Objects, Eventos, Repositorios y Servicios de dominio.

Sin dependencias externas. Contiene la logica de negocio pura.
"""

from src.domain.entities import (
    Categoria,
    Extracto,
    MetaAhorro,
    Notificacion,
    Presupuesto,
    Tarjeta,
    Transaccion,
    Usuario,
)
from src.domain.value_objects import (
    ConfianzaClasificacion,
    Money,
    PeriodoFacturacion,
)

__all__ = [
    "Usuario",
    "Tarjeta",
    "Extracto",
    "Transaccion",
    "Categoria",
    "Presupuesto",
    "MetaAhorro",
    "Notificacion",
    "Money",
    "PeriodoFacturacion",
    "ConfianzaClasificacion",
]
