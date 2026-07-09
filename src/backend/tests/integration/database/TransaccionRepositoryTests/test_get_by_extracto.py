"""Tests para el metodo get_by_extracto del TransaccionRepository."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.models import TransaccionModel

pytestmark = pytest.mark.integration


class TestGetByExtracto:
    """Escenarios del metodo get_by_extracto."""

    @pytest.mark.asyncio
    async def test_Should_ReturnTransacciones_When_ExtractoExists(
        self,
        db_session: AsyncSession,
    ):
        """Retorna todas las transacciones de un extracto."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.transaccion_repo import (
            TransaccionRepository,
        )

        repo = TransaccionRepository(db_session)
        extracto_id = uuid.uuid4()
        usuario_id = uuid.uuid4()

        t1 = TransaccionModel(
            id=uuid.uuid4(),
            extracto_id=extracto_id,
            usuario_id=usuario_id,
            comercio_original="A",
            valor=Decimal("10"),
        )
        t2 = TransaccionModel(
            id=uuid.uuid4(),
            extracto_id=extracto_id,
            usuario_id=usuario_id,
            comercio_original="B",
            valor=Decimal("20"),
        )
        db_session.add_all([t1, t2])
        await db_session.flush()

        # Act ------------------------------------------------------------
        results = await repo.get_by_extracto(extracto_id)

        # Assert ----------------------------------------------------------
        assert len(results) == 2
        ids = {t.id for t in results}
        assert t1.id in ids
        assert t2.id in ids

    @pytest.mark.asyncio
    async def test_Should_ReturnEmpty_When_NoTransacciones(
        self,
        db_session: AsyncSession,
    ):
        """Retorna lista vacia para extracto sin transacciones."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.transaccion_repo import (
            TransaccionRepository,
        )

        repo = TransaccionRepository(db_session)

        # Act ------------------------------------------------------------
        results = await repo.get_by_extracto(uuid.uuid4())

        # Assert ----------------------------------------------------------
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_Should_FilterByCategoria_When_FilterProvided(
        self,
        db_session: AsyncSession,
    ):
        """Filtra transacciones por categoria_id."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.transaccion_repo import (
            TransaccionRepository,
        )

        repo = TransaccionRepository(db_session)
        extracto_id = uuid.uuid4()
        usuario_id = uuid.uuid4()
        cat_a = uuid.uuid4()
        cat_b = uuid.uuid4()

        t1 = TransaccionModel(
            id=uuid.uuid4(),
            extracto_id=extracto_id,
            usuario_id=usuario_id,
            comercio_original="A",
            valor=Decimal("10"),
            categoria_id=cat_a,
        )
        t2 = TransaccionModel(
            id=uuid.uuid4(),
            extracto_id=extracto_id,
            usuario_id=usuario_id,
            comercio_original="B",
            valor=Decimal("20"),
            categoria_id=cat_b,
        )
        db_session.add_all([t1, t2])
        await db_session.flush()

        # Act ------------------------------------------------------------
        results = await repo.get_by_extracto(extracto_id, filters={"categoria_id": cat_a})

        # Assert ----------------------------------------------------------
        assert len(results) == 1
        assert results[0].id == t1.id
