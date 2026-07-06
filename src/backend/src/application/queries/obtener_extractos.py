"""Query: ObtenerExtractos — Lista de extractos del usuario."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ObtenerExtractosQuery:
    """Consulta la lista de extractos del usuario con paginacion."""

    usuario_id: UUID
    tarjeta_id: UUID | None = None
    page: int = 1
    size: int = 12
