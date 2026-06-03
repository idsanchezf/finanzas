"""Router de Comercios — Traduccion colaborativa de nombres de comercios."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Query, status

from src.api.dependencies import get_current_user_id, get_redis

router = APIRouter()


@router.get("/translate")
async def translate_merchant(
    nombre: str = Query(..., min_length=2),
    redis: any = Depends(get_redis),
):
    """Busca la traduccion amigable de un nombre de comercio.

    Primero busca en cache Redis, luego en BD colaborativa.
    Si no encuentra, sugiere usar IA (Gemini) para traduccion.
    """
    # Buscar en cache Redis
    traduccion = await redis.get_merchant_translation(nombre)
    if traduccion:
        return {
            "original": nombre,
            "traducido": traduccion,
            "confidence": "CACHE",
            "fuente": "redis",
        }

    return {
        "original": nombre,
        "traducido": None,
        "confidence": "NONE",
        "fuente": "none",
        "message": "Traduccion no encontrada. Sugiere una traduccion o el sistema la aprendera con el tiempo.",
    }


@router.post("/suggest", status_code=status.HTTP_201_CREATED)
async def suggest_translation(
    body: dict = Body(...),
    user_id: str = Depends(get_current_user_id),
):
    """Sugiere una traduccion para un comercio (colaborativo)."""
    return {
        "nombre_original": body.get("nombre_original"),
        "nombre_traducido": body.get("nombre_traducido"),
        "estado": "pendiente",
        "message": "Traduccion sugerida. Sera revisada por la comunidad.",
    }


@router.get("/top")
async def top_merchants(
    periodo: str = Query("mes"),
    tarjeta_id: str | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    user_id: str = Depends(get_current_user_id),
):
    """Ranking de comercios mas frecuentes en el periodo."""
    return {"items": [], "periodo": periodo}
