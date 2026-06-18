"""Router de Dashboard — KPIs y visualizaciones financieras."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_current_user_id, get_query_handler, get_redis
from src.application.queries.dashboard_by_category import DashboardByCategoryQuery
from src.application.queries.dashboard_daily import DashboardDailyQuery
from src.application.queries.dashboard_monthly_trend import DashboardMonthlyTrendQuery
from src.application.queries.dashboard_summary import DashboardSummaryQuery

logger = logging.getLogger(__name__)

router = APIRouter()


async def _try_get_cache(redis: Any, cache_method: str, *args: Any) -> dict | None:
    """Intenta obtener datos del cache Redis. Retorna None si Redis no esta disponible."""
    try:
        method = getattr(redis, cache_method, None)
        if method:
            return await method(*args)
    except Exception as e:
        logger.debug(f"Cache miss (Redis no disponible): {e}")
    return None


async def _try_set_cache(redis: Any, cache_method: str, *args: Any) -> None:
    """Intenta guardar datos en cache Redis. Silencia errores si Redis no esta disponible."""
    try:
        method = getattr(redis, cache_method, None)
        if method:
            await method(*args)
    except Exception as e:
        logger.debug(f"Cache set fallido (Redis no disponible): {e}")


@router.get("/summary")
async def dashboard_summary(
    extract_id: str = Query(..., description="ID del extracto a consultar"),
    user_id: str = Depends(get_current_user_id),
    query_handler: Any = Depends(get_query_handler),
    redis: Any = Depends(get_redis),
):
    """KPIs del periodo actual.

    Retorna total gastado, ingresos, promedio diario, % cupo utilizado,
    dias hasta fecha de pago y variacion vs mes anterior.
    Cache Redis TTL 60s.
    """
    # Intentar cache
    cached = await _try_get_cache(redis, "get_dashboard_summary", user_id, extract_id)
    if cached:
        return cached

    query = DashboardSummaryQuery(
        usuario_id=uuid.UUID(user_id),
        extracto_id=uuid.UUID(extract_id),
    )
    try:
        result = await query_handler.handle_dashboard_summary(query)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Guardar en cache
    await _try_set_cache(redis, "set_dashboard_summary", user_id, extract_id, result, 60)

    return result


@router.get("/by-category")
async def dashboard_by_category(
    extract_id: str = Query(..., description="ID del extracto a consultar"),
    top_n: int = Query(5, ge=1, le=14, description="Numero de categorias top a mostrar"),
    user_id: str = Depends(get_current_user_id),
    query_handler: Any = Depends(get_query_handler),
    redis: Any = Depends(get_redis),
):
    """Distribucion de gasto por categoria para grafico Donut.

    Retorna top N categorias por monto gastado, con porcentajes y colores.
    Las categorias fuera del top N se agrupan en 'otros'.
    """
    cached = await _try_get_cache(redis, "get_dashboard_by_category", user_id, extract_id)
    if cached:
        return cached

    query = DashboardByCategoryQuery(
        usuario_id=uuid.UUID(user_id),
        extracto_id=uuid.UUID(extract_id),
        top_n=top_n,
    )
    result = await query_handler.handle_dashboard_by_category(query)

    await _try_set_cache(redis, "set_dashboard_by_category", user_id, extract_id, result, 60)
    return result


@router.get("/daily")
async def dashboard_daily(
    extract_id: str = Query(..., description="ID del extracto a consultar"),
    user_id: str = Depends(get_current_user_id),
    query_handler: Any = Depends(get_query_handler),
):
    """Gasto diario del periodo para grafico de Barras Apiladas.

    Retorna gasto total por dia, con desglose por categoria dentro de cada dia.
    Solo incluye gastos (excluye abonos/pagos).
    """
    query = DashboardDailyQuery(
        usuario_id=uuid.UUID(user_id),
        extracto_id=uuid.UUID(extract_id),
    )
    return await query_handler.handle_dashboard_daily(query)


@router.get("/monthly-trend")
async def dashboard_monthly_trend(
    meses: int = Query(6, ge=1, le=24, description="Numero de meses a consultar"),
    tarjeta_id: str | None = Query(None, description="Filtrar por tarjeta especifica"),
    user_id: str = Depends(get_current_user_id),
    query_handler: Any = Depends(get_query_handler),
):
    """Tendencia mensual de gastos/ingresos para grafico de Linea.

    Retorna serie temporal con gastos, ingresos, saldo neto por mes.
    Incluye promedio movil de 3 meses y tendencia general.
    """
    query = DashboardMonthlyTrendQuery(
        usuario_id=uuid.UUID(user_id),
        tarjeta_id=uuid.UUID(tarjeta_id) if tarjeta_id else None,
        meses=meses,
    )
    return await query_handler.handle_dashboard_monthly_trend(query)


@router.get("/installments")
async def dashboard_installments(
    tarjeta_id: str = Query(...),
    user_id: str = Depends(get_current_user_id),
):
    """Proyeccion de cuotas pendientes — stub MVP."""
    return {
        "items": [],
        "message": "Proyeccion de cuotas — proximamente",
    }


@router.get("/calendar-heatmap")
async def dashboard_calendar_heatmap(
    year: int = Query(2026, ge=2020, le=2030),
    tarjeta_id: str = Query(...),
    user_id: str = Depends(get_current_user_id),
):
    """Heatmap de gasto diario anual — stub MVP."""
    return {
        "items": [],
        "year": year,
        "message": "Heatmap — proximamente",
    }
