"""Router de Presupuestos y Metas — Gestion de limites de gasto y ahorro."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status

from src.api.dependencies import (
    get_command_handler,
    get_current_user_id,
    get_presupuesto_repo,
)
from src.application.commands.crear_meta import CrearMetaAhorroCommand
from src.application.commands.crear_presupuesto import CrearPresupuestoCommand

router = APIRouter()


@router.get("")
async def list_budgets(
    user_id: str = Depends(get_current_user_id),
    presupuesto_repo: Any = Depends(get_presupuesto_repo),
):
    """Lista presupuestos del usuario."""
    presupuestos = await presupuesto_repo.get_by_usuario(uuid.UUID(user_id))
    return {
        "items": [
            {
                "id": str(p.id),
                "categoria_id": str(p.categoria_id),
                "limite_mensual": float(p.limite_mensual),
                "alerta_80pct": p.alerta_80pct,
                "alerta_100pct": p.alerta_100pct,
                "activo": p.activo,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in presupuestos
        ]
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_budget(
    body: dict = Body(...),
    user_id: str = Depends(get_current_user_id),
    command_handler: Any = Depends(get_command_handler),
):
    """Crea un presupuesto por categoria."""
    cmd = CrearPresupuestoCommand(
        usuario_id=uuid.UUID(user_id),
        categoria_id=uuid.UUID(body["category_id"]),
        limite_mensual=Decimal(str(body["limite_mensual"])),
        alerta_80pct=body.get("alerta_80pct", True),
        alerta_100pct=body.get("alerta_100pct", True),
    )

    try:
        return await command_handler.handle_crear_presupuesto(cmd)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get("/goals")
async def list_goals(
    user_id: str = Depends(get_current_user_id),
    presupuesto_repo: Any = Depends(get_presupuesto_repo),
):
    """Lista metas de ahorro."""
    metas = await presupuesto_repo.get_metas_by_usuario(uuid.UUID(user_id))
    return {
        "items": [
            {
                "id": str(m.id),
                "nombre": m.nombre,
                "monto_objetivo": float(m.monto_objetivo),
                "monto_acumulado": float(m.monto_acumulado),
                "fecha_deseada": m.fecha_deseada.isoformat() if m.fecha_deseada else None,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in metas
        ]
    }


@router.post("/goals", status_code=status.HTTP_201_CREATED)
async def create_goal(
    body: dict = Body(...),
    user_id: str = Depends(get_current_user_id),
    command_handler: Any = Depends(get_command_handler),
):
    """Crea una meta de ahorro."""
    cmd = CrearMetaAhorroCommand(
        usuario_id=uuid.UUID(user_id),
        nombre=body.get("nombre", ""),
        monto_objetivo=Decimal(str(body.get("monto_objetivo", 0))),
    )

    try:
        return await command_handler.handle_crear_meta(cmd)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post("/simulate")
async def simulate(body: dict = Body(...)):
    """Simulador 'que pasaria si' con ajustes de gasto por categoria."""
    return {
        "proyeccion_1m": 0,
        "proyeccion_3m": 0,
        "proyeccion_6m": 0,
        "proyeccion_12m": 0,
        "impacto_score": 0,
        "ahorro_estimado": 0,
        "message": "Simulador — proximamente",
    }
