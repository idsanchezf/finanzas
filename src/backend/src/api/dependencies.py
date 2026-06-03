"""Dependencias FastAPI — Inyeccion de dependencias para repositorios y servicios.

Usa FastAPI Depends para proveer instancias de repositorios, handlers,
y clientes de infraestructura a los endpoints.
"""

from __future__ import annotations

import os

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.handlers.command_handlers import CommandHandler
from src.application.handlers.query_handlers import QueryHandler
from src.infrastructure.cache.redis_client import get_redis_client, RedisClient
from src.infrastructure.llm.gemini_client import get_gemini_client, GeminiClient
from src.infrastructure.messaging.rabbitmq import get_event_bus, RabbitMQEventBus
from src.infrastructure.persistence.repositories import (
    CategoriaRepository,
    ExtractoRepository,
    TarjetaRepository,
    TransaccionRepository,
    UsuarioRepository,
)
from src.infrastructure.persistence.unit_of_work import create_session_factory
from src.infrastructure.storage.r2_storage import get_storage, R2Storage


# ============================================================
# Database session
# ============================================================
_async_session_factory = None


async def get_async_session_factory():
    """Crea la fabrica de sesiones async (singleton)."""
    global _async_session_factory
    if _async_session_factory is None:
        db_url = os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://postgres:postgres@localhost:5432/finance_report",
        )
        _async_session_factory = await create_session_factory(db_url)
    return _async_session_factory


async def get_db_session() -> AsyncSession:
    """Provee una sesion de BD async por request."""
    factory = await get_async_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ============================================================
# Repositorios
# ============================================================
async def get_extracto_repo(
    session: AsyncSession = Depends(get_db_session),
) -> ExtractoRepository:
    return ExtractoRepository(session)


async def get_transaccion_repo(
    session: AsyncSession = Depends(get_db_session),
) -> TransaccionRepository:
    return TransaccionRepository(session)


async def get_categoria_repo(
    session: AsyncSession = Depends(get_db_session),
) -> CategoriaRepository:
    return CategoriaRepository(session)


async def get_usuario_repo(
    session: AsyncSession = Depends(get_db_session),
) -> UsuarioRepository:
    return UsuarioRepository(session)


async def get_tarjeta_repo(
    session: AsyncSession = Depends(get_db_session),
) -> TarjetaRepository:
    return TarjetaRepository(session)


# ============================================================
# Handlers CQRS
# ============================================================
async def get_command_handler(
    extracto_repo: ExtractoRepository = Depends(get_extracto_repo),
    transaccion_repo: TransaccionRepository = Depends(get_transaccion_repo),
    categoria_repo: CategoriaRepository = Depends(get_categoria_repo),
    usuario_repo: UsuarioRepository = Depends(get_usuario_repo),
    evento_bus: RabbitMQEventBus | None = None,
) -> CommandHandler:
    from src.application.handlers.command_handlers import CommandHandler
    from src.infrastructure.persistence.repositories import PresupuestoRepository

    # PresupuestoRepository se puede crear aqui si es necesario
    return CommandHandler(
        extracto_repo=extracto_repo,
        transaccion_repo=transaccion_repo,
        categoria_repo=categoria_repo,
        presupuesto_repo=None,  # Se inyectara cuando se necesite
        usuario_repo=usuario_repo,
        event_bus=evento_bus,
    )


async def get_query_handler(
    extracto_repo: ExtractoRepository = Depends(get_extracto_repo),
    transaccion_repo: TransaccionRepository = Depends(get_transaccion_repo),
    categoria_repo: CategoriaRepository = Depends(get_categoria_repo),
) -> QueryHandler:
    return QueryHandler(
        extracto_repo=extracto_repo,
        transaccion_repo=transaccion_repo,
        categoria_repo=categoria_repo,
    )


# ============================================================
# Clientes de infraestructura
# ============================================================
async def get_redis() -> RedisClient:
    return await get_redis_client()


async def get_storage_client() -> R2Storage:
    return get_storage()


async def get_gemini() -> GeminiClient:
    return get_gemini_client()


async def get_event_bus_dep() -> RabbitMQEventBus:
    return await get_event_bus()


# ============================================================
# Autenticacion
# ============================================================
async def get_current_user_id(
    authorization: str | None = Header(default=None),
) -> str:
    """Extrae el ID del usuario del token JWT.

    En desarrollo, permite un header X-User-Id para testing.
    En produccion, valida el JWT Bearer token.
    """
    if os.getenv("ENVIRONMENT") == "development":
        # Modo desarrollo: aceptar X-User-Id header
        return "dev-user-id"

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticacion requerido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.replace("Bearer ", "")

    try:
        from jose import jwt, JWTError

        secret = os.getenv("JWT_SECRET", "dev-secret")
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalido: subject no encontrado",
            )
        return str(user_id)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token invalido: {str(e)}",
        ) from e
