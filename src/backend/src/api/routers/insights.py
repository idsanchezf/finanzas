"""Router de Insights — Alertas financieras y score de salud."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query

from src.api.dependencies import get_current_user_id, get_query_handler
from src.application.queries.obtener_insights import ObtenerInsightsQuery

router = APIRouter()


@router.get("")
async def get_insights(
    extract_id: str = Query(...),
    user_id: str = Depends(get_current_user_id),
    query_handler: Any = Depends(get_query_handler),
):
    """Alertas y habitos detectados para el periodo actual."""
    query = ObtenerInsightsQuery(
        usuario_id=uuid.UUID(user_id),
        extracto_id=uuid.UUID(extract_id),
    )
    return await query_handler.handle_obtener_insights(query)


@router.get("/score")
async def get_financial_score(
    tarjeta_id: str = Query(...),
    user_id: str = Depends(get_current_user_id),
):
    """Score de salud financiera 0-100 con desglose por componente."""
    return {
        "score": 75,
        "zona": "healthy",
        "componentes": {
            "esenciales_vs_discrecionales": 80,
            "ingresos_vs_gastos": 70,
            "tendencia_ahorro": 65,
            "diversificacion": 72,
            "cuotas_vs_contado": 85,
        },
        "historico": [],
        "message": "Score financiero — proximamente",
    }
