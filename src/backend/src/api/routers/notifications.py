"""Router de Notificaciones — Preferencias y listado de notificaciones in-app."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Query

from src.api.dependencies import get_current_user_id

router = APIRouter()


@router.get("")
async def list_notifications(
    leidas: bool = Query(False),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    user_id: str = Depends(get_current_user_id),
):
    """Lista notificaciones del usuario (in-app)."""
    return {"items": [], "total": 0, "page": page, "size": size}


@router.patch("/{notification_id}/read")
async def mark_as_read(notification_id: str):
    """Marca una notificacion como leida."""
    return {"id": notification_id, "leida": True}


@router.get("/preferences")
async def get_preferences(user_id: str = Depends(get_current_user_id)):
    """Preferencias de notificacion por tipo y canal."""
    return {
        "canales": {"push": True, "email": True},
        "tipos": {
            "recordatorio_pago": {"push": True, "email": True},
            "alerta_presupuesto": {"push": True, "email": True},
            "resumen_semanal": {"push": True, "email": False},
            "habito_detectado": {"push": True, "email": True},
            "recordatorio_corte": {"push": True, "email": False},
        },
    }


@router.put("/preferences")
async def update_preferences(
    body: dict = Body(...),
    user_id: str = Depends(get_current_user_id),
):
    """Actualiza preferencias de notificacion."""
    return body
