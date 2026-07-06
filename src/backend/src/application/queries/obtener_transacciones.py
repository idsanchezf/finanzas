"""Query: ObtenerTransacciones — Lista de transacciones con filtros."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ObtenerTransaccionesQuery:
    """Consulta la lista de transacciones con filtros y paginacion."""

    usuario_id: UUID
    extracto_id: UUID | None = None
    categoria_id: UUID | None = None
    confidence: str | None = None  # "HIGH", "MEDIUM", "LOW"
    search: str | None = None
    page: int = 1
    size: int = 50
    sort_by: str = "fecha"
    order: str = "desc"
