"""Tests para el metodo buscar_por_nombre del CategoriaRepository."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.models import CategoriaModel

pytestmark = pytest.mark.integration


class TestBuscarPorNombre:
    """Escenarios del metodo buscar_por_nombre."""

    @pytest.mark.asyncio
    async def test_Should_FindCategory_When_ExactNameMatch(
        self,
        db_session: AsyncSession,
    ):
        """Encuentra categoria por coincidencia exacta de nombre."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.categoria_repo import (
            CategoriaRepository,
        )

        repo = CategoriaRepository(db_session)
        user_id = uuid.uuid4()
        model = CategoriaModel(
            id=uuid.uuid4(),
            nombre="Gimnasio Personal",
            es_predefinida=False,
            usuario_id=user_id,
        )
        db_session.add(model)
        await db_session.flush()

        # Act ------------------------------------------------------------
        results = await repo.buscar_por_nombre("Gimnasio Personal", user_id)

        # Assert ----------------------------------------------------------
        assert len(results) == 1
        assert results[0].nombre == "Gimnasio Personal"

    @pytest.mark.asyncio
    async def test_Should_FindByPartialMatch_When_SubstringProvided(
        self,
        db_session: AsyncSession,
    ):
        """Encuentra por coincidencia parcial (ILIKE)."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.categoria_repo import (
            CategoriaRepository,
        )

        repo = CategoriaRepository(db_session)
        user_id = uuid.uuid4()
        model = CategoriaModel(
            id=uuid.uuid4(),
            nombre="Transporte Terrestre",
            es_predefinida=False,
            usuario_id=user_id,
        )
        db_session.add(model)
        await db_session.flush()

        # Act ------------------------------------------------------------
        results = await repo.buscar_por_nombre("transporte", user_id)

        # Assert ----------------------------------------------------------
        assert len(results) >= 1
        nombres = [c.nombre for c in results]
        assert any("transporte" in n.lower() for n in nombres)

    @pytest.mark.asyncio
    async def test_Should_IncludePredefinidas_When_UsuarioIdNone(
        self,
        db_session: AsyncSession,
        categoria_predefinida: CategoriaModel,
    ):
        """Busca entre predefinidas cuando no se especifica usuario."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.categoria_repo import (
            CategoriaRepository,
        )

        repo = CategoriaRepository(db_session)

        # Act ------------------------------------------------------------
        results = await repo.buscar_por_nombre("Alimentacion", None)

        # Assert ----------------------------------------------------------
        assert len(results) >= 1
        assert any(c.id == categoria_predefinida.id for c in results)

    @pytest.mark.asyncio
    async def test_Should_ReturnEmpty_When_NoMatch(
        self,
        db_session: AsyncSession,
    ):
        """Retorna lista vacia cuando no hay coincidencias."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.categoria_repo import (
            CategoriaRepository,
        )

        repo = CategoriaRepository(db_session)

        # Act ------------------------------------------------------------
        results = await repo.buscar_por_nombre("ZZZ_NoExiste", uuid.uuid4())

        # Assert ----------------------------------------------------------
        assert isinstance(results, list)
        assert len(results) == 0
