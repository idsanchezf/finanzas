"""Repositorio concreto de Extractos — SQLAlchemy 2.0 async."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.repositories import IExtractoRepository
from src.infrastructure.persistence.models import ExtractoModel


class ExtractoRepository(IExtractoRepository):
    """Implementacion concreta del repositorio de extractos con SQLAlchemy 2.0."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, extracto_id: uuid.UUID) -> ExtractoModel | None:
        stmt = select(ExtractoModel).where(ExtractoModel.id == extracto_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_usuario(
        self, usuario_id: uuid.UUID, page: int = 1, size: int = 12
    ) -> tuple[list[ExtractoModel], int]:
        count_stmt = (
            select(func.count())
            .select_from(ExtractoModel)
            .where(ExtractoModel.usuario_id == usuario_id)
        )
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = (
            select(ExtractoModel)
            .where(ExtractoModel.usuario_id == usuario_id)
            .order_by(ExtractoModel.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def get_by_tarjeta_and_periodo(
        self, tarjeta_id: uuid.UUID, periodo_inicio: date, periodo_fin: date
    ) -> ExtractoModel | None:
        stmt = select(ExtractoModel).where(
            ExtractoModel.tarjeta_id == tarjeta_id,
            ExtractoModel.periodo_inicio == periodo_inicio,
            ExtractoModel.periodo_fin == periodo_fin,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_tarjeta_and_file_hash(
        self, tarjeta_id: uuid.UUID, file_hash: str
    ) -> ExtractoModel | None:
        """Fix #3: Busca extracto existente por tarjeta_id + hash SHA-256 del archivo.

        Usado como verificacion secundaria de duplicados cuando el chequeo
        por periodo no encuentra coincidencia pero el mismo archivo ya fue cargado.
        """
        stmt = select(ExtractoModel).where(
            ExtractoModel.tarjeta_id == tarjeta_id,
            ExtractoModel.file_hash == file_hash,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def save(self, extracto: Any) -> Any:
        """Persiste un extracto (crea o actualiza).

        Si es un modelo ORM ya gestionado por SQLAlchemy, usa merge directo.
        Si es una entidad de dominio, la convierte a modelo y usa merge
        para soportar tanto insercion como actualizacion.

        Captura IntegrityError del constraint uq_extracto_tarjeta_periodo
        como safety net ante race conditions (feat-003 / T007).
        """
        if hasattr(extracto, "_sa_instance_state"):
            modelo = extracto
            modelo = await self.session.merge(modelo)
        else:
            modelo = self._to_model(extracto)
            modelo = await self.session.merge(modelo)

        try:
            await self.session.flush()
        except IntegrityError:
            await self.session.rollback()
            from src.domain.exceptions import ExtractoDuplicadoException

            raise ExtractoDuplicadoException() from None

        return modelo

    async def delete(self, extracto_id: uuid.UUID) -> None:
        extracto = await self.get_by_id(extracto_id)
        if extracto:
            await self.session.delete(extracto)
            await self.session.flush()

    def _to_model(self, entity: Any) -> ExtractoModel:
        """Convierte entidad de dominio a modelo ORM.

        Maneja la conversion de Value Objects Money a Decimal para los campos monetarios.
        """
        _amount = lambda v: v.amount if hasattr(v, "amount") else v

        return ExtractoModel(
            id=entity.id,
            tarjeta_id=entity.tarjeta_id,
            usuario_id=entity.usuario_id,
            estado=entity.estado.value if hasattr(entity.estado, "value") else str(entity.estado),
            periodo_inicio=entity.periodo_inicio,
            periodo_fin=entity.periodo_fin,
            fecha_corte=entity.fecha_corte,
            fecha_limite_pago=entity.fecha_limite_pago,
            pago_minimo=_amount(entity.pago_minimo),
            pago_total=_amount(entity.pago_total),
            cupo_total=_amount(entity.cupo_total),
            cupo_disponible=_amount(entity.cupo_disponible),
            archivo_s3_key=entity.archivo_s3_key,
            file_hash=getattr(entity, "file_hash", None),
            progress_pct=entity.progress_pct,
            error_message=entity.error_message,
        )
