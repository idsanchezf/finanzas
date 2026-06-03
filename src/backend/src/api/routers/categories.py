"""Router de Categorias — Gestion de categorias de gasto."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status

from src.api.dependencies import get_categoria_repo, get_current_user_id, get_command_handler
from src.application.commands.crear_categoria import CrearCategoriaCommand

router = APIRouter()


@router.get("")
async def list_categories(
    user_id: str = Depends(get_current_user_id),
    categoria_repo: Any = Depends(get_categoria_repo),
):
    """Lista categorias (predefinidas + personalizadas del usuario)."""
    categorias = await categoria_repo.get_all(uuid.UUID(user_id))
    return {
        "items": [
            {
                "id": str(c.id),
                "nombre": c.nombre,
                "icono": c.icono,
                "color": c.color,
                "parent_id": str(c.parent_id) if c.parent_id else None,
                "es_predefinida": c.es_predefinida,
                "subcategorias": [
                    {"id": str(s.id), "nombre": s.nombre, "icono": s.icono}
                    for s in getattr(c, "subcategorias", [])
                ],
            }
            for c in categorias
            if not c.parent_id  # Solo categorias raiz
        ],
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_category(
    body: dict = Body(...),
    user_id: str = Depends(get_current_user_id),
    command_handler: Any = Depends(get_command_handler),
):
    """Crea una categoria o subcategoria personalizada."""
    cmd = CrearCategoriaCommand(
        usuario_id=uuid.UUID(user_id),
        nombre=body.get("nombre", ""),
        icono=body.get("icono", "📁"),
        color=body.get("color", "#6B7280"),
        parent_id=uuid.UUID(body["parent_id"]) if body.get("parent_id") else None,
    )

    if not cmd.nombre:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="nombre es requerido")

    return await command_handler.handle_crear_categoria(cmd)


@router.put("/{category_id}")
async def update_category(
    category_id: str,
    body: dict = Body(...),
    categoria_repo: Any = Depends(get_categoria_repo),
):
    """Actualiza nombre, icono o color de una categoria."""
    categoria = await categoria_repo.get_by_id(uuid.UUID(category_id))
    if not categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria no encontrada")

    if "nombre" in body:
        categoria.nombre = body["nombre"]
    if "icono" in body:
        categoria.icono = body["icono"]
    if "color" in body:
        categoria.color = body["color"]

    await categoria_repo.save(categoria)
    return {"id": str(categoria.id), "nombre": categoria.nombre}


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: str,
    categoria_repo: Any = Depends(get_categoria_repo),
):
    """Elimina una categoria personalizada (no predefinidas)."""
    categoria = await categoria_repo.get_by_id(uuid.UUID(category_id))
    if not categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria no encontrada")
    if categoria.es_predefinida:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pueden eliminar categorias predefinidas",
        )

    await categoria_repo.delete(uuid.UUID(category_id))
