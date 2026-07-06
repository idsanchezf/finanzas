"""Tests para el metodo save del CategoriaRepository."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.models import CategoriaModel

pytestmark = pytest.mark.integration


class TestSave:
    """Escenarios del metodo save."""

    @pytest.mark.asyncio
    async def test_Should_PersistNewCategoria_When_ValidModel(
        self, db_session: AsyncSession,
    ):
        """Crea y persiste una nueva categoria desde el modelo."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.categoria_repo import (
            CategoriaRepository,
        )
        repo = CategoriaRepository(db_session)
        model = CategoriaModel(
            id=uuid.uuid4(),
            nombre="Test Category",
            icono="📁",
            color="#AABBCC",
            es_predefinida=False,
            usuario_id=uuid.uuid4(),
            palabras_clave=["test", "prueba"],
        )

        # Act ------------------------------------------------------------
        saved = await repo.save(model)

        # Assert ----------------------------------------------------------
        assert saved is not None
        assert saved.id == model.id
        assert saved.nombre == "Test Category"

        # Verify persistence
        retrieved = await repo.get_by_id(model.id)
        assert retrieved is not None
        assert retrieved.nombre == "Test Category"

    @pytest.mark.asyncio
    async def test_Should_UpdateExistingCategoria_When_Merged(
        self, db_session: AsyncSession, categoria_predefinida: CategoriaModel,
    ):
        """Actualiza una categoria existente via merge."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.categoria_repo import (
            CategoriaRepository,
        )
        repo = CategoriaRepository(db_session)
        categoria_predefinida.nombre = "Alimentacion Modificada"

        # Act ------------------------------------------------------------
        saved = await repo.save(categoria_predefinida)

        # Assert ----------------------------------------------------------
        assert saved.nombre == "Alimentacion Modificada"

        retrieved = await repo.get_by_id(categoria_predefinida.id)
        assert retrieved is not None
        assert retrieved.nombre == "Alimentacion Modificada"

    @pytest.mark.asyncio
    async def test_Should_SaveCategoryWithKeywords_When_KeywordsProvided(
        self, db_session: AsyncSession,
    ):
        """Persiste una categoria con palabras clave JSON."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.categoria_repo import (
            CategoriaRepository,
        )
        repo = CategoriaRepository(db_session)
        keywords = ["supermercado", "mercado", "comida rapida"]
        model = CategoriaModel(
            id=uuid.uuid4(),
            nombre="Alimentos",
            es_predefinida=True,
            palabras_clave=keywords,
        )

        # Act ------------------------------------------------------------
        saved = await repo.save(model)

        # Assert ----------------------------------------------------------
        retrieved = await repo.get_by_id(model.id)
        assert retrieved is not None
        assert retrieved.palabras_clave == keywords
