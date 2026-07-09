"""Repositorio concreto de Presupuestos y Metas de Ahorro — SQLAlchemy 2.0 async.

Implementa IPresupuestoRepository para PresupuestoModel y
provee operaciones CRUD para MetaAhorroModel.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.repositories import IPresupuestoRepository
from src.infrastructure.persistence.models import MetaAhorroModel, PresupuestoModel


class PresupuestoRepository(IPresupuestoRepository):
    """Implementacion concreta del repositorio de presupuestos y metas de ahorro."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Presupuesto CRUD
    # ------------------------------------------------------------------

    async def get_by_id(self, presupuesto_id: uuid.UUID) -> PresupuestoModel | None:
        stmt = select(PresupuestoModel).where(PresupuestoModel.id == presupuesto_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_usuario(self, usuario_id: uuid.UUID) -> list[PresupuestoModel]:
        stmt = select(PresupuestoModel).where(PresupuestoModel.usuario_id == usuario_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def save(self, presupuesto: Any) -> Any:
        """Guarda o actualiza un presupuesto.

        Soporta tanto entidades de dominio (dataclass) como modelos ORM.
        """
        if hasattr(presupuesto, "_sa_instance_state"):
            # Es un modelo ORM ya tracked
            await self.session.merge(presupuesto)
        else:
            # Es una entidad de dominio (dataclass)
            modelo = PresupuestoModel(
                id=presupuesto.id,
                usuario_id=presupuesto.usuario_id,
                categoria_id=presupuesto.categoria_id,
                limite_mensual=presupuesto.limite_mensual
                if isinstance(presupuesto.limite_mensual, Decimal)
                else Decimal(str(presupuesto.limite_mensual)),
                alerta_80pct=presupuesto.alerta_80pct,
                alerta_100pct=presupuesto.alerta_100pct,
                activo=getattr(presupuesto, "activo", True),
            )
            self.session.add(modelo)
            presupuesto = modelo
        await self.session.flush()
        return presupuesto

    async def delete(self, presupuesto_id: uuid.UUID) -> None:
        presupuesto = await self.get_by_id(presupuesto_id)
        if presupuesto:
            await self.session.delete(presupuesto)
            await self.session.flush()

    # ------------------------------------------------------------------
    # MetaAhorro CRUD
    # ------------------------------------------------------------------

    async def get_meta_by_id(self, meta_id: uuid.UUID) -> MetaAhorroModel | None:
        stmt = select(MetaAhorroModel).where(MetaAhorroModel.id == meta_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_metas_by_usuario(self, usuario_id: uuid.UUID) -> list[MetaAhorroModel]:
        stmt = select(MetaAhorroModel).where(MetaAhorroModel.usuario_id == usuario_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def save_meta(self, meta: Any) -> Any:
        """Guarda o actualiza una meta de ahorro."""
        if hasattr(meta, "_sa_instance_state"):
            await self.session.merge(meta)
        else:
            # Es una entidad de dominio (dataclass)
            modelo = MetaAhorroModel(
                id=meta.id,
                usuario_id=meta.usuario_id,
                nombre=meta.nombre,
                monto_objetivo=meta.monto_objetivo
                if isinstance(meta.monto_objetivo, Decimal)
                else Decimal(str(meta.monto_objetivo)),
                monto_acumulado=meta.monto_acumulado
                if isinstance(meta.monto_acumulado, Decimal)
                else Decimal(str(meta.monto_acumulado)),
                fecha_deseada=meta.fecha_deseada,
            )
            self.session.add(modelo)
            meta = modelo
        await self.session.flush()
        return meta

    async def delete_meta(self, meta_id: uuid.UUID) -> None:
        meta = await self.get_meta_by_id(meta_id)
        if meta:
            await self.session.delete(meta)
            await self.session.flush()
