"""Tests para el metodo get_all del CategoriaRepository."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.models import CategoriaModel

pytestmark = pytest.mark.integration


class TestGetAll:
    """Escenarios del metodo get_all."""

    @pytest.mark.asyncio
    async def test_Should_ReturnPredefinidasAndPersonalizadas_When_UsuarioIdProvided(
        self,
        db_session: AsyncSession,
        categoria_predefinida: CategoriaModel,
        categoria_personalizada: CategoriaModel,
    ):
        """Retorna predefinidas + personalizadas del usuario."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.categoria_repo import (
            CategoriaRepository,
        )

        repo = CategoriaRepository(db_session)
        user_id = categoria_personalizada.usuario_id

        # Act ------------------------------------------------------------
        results = await repo.get_all(usuario_id=user_id)

        # Assert ----------------------------------------------------------
        assert len(results) >= 2
        ids = {c.id for c in results}
        assert categoria_predefinida.id in ids
        assert categoria_personalizada.id in ids

    @pytest.mark.asyncio
    async def test_Should_ReturnOnlyPredefinidas_When_UsuarioIdIsNone(
        self,
        db_session: AsyncSession,
        categoria_predefinida: CategoriaModel,
        categoria_personalizada: CategoriaModel,
    ):
        """Retorna solo predefinidas cuando no se especifica usuario."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.categoria_repo import (
            CategoriaRepository,
        )

        repo = CategoriaRepository(db_session)

        # Act ------------------------------------------------------------
        results = await repo.get_all(usuario_id=None)

        # Assert ----------------------------------------------------------
        ids = {c.id for c in results}
        assert categoria_predefinida.id in ids
        assert categoria_personalizada.id not in ids

    @pytest.mark.asyncio
    async def test_Should_IncludePersonalizadasOfDifferentUser_When_OtherUserId(
        self,
        db_session: AsyncSession,
        categoria_predefinida: CategoriaModel,
        categoria_personalizada: CategoriaModel,
    ):
        """No retorna personalizadas de otro usuario."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.categoria_repo import (
            CategoriaRepository,
        )

        repo = CategoriaRepository(db_session)
        other_user_id = uuid.uuid4()

        # Act ------------------------------------------------------------
        results = await repo.get_all(usuario_id=other_user_id)

        # Assert ----------------------------------------------------------
        ids = {c.id for c in results}
        assert categoria_predefinida.id in ids
        # La personalizada pertenece a otro usuario
        assert categoria_personalizada.id not in ids
