"""Router de Transacciones — Consulta, clasificacion y correccion de transacciones."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from src.api.dependencies import (
    get_command_handler,
    get_current_user_id,
    get_query_handler,
    get_transaccion_repo,
)
from src.application.commands.clasificar_masivas import ClasificarTransaccionesMasivasCommand
from src.application.commands.corregir_categoria import CorregirCategoriaCommand
from src.application.queries.obtener_transacciones import ObtenerTransaccionesQuery

router = APIRouter()


# ============================================================
# Rutas fijas (antes de las rutas con parametros de path)
# ============================================================

@router.get("/search")
async def search_transactions(
    q: str = Query(..., min_length=2),
    extract_id: str | None = Query(None),
    user_id: str = Depends(get_current_user_id),
    transaccion_repo: Any = Depends(get_transaccion_repo),
):
    """Busqueda full-text por nombre de comercio."""
    items = await transaccion_repo.search_comercio(uuid.UUID(user_id), q)
    return {
        "items": [
            {"id": str(t.id), "comercio": t.comercio_original, "valor": float(t.valor)}
            for t in items
        ]
    }


@router.get("/unclassified/list")
async def get_unclassified(
    extract_id: str = Query(...),
    transaccion_repo: Any = Depends(get_transaccion_repo),
):
    """Transacciones con confianza baja (<70%) pendientes de confirmacion."""
    items = await transaccion_repo.get_unclassified(uuid.UUID(extract_id))
    return {
        "items": [
            {"id": str(t.id), "comercio": t.comercio_original, "valor": float(abs(t.valor))}
            for t in items
        ],
        "count": len(items),
    }


@router.patch("/bulk/category")
async def bulk_update_category(
    body: dict = Body(...),
    user_id: str = Depends(get_current_user_id),
    command_handler: Any = Depends(get_command_handler),
):
    """Clasificacion masiva — asigna la misma categoria a multiples transacciones."""
    transaction_ids = body.get("transaction_ids", [])
    categoria_id = body.get("category_id")

    if not transaction_ids or not categoria_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="transaction_ids y category_id son requeridos",
        )

    cmd = ClasificarTransaccionesMasivasCommand(
        usuario_id=uuid.UUID(user_id),
        transaccion_ids=[uuid.UUID(tid) for tid in transaction_ids],
        categoria_id=uuid.UUID(categoria_id),
    )

    return await command_handler.handle_clasificacion_masiva(cmd)


# ============================================================
# Rutas principales
# ============================================================

@router.get("")
async def list_transactions(
    extract_id: str | None = Query(None),
    category_id: str | None = Query(None),
    confidence: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    sort_by: str = Query("fecha"),
    order: str = Query("desc"),
    user_id: str = Depends(get_current_user_id),
    query_handler: Any = Depends(get_query_handler),
):
    """Lista transacciones con filtros y paginacion."""
    query = ObtenerTransaccionesQuery(
        usuario_id=uuid.UUID(user_id),
        extracto_id=uuid.UUID(extract_id) if extract_id else None,
        categoria_id=uuid.UUID(category_id) if category_id else None,
        confidence=confidence,
        search=search,
        page=page,
        size=size,
        sort_by=sort_by,
        order=order,
    )
    return await query_handler.handle_obtener_transacciones(query)


@router.get("/{transaction_id}")
async def get_transaction(
    transaction_id: str,
    transaccion_repo: Any = Depends(get_transaccion_repo),
):
    """Obtiene el detalle completo de una transaccion."""
    t = await transaccion_repo.get_by_id(uuid.UUID(transaction_id))
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaccion no encontrada")

    return {
        "id": str(t.id),
        "extracto_id": str(t.extracto_id),
        "autorizacion": t.numero_autorizacion,
        "fecha": t.fecha.isoformat() if t.fecha else None,
        "comercio": t.comercio_original,
        "comercio_traducido": t.comercio_traducido,
        "valor": float(t.valor),
        "cuotas": t.numero_cuotas,
        "cuotas_totales": t.cuotas_totales,
        "cuota_actual": t.cuota_actual,
        "moneda_original": t.moneda_original,
        "valor_moneda_original": float(t.valor_moneda_original) if t.valor_moneda_original else None,
        "categoria_id": str(t.categoria_id) if t.categoria_id else None,
        "confidence": float(t.confidence) if t.confidence else None,
    }


@router.patch("/{transaction_id}/category")
async def update_transaction_category(
    transaction_id: str,
    body: dict[str, str] = Body(...),
    user_id: str = Depends(get_current_user_id),
    command_handler: Any = Depends(get_command_handler),
):
    """Cambia la categoria de una transaccion. Dispara aprendizaje del modelo ML."""
    categoria_id = body.get("category_id")
    if not categoria_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="category_id es requerido")

    cmd = CorregirCategoriaCommand(
        usuario_id=uuid.UUID(user_id),
        transaccion_id=uuid.UUID(transaction_id),
        categoria_id=uuid.UUID(categoria_id),
    )

    try:
        return await command_handler.handle_corregir_categoria(cmd)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
