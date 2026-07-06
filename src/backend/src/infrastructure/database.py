"""Configuracion de conexion a base de datos — SQLAlchemy 2.0 async.

Provee:
- create_async_engine con URL desde variables de entorno
- async_sessionmaker para crear sesiones async
- get_db() generator para dependency injection de FastAPI
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# URL de conexion desde variable de entorno, con fallback para desarrollo local
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/finance_report",
)

# Engine async con pool de conexiones optimizado para picos (dias 1-5 del mes)
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
    pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
    pool_pre_ping=True,
)

# Fabrica de sesiones async — NO autoflush para control explicito de transacciones
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Generador async de sesiones de BD para FastAPI dependency injection.

    Uso:
        @app.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            ...

    La sesion se cierra automaticamente al finalizar el request.
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
