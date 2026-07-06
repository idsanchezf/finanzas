"""Tests para el metodo get_by_id del CategoriaRepository."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.integration


class TestGetById:
    """Escenarios del metodo get_by_id."""

    @pytest.mark.asyncio
    async def test_Should_ReturnCategoria_When_ValidId(
        self, db_session: AsyncSession, categoria_predefinida,
    ):
        """Retorna una categoria existente por su ID."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.categoria_repo import (
            CategoriaRepository,
        )
        repo = CategoriaRepository(db_session)
        target_id = categoria_predefinida.id

        # Act ------------------------------------------------------------
        result = await repo.get_by_id(target_id)

        # Assert ----------------------------------------------------------
        assert result is not None
        assert result.id == target_id
        assert result.nombre == categoria_predefinida.nombre

    @pytest.mark.asyncio
    async def test_Should_ReturnNone_When_IdNotFound(
        self, db_session: AsyncSession,
    ):
        """Retorna None cuando el ID no existe."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.categoria_repo import (
            CategoriaRepository,
        )
        repo = CategoriaRepository(db_session)
        fake_id = uuid.uuid4()

        # Act ------------------------------------------------------------
        result = await repo.get_by_id(fake_id)

        # Assert ----------------------------------------------------------
        assert result is None
