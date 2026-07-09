"""Tests para el metodo get_by_usuario del TransaccionRepository."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.models import TransaccionModel

pytestmark = pytest.mark.integration


class TestGetByUsuario:
    """Escenarios del metodo get_by_usuario."""

    @pytest.mark.asyncio
    async def test_Should_ReturnPaginatedResults_When_UserHasTransacciones(
        self,
        db_session: AsyncSession,
    ):
        """Retorna resultados paginados para el usuario."""
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
        items, total = await repo.get_by_usuario(usuario_id, page=1, size=3)

        # Assert ----------------------------------------------------------
        assert len(items) == 3
        assert total == 5

    @pytest.mark.asyncio
    async def test_Should_ReturnSecondPage_When_Page2Requested(
        self,
        db_session: AsyncSession,
    ):
        """Retorna la segunda pagina correctamente."""
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
        items, total = await repo.get_by_usuario(usuario_id, page=2, size=3)

        # Assert ----------------------------------------------------------
        assert len(items) == 2  # 5 total, 3 en pag 1, 2 en pag 2
        assert total == 5

    @pytest.mark.asyncio
    async def test_Should_ReturnEmpty_When_UserHasNoTransacciones(
        self,
        db_session: AsyncSession,
    ):
        """Retorna lista vacia para usuario sin transacciones."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.transaccion_repo import (
            TransaccionRepository,
        )

        repo = TransaccionRepository(db_session)

        # Act ------------------------------------------------------------
        items, total = await repo.get_by_usuario(uuid.uuid4())

        # Assert ----------------------------------------------------------
        assert len(items) == 0
        assert total == 0

    @pytest.mark.asyncio
    async def test_Should_FilterBySearch_When_SearchProvided(
        self,
        db_session: AsyncSession,
    ):
        """Filtra por termino de busqueda en comercio_original."""
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
            fecha=date(2026, 6, 1),
            comercio_original="NETFLIX STREAMING",
            valor=Decimal("15"),
        )
        t2 = TransaccionModel(
            id=uuid.uuid4(),
            extracto_id=extracto_id,
            usuario_id=usuario_id,
            fecha=date(2026, 6, 2),
            comercio_original="SPOTIFY PREMIUM",
            valor=Decimal("10"),
        )
        db_session.add_all([t1, t2])
        await db_session.flush()

        # Act ------------------------------------------------------------
        items, total = await repo.get_by_usuario(usuario_id, filters={"search": "netflix"})

        # Assert ----------------------------------------------------------
        assert len(items) == 1
        assert items[0].comercio_original == "NETFLIX STREAMING"
        assert total == 1
