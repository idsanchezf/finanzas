"""Query: DashboardByCategory — Distribucion de gasto por categoria."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class DashboardByCategoryQuery:
    """Consulta la distribucion del gasto por categoria para el grafico Donut.

    Retorna:
    - items: [{categoria, total, porcentaje, color}]
    - otros: {total, porcentaje} (categorias fuera del top_n)
    """

    usuario_id: UUID
    extracto_id: UUID
    top_n: int = 5
