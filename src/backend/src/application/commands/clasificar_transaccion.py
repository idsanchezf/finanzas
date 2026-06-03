"""Comando: ClasificarTransaccion.

Clasifica una transaccion individual con el motor hibrido (reglas + ML).
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ClasificarTransaccionCommand:
    """Comando para clasificar una transaccion especifica.

    El handler ejecuta el pipeline de clasificacion:
    1. Reglas deterministicas (palabras clave).
    2. ML si las reglas no tienen confianza suficiente.
    3. Asigna categoria + confidence.
    """

    transaccion_id: UUID
    extracto_id: UUID
    usuario_id: UUID
