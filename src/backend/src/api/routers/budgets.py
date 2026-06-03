"""Router de Presupuestos y Metas — Gestion de limites de gasto y ahorro."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status

from src.api.dependencies import get_current_user_id, get_command_handler
from src.application.commands.crear_meta import CrearMetaAhorroCommand
from src.application.commands.crear_presupuesto import CrearPresupuestoCommand

router = APIRouter()


@router.get("")
async def list_budgets(user_id: str = Depends(get_current_user_id)):
    """Lista presupuestos del usuario."""
    return {"items": []}


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
async def list_goals():
    """Lista metas de ahorro."""
    return {"items": []}


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
