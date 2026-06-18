"""Tests para el metodo get_by_id del TransaccionRepository."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.integration


class TestGetById:
    """Escenarios del metodo get_by_id."""

    @pytest.mark.asyncio
    async def test_Should_ReturnTransaccion_When_ValidId(
        self, db_session: AsyncSession, transaccion_prueba,
    ):
        """Retorna una transaccion existente por su ID."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.transaccion_repo import (
            TransaccionRepository,
        )
        repo = TransaccionRepository(db_session)

        # Act ------------------------------------------------------------
        result = await repo.get_by_id(transaccion_prueba.id)

        # Assert ----------------------------------------------------------
        assert result is not None
        assert result.id == transaccion_prueba.id
        assert result.comercio_original == "RESTAURANTE DON PEPE"

    @pytest.mark.asyncio
    async def test_Should_ReturnNone_When_IdNotFound(
        self, db_session: AsyncSession,
    ):
        """Retorna None cuando el ID no existe."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.transaccion_repo import (
            TransaccionRepository,
        )
        repo = TransaccionRepository(db_session)

        # Act ------------------------------------------------------------
        result = await repo.get_by_id(uuid.uuid4())

        # Assert ----------------------------------------------------------
        assert result is None
