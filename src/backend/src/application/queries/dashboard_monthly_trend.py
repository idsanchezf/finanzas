"""Query: DashboardMonthlyTrend — Tendencia mensual."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class DashboardMonthlyTrendQuery:
    """Consulta la tendencia mensual de gastos/ingresos para grafico de Linea.

    Retorna:
    - items: [{mes, gastos, ingresos, saldo_neto}]
    - promedio_movil
    """

    usuario_id: UUID
    tarjeta_id: UUID | None = None
    meses: int = 6
