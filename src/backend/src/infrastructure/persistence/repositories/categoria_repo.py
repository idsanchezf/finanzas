"""Repositorio concreto de Categorias — SQLAlchemy 2.0 async."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.repositories import ICategoriaRepository
from src.infrastructure.persistence.models import CategoriaModel


class CategoriaRepository(ICategoriaRepository):
    """Implementacion concreta del repositorio de categorias."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, categoria_id: uuid.UUID) -> CategoriaModel | None:
        stmt = select(CategoriaModel).where(CategoriaModel.id == categoria_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, usuario_id: uuid.UUID | None = None) -> list[CategoriaModel]:
        """Retorna categorias predefinidas + personalizadas del usuario."""
        stmt = select(CategoriaModel).where(
            or_(
                CategoriaModel.es_predefinida is True,
                CategoriaModel.usuario_id == usuario_id,
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_predefinidas(self) -> list[CategoriaModel]:
        stmt = select(CategoriaModel).where(CategoriaModel.es_predefinida is True)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def save(self, categoria: Any) -> Any:
        if hasattr(categoria, "_sa_instance_state"):
            await self.session.merge(categoria)
        else:
            modelo = CategoriaModel(
                id=categoria.id,
                nombre=categoria.nombre,
                icono=categoria.icono,
                color=categoria.color,
                parent_id=categoria.parent_id,
                es_predefinida=categoria.es_predefinida,
                usuario_id=categoria.usuario_id,
                palabras_clave=categoria.palabras_clave,
            )
            self.session.add(modelo)
            categoria = modelo
        await self.session.flush()
        return categoria

    async def delete(self, categoria_id: uuid.UUID) -> None:
        categoria = await self.get_by_id(categoria_id)
        if categoria and not categoria.es_predefinida:
            await self.session.delete(categoria)
            await self.session.flush()

    async def buscar_por_nombre(
        self, nombre: str, usuario_id: uuid.UUID | None = None
    ) -> list[CategoriaModel]:
        """Busca categorias por coincidencia parcial en el nombre.

        Busca entre predefinidas y personalizadas del usuario.
        """
        conditions = [CategoriaModel.nombre.ilike(f"%{nombre}%")]
        if usuario_id is not None:
            conditions.append(
                or_(
                    CategoriaModel.es_predefinida is True,
                    CategoriaModel.usuario_id == usuario_id,
                )
            )
        else:
            conditions.append(CategoriaModel.es_predefinida is True)

        stmt = select(CategoriaModel).where(*conditions)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
