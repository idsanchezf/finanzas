"""Router de Dashboard — KPIs y visualizaciones financieras."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.dependencies import get_current_user_id, get_query_handler, get_redis
from src.application.queries.dashboard_by_category import DashboardByCategoryQuery
from src.application.queries.dashboard_daily import DashboardDailyQuery
from src.application.queries.dashboard_monthly_trend import DashboardMonthlyTrendQuery
from src.application.queries.dashboard_summary import DashboardSummaryQuery

router = APIRouter()


@router.get("/summary")
async def dashboard_summary(
    extract_id: str = Query(...),
    user_id: str = Depends(get_current_user_id),
    query_handler: Any = Depends(get_query_handler),
    redis: Any = Depends(get_redis),
):
    """KPIs del periodo actual. Cache Redis TTL 60s."""
    # Intentar cache
    cached = await redis.get_dashboard_summary(user_id, extract_id)
    if cached:
        return cached

    query = DashboardSummaryQuery(
        usuario_id=uuid.UUID(user_id),
        extracto_id=uuid.UUID(extract_id),
    )
    result = await query_handler.handle_dashboard_summary(query)

    # Guardar en cache
    await redis.set_dashboard_summary(user_id, extract_id, result, ttl=60)

    return result


@router.get("/by-category")
async def dashboard_by_category(
    extract_id: str = Query(...),
    top_n: int = Query(5, ge=1, le=14),
    user_id: str = Depends(get_current_user_id),
    query_handler: Any = Depends(get_query_handler),
    redis: Any = Depends(get_redis),
):
    """Distribucion de gasto por categoria para grafico Donut."""
    cached = await redis.get_dashboard_by_category(user_id, extract_id)
    if cached:
        return cached

    query = DashboardByCategoryQuery(
        usuario_id=uuid.UUID(user_id),
        extracto_id=uuid.UUID(extract_id),
        top_n=top_n,
    )
    result = await query_handler.handle_dashboard_by_category(query)

    await redis.set_dashboard_by_category(user_id, extract_id, result, ttl=60)
    return result


@router.get("/daily")
async def dashboard_daily(
    extract_id: str = Query(...),
    user_id: str = Depends(get_current_user_id),
    query_handler: Any = Depends(get_query_handler),
):
    """Gasto diario del periodo para grafico de Barras Apiladas."""
    query = DashboardDailyQuery(
        usuario_id=uuid.UUID(user_id),
        extracto_id=uuid.UUID(extract_id),
    )
    return await query_handler.handle_dashboard_daily(query)


@router.get("/monthly-trend")
async def dashboard_monthly_trend(
    meses: int = Query(6, ge=1, le=24),
    tarjeta_id: str | None = Query(None),
    user_id: str = Depends(get_current_user_id),
    query_handler: Any = Depends(get_query_handler),
):
    """Tendencia mensual de gastos/ingresos para grafico de Linea."""
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
    """Proyeccion de cuotas pendientes."""
    # TODO: Implementar usando CalculadorCuotas del dominio
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
    """Heatmap de gasto diario anual."""
    return {
        "items": [],
        "year": year,
        "message": "Heatmap — proximamente",
    }
