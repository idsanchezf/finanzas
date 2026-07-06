"""Queries CQRS — Operaciones de lectura (sin efectos secundarios).

Cada query es un DTO inmutable que describe los parametros de consulta.
Los handlers retornan DTOs de respuesta sin modificar el estado del sistema.
"""

from src.application.queries.dashboard_by_category import DashboardByCategoryQuery
from src.application.queries.dashboard_daily import DashboardDailyQuery
from src.application.queries.dashboard_monthly_trend import DashboardMonthlyTrendQuery
from src.application.queries.dashboard_summary import DashboardSummaryQuery
from src.application.queries.obtener_extractos import ObtenerExtractosQuery
from src.application.queries.obtener_insights import ObtenerInsightsQuery
from src.application.queries.obtener_transacciones import ObtenerTransaccionesQuery

__all__ = [
    "DashboardSummaryQuery",
    "DashboardByCategoryQuery",
    "DashboardDailyQuery",
    "DashboardMonthlyTrendQuery",
    "ObtenerTransaccionesQuery",
    "ObtenerExtractosQuery",
    "ObtenerInsightsQuery",
]
