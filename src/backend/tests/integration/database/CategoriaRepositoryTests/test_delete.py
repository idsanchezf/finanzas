"""Tests para el metodo delete del CategoriaRepository."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.models import CategoriaModel

pytestmark = pytest.mark.integration


class TestDelete:
    """Escenarios del metodo delete."""

    @pytest.mark.asyncio
    async def test_Should_DeletePersonalizada_When_Exists(
        self, db_session: AsyncSession, categoria_personalizada: CategoriaModel,
    ):
        """Elimina una categoria personalizada existente."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.categoria_repo import (
            CategoriaRepository,
        )
        repo = CategoriaRepository(db_session)

        # Act ------------------------------------------------------------
        await repo.delete(categoria_personalizada.id)

        # Assert ----------------------------------------------------------
        result = await repo.get_by_id(categoria_personalizada.id)
        assert result is None

    @pytest.mark.asyncio
    async def test_Should_NotDeletePredefinida_When_SystemCategory(
        self, db_session: AsyncSession, categoria_predefinida: CategoriaModel,
    ):
        """No elimina categorias predefinidas del sistema."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.categoria_repo import (
            CategoriaRepository,
        )
        repo = CategoriaRepository(db_session)

        # Act ------------------------------------------------------------
        await repo.delete(categoria_predefinida.id)

        # Assert ----------------------------------------------------------
        result = await repo.get_by_id(categoria_predefinida.id)
        assert result is not None  # No debe eliminarse

    @pytest.mark.asyncio
    async def test_Should_DoNothing_When_IdNotFound(
        self, db_session: AsyncSession,
    ):
        """No lanza error al eliminar un ID inexistente."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.categoria_repo import (
            CategoriaRepository,
        )
        repo = CategoriaRepository(db_session)

        # Act ------------------------------------------------------------
        # No debe lanzar excepcion
        await repo.delete(uuid.uuid4())

        # Assert ----------------------------------------------------------
        # No error = success
