"""Comando: ClasificarTransaccionesMasivas.

Asigna la misma categoria a multiples transacciones seleccionadas por el usuario.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ClasificarTransaccionesMasivasCommand:
    """Comando para clasificar varias transacciones con la misma categoria.

    El handler:
    1. Valida que todas las transacciones pertenezcan al usuario.
    2. Actualiza categoria + confidence=100 (manual).
    3. Publica eventos CategoriaCorregida para aprendizaje del modelo.
    """

    usuario_id: UUID
    transaccion_ids: list[UUID]
    categoria_id: UUID
