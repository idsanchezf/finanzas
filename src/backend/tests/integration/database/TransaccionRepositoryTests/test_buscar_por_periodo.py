"""Tests para el metodo buscar_por_periodo del TransaccionRepository."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.models import TransaccionModel

pytestmark = pytest.mark.integration


class TestBuscarPorPeriodo:
    """Escenarios del metodo buscar_por_periodo."""

    @pytest.mark.asyncio
    async def test_Should_ReturnTransaccionesInRange_When_DateRangeProvided(
        self,
        db_session: AsyncSession,
    ):
        """Retorna transacciones dentro del rango de fechas."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.transaccion_repo import (
            TransaccionRepository,
        )

        repo = TransaccionRepository(db_session)
        usuario_id = uuid.uuid4()
        extracto_id = uuid.uuid4()

        t1 = TransaccionModel(
            id=uuid.uuid4(),
            extracto_id=extracto_id,
            usuario_id=usuario_id,
            fecha=date(2026, 6, 5),
            comercio_original="Compra A",
            valor=Decimal("100"),
        )
        t2 = TransaccionModel(
            id=uuid.uuid4(),
            extracto_id=extracto_id,
            usuario_id=usuario_id,
            fecha=date(2026, 6, 15),
            comercio_original="Compra B",
            valor=Decimal("200"),
        )
        t3 = TransaccionModel(
            id=uuid.uuid4(),
            extracto_id=extracto_id,
            usuario_id=usuario_id,
            fecha=date(2026, 7, 1),
            comercio_original="Compra C",
            valor=Decimal("300"),
        )
        db_session.add_all([t1, t2, t3])
        await db_session.flush()

        # Act ------------------------------------------------------------
        items, total = await repo.buscar_por_periodo(
            usuario_id,
            fecha_inicio=date(2026, 6, 1),
            fecha_fin=date(2026, 6, 30),
            page=1,
            size=10,
        )

        # Assert ----------------------------------------------------------
        assert total == 2
        ids = {t.id for t in items}
        assert t1.id in ids
        assert t2.id in ids
        assert t3.id not in ids

    @pytest.mark.asyncio
    async def test_Should_ReturnEmpty_When_NoTransaccionesInRange(
        self,
        db_session: AsyncSession,
    ):
        """Retorna vacio cuando no hay transacciones en el rango."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.transaccion_repo import (
            TransaccionRepository,
        )

        repo = TransaccionRepository(db_session)
        usuario_id = uuid.uuid4()
        extracto_id = uuid.uuid4()

        t1 = TransaccionModel(
            id=uuid.uuid4(),
            extracto_id=extracto_id,
            usuario_id=usuario_id,
            fecha=date(2026, 1, 10),
            comercio_original="Compra Antigua",
            valor=Decimal("50"),
        )
        db_session.add(t1)
        await db_session.flush()

        # Act ------------------------------------------------------------
        items, total = await repo.buscar_por_periodo(
            usuario_id,
            fecha_inicio=date(2026, 6, 1),
            fecha_fin=date(2026, 6, 30),
        )

        # Assert ----------------------------------------------------------
        assert total == 0
        assert len(items) == 0

    @pytest.mark.asyncio
    async def test_Should_SupportPagination_When_ManyResults(
        self,
        db_session: AsyncSession,
    ):
        """Soporta paginacion en busqueda por periodo."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.transaccion_repo import (
            TransaccionRepository,
        )

        repo = TransaccionRepository(db_session)
        usuario_id = uuid.uuid4()
        extracto_id = uuid.uuid4()

        for i in range(5):
            model = TransaccionModel(
                id=uuid.uuid4(),
                extracto_id=extracto_id,
                usuario_id=usuario_id,
                fecha=date(2026, 6, i + 1),
                comercio_original=f"Comercio {i}",
                valor=Decimal(str(i * 10)),
            )
            db_session.add(model)
        await db_session.flush()

        # Act ------------------------------------------------------------
        items, total = await repo.buscar_por_periodo(
            usuario_id,
            fecha_inicio=date(2026, 6, 1),
            fecha_fin=date(2026, 6, 30),
            page=1,
            size=2,
        )

        # Assert ----------------------------------------------------------
        assert len(items) == 2
        assert total == 5
