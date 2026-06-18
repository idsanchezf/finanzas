"""Fixtures compartidas para tests de integracion con base de datos.

Usa SQLite en memoria via aiosqlite para tests rapidos sin PostgreSQL.
"""

from __future__ import annotations

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.infrastructure.persistence.models import Base


@pytest_asyncio.fixture
async def db_session():
    """Sesion de BD async con SQLite en memoria.

    Crea todas las tablas antes del test y las limpia despues.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        echo=False,
    )

    # Crear tablas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session

    # Limpiar
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(db_session: AsyncSession):
    """Retorna una factory para crear sesiones (necesario para UnitOfWork)."""
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    yield factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
