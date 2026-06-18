"""Tests para el metodo bulk_save del TransaccionRepository."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.models import TransaccionModel

pytestmark = pytest.mark.integration


class TestBulkSave:
    """Escenarios del metodo bulk_save."""

    @pytest.mark.asyncio
    async def test_Should_PersistMultipleTransacciones_When_BulkInsert(
        self, db_session: AsyncSession,
    ):
        """Persiste multiples transacciones en lote."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.transaccion_repo import (
            TransaccionRepository,
        )
        repo = TransaccionRepository(db_session)
        extracto_id = uuid.uuid4()
        usuario_id = uuid.uuid4()

        modelos = [
            TransaccionModel(
                id=uuid.uuid4(), extracto_id=extracto_id, usuario_id=usuario_id,
                fecha=date(2026, 6, 1), comercio_original=f"Comercio {i}",
                valor=Decimal(str(i * 10 + 10)),
            )
            for i in range(3)
        ]

        # Act ------------------------------------------------------------
        saved = await repo.bulk_save(modelos)

        # Assert ----------------------------------------------------------
        assert len(saved) == 3

        # Verify all persisted
        for m in modelos:
            retrieved = await repo.get_by_id(m.id)
            assert retrieved is not None, f"Transaccion {m.id} no fue persistida"

    @pytest.mark.asyncio
    async def test_Should_HandleEmptyList_When_NoTransacciones(
        self, db_session: AsyncSession,
    ):
        """Maneja lista vacia sin errores."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.transaccion_repo import (
            TransaccionRepository,
        )
        repo = TransaccionRepository(db_session)

        # Act ------------------------------------------------------------
        saved = await repo.bulk_save([])

        # Assert ----------------------------------------------------------
        assert saved == []
