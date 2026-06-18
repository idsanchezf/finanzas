"""Tests para el metodo get_predefinidas del CategoriaRepository."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.models import CategoriaModel

pytestmark = pytest.mark.integration


class TestGetPredefinidas:
    """Escenarios del metodo get_predefinidas."""

    @pytest.mark.asyncio
    async def test_Should_ReturnOnlyPredefinidas_When_Called(
        self, db_session: AsyncSession,
        categoria_predefinida: CategoriaModel,
        categoria_personalizada: CategoriaModel,
    ):
        """Retorna solo categorias predefinidas."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.categoria_repo import (
            CategoriaRepository,
        )
        repo = CategoriaRepository(db_session)

        # Act ------------------------------------------------------------
        results = await repo.get_predefinidas()

        # Assert ----------------------------------------------------------
        ids = {c.id for c in results}
        assert categoria_predefinida.id in ids
        assert categoria_personalizada.id not in ids

    @pytest.mark.asyncio
    async def test_Should_ReturnEmptyList_When_NoPredefinidas(
        self, db_session: AsyncSession,
    ):
        """Retorna lista vacia cuando no hay predefinidas."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.categoria_repo import (
            CategoriaRepository,
        )
        repo = CategoriaRepository(db_session)

        # Act ------------------------------------------------------------
        results = await repo.get_predefinidas()

        # Assert ----------------------------------------------------------
        assert isinstance(results, list)
        assert len(results) == 0
