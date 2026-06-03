"""Comando: CorregirCategoria.

El usuario corrige manualmente la categoria de una transaccion.
Dispara el evento de aprendizaje para el modelo ML.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class CorregirCategoriaCommand:
    """Comando para corregir la categoria de una transaccion.

    El handler:
    1. Obtiene la transaccion actual.
    2. Actualiza la categoria y confidence=100.
    3. Publica CategoriaCorregida para reentrenar el modelo ML.
    4. Aplica propagacion retroactiva al mismo comercio (BN-09).
    """

    usuario_id: UUID
    transaccion_id: UUID
    categoria_id: UUID
