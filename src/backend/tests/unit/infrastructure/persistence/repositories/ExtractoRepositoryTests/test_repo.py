"""Tests para ExtractoRepository — get_by_tarjeta_and_file_hash (Fix #3).

Convencion TDD:
- Carpeta: ExtractoRepositoryTests/
- Archivo: test_repo.py (escenarios del repositorio de extractos)
- Nombramiento: test_should_{resultado}_when_{condicion}
- Patron: AAA con # Arrange -----, # Act -----, # Assert -----
"""

from __future__ import annotations

import uuid
from datetime import date
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.repositories.extracto_repo import ExtractoRepository


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def mock_session() -> MagicMock:
    """Mock de AsyncSession para tests unitarios."""
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.scalars = MagicMock()
    return session


@pytest.fixture
def repository(mock_session: MagicMock) -> ExtractoRepository:
    """SUT: ExtractoRepository con sesion mockeada."""
    return ExtractoRepository(mock_session)


# ============================================================
# TestGetByTarjetaAndFileHash — Fix #3
# ============================================================


class TestGetByTarjetaAndFileHash:
    """Tests para get_by_tarjeta_and_file_hash()."""

    @pytest.mark.asyncio
    async def test_should_find_extracto_by_tarjeta_and_file_hash(
        self,
        repository: ExtractoRepository,
        mock_session: MagicMock,
    ):
        """Fix #3: Debe encontrar extracto existente por tarjeta_id + file_hash."""
        # Arrange --------------------------------------------------------
        tarjeta_id = uuid.uuid4()
        file_hash = "a" * 64  # SHA-256 produce 64 caracteres hex

        # Mock: el resultado de execute.scalar_one_or_none() retorna un modelo
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock(
            id=uuid.uuid4(),
            tarjeta_id=tarjeta_id,
            file_hash=file_hash,
        )
        mock_session.execute.return_value = mock_result

        # Act ------------------------------------------------------------
        result = await repository.get_by_tarjeta_and_file_hash(tarjeta_id, file_hash)

        # Assert ----------------------------------------------------------
        mock_session.execute.assert_called_once()
        assert result is not None
        assert result.tarjeta_id == tarjeta_id

    @pytest.mark.asyncio
    async def test_should_return_none_when_file_hash_not_found(
        self,
        repository: ExtractoRepository,
        mock_session: MagicMock,
    ):
        """Fix #3: Debe retornar None cuando no hay coincidencia de file_hash."""
        # Arrange --------------------------------------------------------
        tarjeta_id = uuid.uuid4()
        file_hash = "b" * 64

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act ------------------------------------------------------------
        result = await repository.get_by_tarjeta_and_file_hash(tarjeta_id, file_hash)

        # Assert ----------------------------------------------------------
        mock_session.execute.assert_called_once()
        assert result is None
