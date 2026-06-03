"""Query: DashboardDaily — Gasto diario del periodo."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class DashboardDailyQuery:
    """Consulta el gasto diario del periodo para grafico de Barras Apiladas.

    Retorna:
    - items: [{dia, total, categorias: {cat_id: monto}}]
    - promedio
    """

    usuario_id: UUID
    extracto_id: UUID
