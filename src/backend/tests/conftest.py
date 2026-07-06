"""Configuracion global de pytest para el backend.

Fixtures compartidas: sesion de BD, cliente HTTP async, etc.
"""

from __future__ import annotations

import pytest_asyncio
from httpx import ASGITransport, AsyncClient


@pytest_asyncio.fixture
async def async_client():
    """Cliente HTTP async para pruebas de integracion de la API."""
    from src.api.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def db_session():
    """Sesion de BD para pruebas (requiere PostgreSQL de prueba)."""
    # En tests unitarios se usaria mock o SQLite en memoria
    # En tests de integracion se usaria TestContainers o BD de prueba
    yield None
