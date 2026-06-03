"""Comando: CrearMetaAhorro.

Crea una meta de ahorro con objetivo financiero.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class CrearMetaAhorroCommand:
    """Comando para crear una meta de ahorro.

    El handler:
    1. Valida que el monto objetivo sea positivo.
    2. Crea la meta asociada al usuario.
    3. Inicializa el monto acumulado en 0.
    """

    usuario_id: UUID
    nombre: str
    monto_objetivo: Decimal
    fecha_deseada: date | None = None
