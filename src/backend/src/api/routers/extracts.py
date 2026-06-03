"""Router de Extractos — Carga, consulta y gestion de extractos bancarios."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from src.api.dependencies import (
    get_command_handler,
    get_current_user_id,
    get_extracto_repo,
    get_query_handler,
    get_storage_client,
)
from src.application.commands.cargar_extracto import CargarExtractoCommand
from src.application.queries.obtener_extractos import ObtenerExtractosQuery

router = APIRouter()


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_extract(
    file: UploadFile = File(...),
    tarjeta_id: str = Query(..., description="ID de la tarjeta"),
    user_id: str = Depends(get_current_user_id),
    command_handler: Any = Depends(get_command_handler),
    storage: Any = Depends(get_storage_client),
):
    """Carga un archivo Excel de extracto bancario y registra su procesamiento.

    El archivo se almacena en R2 y se publica el evento ExtractoCargado
    para que el worker de procesamiento lo procese asincronicamente.
    """
    # Validar formato
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se aceptan archivos Excel (.xlsx, .xls)",
        )

    # Validar tamano maximo (10MB)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo excede el tamano maximo permitido (10MB)",
        )

    # Subir a R2
    try:
        s3_key = f"{user_id}/extracts/{uuid.uuid4()}/{file.filename}"
        storage.upload_file(
            bucket="finance-extracts",
            key=s3_key,
            file_content=content,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al almacenar el archivo: {str(e)}",
        ) from e

    # Registrar extracto via command
    cmd = CargarExtractoCommand(
        usuario_id=uuid.UUID(user_id),
        tarjeta_id=uuid.UUID(tarjeta_id),
        filename=file.filename,
        file_content=content,
    )

    try:
        result = await command_handler.handle_cargar_extracto(cmd)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar el extracto: {str(e)}",
        ) from e

    return result


@router.get("")
async def list_extracts(
    tarjeta_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(12, ge=1, le=50),
    user_id: str = Depends(get_current_user_id),
    query_handler: Any = Depends(get_query_handler),
):
    """Lista los extractos del usuario autenticado con paginacion."""
    query = ObtenerExtractosQuery(
        usuario_id=uuid.UUID(user_id),
        tarjeta_id=uuid.UUID(tarjeta_id) if tarjeta_id else None,
        page=page,
        size=size,
    )
    return await query_handler.handle_obtener_extractos(query)


@router.get("/{extract_id}")
async def get_extract(
    extract_id: str,
    user_id: str = Depends(get_current_user_id),
    extracto_repo: Any = Depends(get_extracto_repo),
):
    """Obtiene el detalle de un extracto especifico."""
    extracto = await extracto_repo.get_by_id(uuid.UUID(extract_id))
    if not extracto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Extracto no encontrado")

    return {
        "id": str(extracto.id),
        "estado": extracto.estado,
        "tarjeta_id": str(extracto.tarjeta_id),
        "periodo_inicio": extracto.periodo_inicio.isoformat() if extracto.periodo_inicio else None,
        "periodo_fin": extracto.periodo_fin.isoformat() if extracto.periodo_fin else None,
        "fecha_corte": extracto.fecha_corte.isoformat() if extracto.fecha_corte else None,
        "fecha_limite_pago": extracto.fecha_limite_pago.isoformat() if extracto.fecha_limite_pago else None,
        "pago_minimo": float(extracto.pago_minimo),
        "pago_total": float(extracto.pago_total),
        "cupo_total": float(extracto.cupo_total),
        "cupo_disponible": float(extracto.cupo_disponible),
        "progress_pct": extracto.progress_pct,
        "created_at": extracto.created_at.isoformat() if extracto.created_at else None,
    }


@router.get("/{extract_id}/status")
async def get_extract_status(
    extract_id: str,
    extracto_repo: Any = Depends(get_extracto_repo),
):
    """Estado del procesamiento asincrono (polling para barra de progreso)."""
    extracto = await extracto_repo.get_by_id(uuid.UUID(extract_id))
    if not extracto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Extracto no encontrado")

    return {
        "status": extracto.estado,
        "progress_pct": extracto.progress_pct,
        "message": extracto.error_message if extracto.estado == "ERROR" else None,
    }


@router.delete("/{extract_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_extract(
    extract_id: str,
    user_id: str = Depends(get_current_user_id),
    extracto_repo: Any = Depends(get_extracto_repo),
):
    """Elimina un extracto y todas sus transacciones asociadas."""
    try:
        await extracto_repo.delete(uuid.UUID(extract_id))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar el extracto: {str(e)}",
        ) from e
