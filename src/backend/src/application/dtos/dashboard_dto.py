"""DTO: DashboardSummary — KPIs del dashboard."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DashboardSummaryDTO:
    """DTO con los KPIs principales del dashboard."""

    total_gastado: float = 0.0
    total_ingresos: float = 0.0
    promedio_diario: float = 0.0
    pct_cupo_utilizado: float = 0.0
    dias_para_corte: int = 0
    variacion_vs_anterior: float = 0.0
    score_salud_financiera: int = 75
