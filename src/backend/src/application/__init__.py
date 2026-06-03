"""Capa de aplicacion — Casos de uso (CQRS: commands + queries).

Orquesta la logica de negocio del dominio. Depende solo de la capa de dominio.
Define los handlers que ejecutan los casos de uso.
"""

from src.application.commands import (
    CargarExtractoCommand,
    ClasificarTransaccionCommand,
    ClasificarTransaccionesMasivasCommand,
    CrearCategoriaCommand,
    CrearPresupuestoCommand,
    CorregirCategoriaCommand,
    CrearMetaAhorroCommand,
)
from src.application.queries import (
    DashboardByCategoryQuery,
    DashboardDailyQuery,
    DashboardMonthlyTrendQuery,
    DashboardSummaryQuery,
)

__all__ = [
    "CargarExtractoCommand",
    "ClasificarTransaccionCommand",
    "ClasificarTransaccionesMasivasCommand",
    "CrearCategoriaCommand",
    "CrearPresupuestoCommand",
    "CorregirCategoriaCommand",
    "CrearMetaAhorroCommand",
    "DashboardSummaryQuery",
    "DashboardByCategoryQuery",
    "DashboardDailyQuery",
    "DashboardMonthlyTrendQuery",
]
