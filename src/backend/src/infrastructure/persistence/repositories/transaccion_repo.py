"""Repositorio concreto de Transacciones — SQLAlchemy 2.0 async."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.models import TransaccionModel
from src.domain.repositories import ITransaccionRepository


class TransaccionRepository(ITransaccionRepository):
    """Implementacion concreta del repositorio de transacciones."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, transaccion_id: uuid.UUID) -> TransaccionModel | None:
        stmt = select(TransaccionModel).where(TransaccionModel.id == transaccion_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_extracto(
        self, extracto_id: uuid.UUID, filters: dict[str, Any] | None = None
    ) -> list[TransaccionModel]:
        stmt = select(TransaccionModel).where(TransaccionModel.extracto_id == extracto_id)
        if filters:
            if "categoria_id" in filters:
                stmt = stmt.where(TransaccionModel.categoria_id == filters["categoria_id"])
        stmt = stmt.order_by(TransaccionModel.fecha.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_usuario(
        self, usuario_id: uuid.UUID, filters: dict[str, Any] | None = None,
        page: int = 1, size: int = 50
    ) -> tuple[list[TransaccionModel], int]:
        stmt = select(TransaccionModel).where(TransaccionModel.usuario_id == usuario_id)

        if filters:
            if "extracto_id" in filters:
                stmt = stmt.where(TransaccionModel.extracto_id == filters["extracto_id"])
            if "categoria_id" in filters:
                stmt = stmt.where(TransaccionModel.categoria_id == filters["categoria_id"])
            if "search" in filters:
                stmt = stmt.where(
                    TransaccionModel.comercio_original.ilike(f"%{filters['search']}%")
                )

        # Count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        # Paginacion
        stmt = stmt.order_by(TransaccionModel.fecha.desc())
        stmt = stmt.offset((page - 1) * size).limit(size)
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def get_unclassified(self, extracto_id: uuid.UUID) -> list[TransaccionModel]:
        """Transacciones con confidence < 70% o sin clasificar."""
        stmt = select(TransaccionModel).where(
            TransaccionModel.extracto_id == extracto_id,
            (
                (TransaccionModel.confidence < 70)
                | (TransaccionModel.confidence.is_(None))
            ),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search_comercio(
        self, usuario_id: uuid.UUID, query: str
    ) -> list[TransaccionModel]:
        stmt = (
            select(TransaccionModel)
            .where(
                TransaccionModel.usuario_id == usuario_id,
                TransaccionModel.comercio_original.ilike(f"%{query}%"),
            )
            .limit(20)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def save(self, transaccion: Any) -> Any:
        if hasattr(transaccion, "_sa_instance_state"):
            await self.session.merge(transaccion)
        else:
            modelo = self._to_model(transaccion)
            self.session.add(modelo)
            transaccion = modelo
        await self.session.flush()
        return transaccion

    async def bulk_save(self, transacciones: list[Any]) -> list[Any]:
        modelos = [self._to_model(t) if not hasattr(t, "_sa_instance_state") else t for t in transacciones]
        self.session.add_all(modelos)
        await self.session.flush()
        return modelos

    async def bulk_update_category(
        self, transaccion_ids: list[uuid.UUID], categoria_id: uuid.UUID
    ) -> int:
        stmt = (
            update(TransaccionModel)
            .where(TransaccionModel.id.in_(transaccion_ids))
            .values(categoria_id=categoria_id, confidence=100.00)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount

    def _to_model(self, entity: Any) -> TransaccionModel:
        return TransaccionModel(
            id=entity.id,
            extracto_id=entity.extracto_id,
            usuario_id=entity.usuario_id,
            numero_autorizacion=entity.numero_autorizacion,
            fecha=entity.fecha,
            comercio_original=entity.comercio_original,
            comercio_traducido=entity.comercio_traducido,
            valor=entity.valor,
            numero_cuotas=entity.numero_cuotas,
            cuotas_totales=entity.cuotas_totales,
            cuota_actual=entity.cuota_actual,
            valor_cuota=entity.valor_cuota,
            moneda_original=entity.moneda_original,
            valor_moneda_original=entity.valor_moneda_original,
            categoria_id=entity.categoria_id,
            confidence=entity.confidence,
            es_abono=entity.es_abono,
            es_cuota=entity.es_cuota,
        )
