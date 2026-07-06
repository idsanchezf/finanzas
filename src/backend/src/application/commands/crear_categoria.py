"""Comando: CrearCategoria.

Crea una categoria o subcategoria personalizada para el usuario.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class CrearCategoriaCommand:
    """Comando para crear una categoria personalizada.

    El handler:
    1. Valida que el nombre no este duplicado.
    2. Crea la categoria con los datos proporcionados.
    3. Si es subcategoria, la asocia al parent_id.
    """

    usuario_id: UUID
    nombre: str
    icono: str = "📁"
    color: str = "#6B7280"
    parent_id: UUID | None = None
