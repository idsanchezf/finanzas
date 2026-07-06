"""Repositorio concreto de Tarjetas — SQLAlchemy 2.0 async."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.repositories import ITarjetaRepository
from src.infrastructure.persistence.models import TarjetaModel


class TarjetaRepository(ITarjetaRepository):
    """Implementacion concreta del repositorio de tarjetas."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, tarjeta_id: uuid.UUID) -> TarjetaModel | None:
        stmt = select(TarjetaModel).where(TarjetaModel.id == tarjeta_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_usuario(self, usuario_id: uuid.UUID) -> list[TarjetaModel]:
        stmt = select(TarjetaModel).where(TarjetaModel.usuario_id == usuario_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def save(self, tarjeta: Any) -> Any:
        if hasattr(tarjeta, "_sa_instance_state"):
            await self.session.merge(tarjeta)
        else:
            modelo = TarjetaModel(
                id=tarjeta.id,
                usuario_id=tarjeta.usuario_id,
                banco=tarjeta.banco,
                ultimos_4_digitos=tarjeta.ultimos_4_digitos,
                tipo=tarjeta.tipo.value if hasattr(tarjeta.tipo, "value") else tarjeta.tipo,
                alias=tarjeta.alias,
                activa=tarjeta.activa,
            )
            self.session.add(modelo)
            tarjeta = modelo
        await self.session.flush()
        return tarjeta

    async def delete(self, tarjeta_id: uuid.UUID) -> None:
        tarjeta = await self.get_by_id(tarjeta_id)
        if tarjeta:
            await self.session.delete(tarjeta)
            await self.session.flush()
