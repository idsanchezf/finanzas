"""Repositorio concreto de Transacciones — SQLAlchemy 2.0 async.

Provee persistencia para la entidad Transaccion con:
- CRUD completo con paginacion y filtros
- Conversiones bidireccionales entre modelo ORM y entidad de dominio
- Soporte para sorting dinamico por campo
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.transaccion import Transaccion
from src.domain.repositories import ITransaccionRepository
from src.infrastructure.persistence.models import TransaccionModel

# Mapa de campos de ordenamiento: nombre publico -> columna ORM
_ORDER_COLUMNS = {
    "fecha": TransaccionModel.fecha,
    "valor": TransaccionModel.valor,
    "comercio": TransaccionModel.comercio_original,
    "confidence": TransaccionModel.confidence,
    "categoria": TransaccionModel.categoria_id,
}


class TransaccionRepository(ITransaccionRepository):
    """Implementacion concreta del repositorio de transacciones.

    Usa SQLAlchemy 2.0 async para operaciones de BD.
    Soporta conversion bidireccional entre TransaccionModel (ORM) y
    Transaccion (entidad de dominio) para mantener clean architecture.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ============================================================
    # Conversiones modelo <-> entidad
    # ============================================================

    @staticmethod
    def _model_to_entity(model: TransaccionModel) -> Transaccion:
        """Convierte un modelo ORM en una entidad de dominio."""
        return Transaccion(
            id=model.id,
            extracto_id=model.extracto_id,
            usuario_id=model.usuario_id,
            numero_autorizacion=model.numero_autorizacion,
            fecha=model.fecha,
            comercio_original=model.comercio_original,
            comercio_traducido=model.comercio_traducido,
            valor=model.valor,
            numero_cuotas=model.numero_cuotas,
            cuotas_totales=model.cuotas_totales,
            cuota_actual=model.cuota_actual,
            valor_cuota=model.valor_cuota or Decimal("0"),
            interes_mensual_pct=model.interes_mensual_pct,
            interes_anual_pct=model.interes_anual_pct,
            saldo_pendiente=model.saldo_pendiente or Decimal("0"),
            moneda_original=model.moneda_original,
            valor_moneda_original=model.valor_moneda_original,
            categoria_id=model.categoria_id,
            confidence=model.confidence,
            es_abono=model.es_abono,
            es_cuota=model.es_cuota,
            parent_transaccion_id=model.parent_transaccion_id,
        )

    def _to_model(self, entity: Transaccion) -> TransaccionModel:
        """Convierte una entidad de dominio en modelo ORM."""
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

    @staticmethod
    def _apply_entity_changes(entity: Transaccion, model: TransaccionModel) -> TransaccionModel:
        """Aplica los cambios de una entidad de dominio al modelo ORM.

        Solo se actualizan los campos que la entidad pudo haber modificado
        (categoria_id, confidence). El resto se mantiene igual.
        """
        model.categoria_id = entity.categoria_id
        model.confidence = entity.confidence
        return model

    # ============================================================
    # Queries
    # ============================================================

    async def get_by_id(self, transaccion_id: uuid.UUID) -> TransaccionModel | None:
        """Obtiene una transaccion por su ID (retorna modelo ORM)."""
        stmt = select(TransaccionModel).where(TransaccionModel.id == transaccion_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_entity_by_id(self, transaccion_id: uuid.UUID) -> Transaccion | None:
        """Obtiene una transaccion como entidad de dominio."""
        model = await self.get_by_id(transaccion_id)
        if model is None:
            return None
        return self._model_to_entity(model)

    async def get_by_extracto(
        self, extracto_id: uuid.UUID, filters: dict[str, Any] | None = None
    ) -> list[TransaccionModel]:
        """Lista todas las transacciones de un extracto."""
        stmt = select(TransaccionModel).where(TransaccionModel.extracto_id == extracto_id)
        if filters and "categoria_id" in filters:
            stmt = stmt.where(TransaccionModel.categoria_id == filters["categoria_id"])
        stmt = stmt.order_by(TransaccionModel.fecha.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_usuario(
        self,
        usuario_id: uuid.UUID,
        filters: dict[str, Any] | None = None,
        page: int = 1,
        size: int = 50,
        sort_by: str = "fecha",
        order: str = "desc",
    ) -> tuple[list[TransaccionModel], int]:
        """Lista transacciones de un usuario con filtros, paginacion y sorting.

        Args:
            usuario_id: ID del usuario propietario.
            filters: Diccionario con filtros opcionales:
                - extracto_id: Filtrar por extracto.
                - categoria_id: Filtrar por categoria.
                - search: Busqueda parcial en comercio_original.
                - confidence: "HIGH" (>=90), "MEDIUM" (70-89), "LOW" (<70).
            page: Numero de pagina (1-based).
            size: Items por pagina.
            sort_by: Campo para ordenar (fecha, valor, comercio, confidence).
            order: Direccion 'asc' o 'desc'.

        Returns:
            Tuple con (items, total_count).
        """
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
            if "confidence" in filters:
                conf = filters["confidence"].upper()
                if conf == "HIGH":
                    stmt = stmt.where(TransaccionModel.confidence >= 90)
                elif conf == "MEDIUM":
                    stmt = stmt.where(
                        TransaccionModel.confidence >= 70,
                        TransaccionModel.confidence < 90,
                    )
                elif conf == "LOW":
                    stmt = stmt.where(
                        (TransaccionModel.confidence < 70) | (TransaccionModel.confidence.is_(None))
                    )

        # Count total (sin paginacion)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        # Ordenamiento
        order_col = _ORDER_COLUMNS.get(sort_by, TransaccionModel.fecha)
        if order.lower() == "asc":
            stmt = stmt.order_by(order_col.asc())
        else:
            stmt = stmt.order_by(order_col.desc())

        # Paginacion
        stmt = stmt.offset((page - 1) * size).limit(size)
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def get_unclassified(self, extracto_id: uuid.UUID) -> list[TransaccionModel]:
        """Transacciones con confidence < 70% o sin clasificar."""
        stmt = select(TransaccionModel).where(
            TransaccionModel.extracto_id == extracto_id,
            ((TransaccionModel.confidence < 70) | (TransaccionModel.confidence.is_(None))),
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search_comercio(self, usuario_id: uuid.UUID, query: str) -> list[TransaccionModel]:
        """Busqueda full-text por nombre de comercio."""
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

    async def buscar_por_periodo(
        self,
        usuario_id: uuid.UUID,
        fecha_inicio: date,
        fecha_fin: date,
        page: int = 1,
        size: int = 50,
    ) -> tuple[list[TransaccionModel], int]:
        """Busca transacciones de un usuario en un rango de fechas con paginacion."""
        base_stmt = select(TransaccionModel).where(
            TransaccionModel.usuario_id == usuario_id,
            TransaccionModel.fecha >= fecha_inicio,
            TransaccionModel.fecha <= fecha_fin,
        )

        # Count
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        # Paginacion
        stmt = base_stmt.order_by(TransaccionModel.fecha.desc())
        stmt = stmt.offset((page - 1) * size).limit(size)
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    # ============================================================
    # Commands (persistencia)
    # ============================================================

    async def save(self, transaccion: Any) -> Any:
        """Persiste o actualiza una transaccion (modelo ORM o entidad de dominio).

        - Si es un modelo ORM (tiene _sa_instance_state): usa merge para actualizar.
        - Si es una entidad de dominio: convierte a modelo y usa merge.
        """
        if hasattr(transaccion, "_sa_instance_state"):
            # Es un modelo ORM — merge para manejar inserts y updates
            merged = await self.session.merge(transaccion)
        else:
            # Es una entidad de dominio — convertir a modelo y merge
            modelo = self._to_model(transaccion)
            merged = await self.session.merge(modelo)
        await self.session.flush()
        return merged

    async def bulk_save(self, transacciones: list[Any]) -> list[Any]:
        """Guarda multiples transacciones en lote."""
        modelos = [
            t if hasattr(t, "_sa_instance_state") else self._to_model(t) for t in transacciones
        ]
        # Usar merge para cada una (soporta inserts y updates)
        for modelo in modelos:
            await self.session.merge(modelo)
        await self.session.flush()
        return modelos

    async def bulk_update_category(
        self, transaccion_ids: list[uuid.UUID], categoria_id: uuid.UUID
    ) -> int:
        """Actualiza la categoria de multiples transacciones en un solo UPDATE."""
        stmt = (
            update(TransaccionModel)
            .where(TransaccionModel.id.in_(transaccion_ids))
            .values(categoria_id=categoria_id, confidence=100.00)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount

    async def update(
        self, transaccion_id: uuid.UUID, entity: Transaccion
    ) -> TransaccionModel | None:
        """Actualiza una transaccion existente desde una entidad de dominio.

        Busca el modelo ORM por ID, aplica los cambios desde la entidad,
        y persiste con merge.

        Returns:
            El modelo ORM actualizado, o None si no existe.
        """
        model = await self.get_by_id(transaccion_id)
        if model is None:
            return None
        self._apply_entity_changes(entity, model)
        await self.session.merge(model)
        await self.session.flush()
        return model
