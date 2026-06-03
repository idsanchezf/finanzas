"""Query: DashboardSummary — KPIs del periodo actual."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class DashboardSummaryQuery:
    """Consulta los KPIs principales del dashboard para un extracto.

    Retorna:
    - total_gastado
    - total_ingresos
    - promedio_diario
    - porcentaje_cupo_utilizado
    - dias_para_corte
    - variacion_vs_anterior
    """

    usuario_id: UUID
    extracto_id: UUID
