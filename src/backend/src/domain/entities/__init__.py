"""Entidades de dominio — Aggregate Roots y entidades hijas."""

from src.domain.entities.usuario import Usuario
from src.domain.entities.tarjeta import Tarjeta
from src.domain.entities.extracto import Extracto
from src.domain.entities.transaccion import Transaccion
from src.domain.entities.categoria import Categoria
from src.domain.entities.presupuesto import Presupuesto
from src.domain.entities.meta_ahorro import MetaAhorro
from src.domain.entities.notificacion import Notificacion

__all__ = [
    "Usuario",
    "Tarjeta",
    "Extracto",
    "Transaccion",
    "Categoria",
    "Presupuesto",
    "MetaAhorro",
    "Notificacion",
]
