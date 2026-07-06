"""Unit of Work — Gestion de transacciones de base de datos.

Garantiza atomicidad en operaciones que involucran multiples repositorios.
Implementa el patron Unit of Work para SQLAlchemy async.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.domain.repositories import IUnitOfWork

logger = logging.getLogger(__name__)


class UnitOfWork(IUnitOfWork):
    """Gestiona transacciones de base de datos con SQLAlchemy async.

    Uso:
        async with UnitOfWork(session_factory) as uow:
            repo = SomeRepository(uow.session)
            await repo.save(entity)
            await uow.commit()
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory
        self._session: AsyncSession | None = None

    @property
    def session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("UnitOfWork no ha sido iniciado. Usa 'async with'.")
        return self._session

    async def __aenter__(self) -> UnitOfWork:
        self._session = self.session_factory()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            await self.rollback()
            logger.error("Transaccion revertida por error", exc_info=(exc_type, exc_val, exc_tb))
        else:
            await self.commit()
        if self._session:
            await self._session.close()
            self._session = None

    async def commit(self) -> None:
        """Confirma la transaccion actual."""
        await self.session.commit()
        logger.debug("Transaccion confirmada")

    async def rollback(self) -> None:
        """Revierte la transaccion actual."""
        await self.session.rollback()
        logger.debug("Transaccion revertida")

    async def flush(self) -> None:
        """Flush de cambios pendientes a la BD sin commit."""
        await self.session.flush()


async def create_session_factory(database_url: str) -> async_sessionmaker[AsyncSession]:
    """Crea una fabrica de sesiones async de SQLAlchemy.

    Args:
        database_url: URL de conexion async (postgresql+asyncpg://...).

    Returns:
        async_sessionmaker configurada.
    """
    engine = create_async_engine(
        database_url,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
        pool_pre_ping=True,
    )
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
