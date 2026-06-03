"""Comando: CrearPresupuesto.

Crea un presupuesto mensual para una categoria de gasto.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class CrearPresupuestoCommand:
    """Comando para crear un presupuesto por categoria.

    El handler:
    1. Valida que el limite sea positivo.
    2. Crea el presupuesto asociado al usuario y categoria.
    3. Configura alertas de 80% y 100% segun preferencia.
    """

    usuario_id: UUID
    categoria_id: UUID
    limite_mensual: Decimal
    alerta_80pct: bool = True
    alerta_100pct: bool = True
