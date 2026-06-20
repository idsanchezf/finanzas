"""Dependencias FastAPI — Inyeccion de dependencias para repositorios y servicios.

Usa FastAPI Depends para proveer instancias de repositorios, handlers,
y clientes de infraestructura a los endpoints.
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.handlers.command_handlers import CommandHandler
from src.application.handlers.query_handlers import QueryHandler
from src.infrastructure.persistence.repositories import (
    CategoriaRepository,
    ExtractoRepository,
    TarjetaRepository,
    TransaccionRepository,
    UsuarioRepository,
)
from src.infrastructure.persistence.unit_of_work import create_session_factory

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
    evento_bus: Any = None,
) -> CommandHandler:
    return CommandHandler(
        extracto_repo=extracto_repo,
        transaccion_repo=transaccion_repo,
        categoria_repo=categoria_repo,
        presupuesto_repo=None,  # Implementacion pendiente
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
async def get_redis() -> Any:
    from src.infrastructure.cache.redis_client import get_redis_client
    return await get_redis_client()


async def get_storage_client() -> Any:
    from src.infrastructure.storage.r2_storage import get_storage
    return get_storage()


async def get_gemini() -> Any:
    from src.infrastructure.llm.gemini_client import get_gemini_client
    return get_gemini_client()


async def get_event_bus_dep() -> Any:
    from src.infrastructure.messaging.rabbitmq import get_event_bus
    return await get_event_bus()


# ============================================================
# Servicios de autenticacion
# ============================================================
_jwt_service: Any = None
_google_oauth_service: Any = None


def get_jwt_service() -> Any:
    """Provee el JWTService (singleton)."""
    global _jwt_service
    if _jwt_service is None:
        from src.infrastructure.auth.jwt_service import JWTService

        _jwt_service = JWTService(
            secret=os.getenv("JWT_SECRET", "dev-secret"),
            access_token_ttl=int(os.getenv("JWT_ACCESS_TTL", "900")),
            refresh_token_ttl=int(os.getenv("JWT_REFRESH_TTL", "604800")),
            issuer="finance-report",
        )
    return _jwt_service


def get_google_oauth_service() -> Any:
    """Provee el GoogleOAuthService (singleton)."""
    global _google_oauth_service
    if _google_oauth_service is None:
        from src.infrastructure.auth.google_oauth_service import GoogleOAuthService

        _google_oauth_service = GoogleOAuthService(
            client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
        )
    return _google_oauth_service


async def get_refresh_token_repo(
    session: AsyncSession = Depends(get_db_session),
) -> Any:
    """Provee el RefreshTokenRepository."""
    from src.infrastructure.persistence.repositories import RefreshTokenRepository

    return RefreshTokenRepository(session)


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
        # Modo desarrollo: si hay token JWT valido, extraer user_id real
        if authorization and authorization.startswith("Bearer "):
            token = authorization.replace("Bearer ", "")
            try:
                jwt_svc = get_jwt_service()
                payload = jwt_svc.validate_access_token(token)
                user_id = payload.get("sub")
                if user_id:
                    return str(user_id)
            except Exception:
                pass
        # Fallback: UUID placeholder para desarrollo sin auth
        return "00000000-0000-0000-0000-000000000001"

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticacion requerido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.replace("Bearer ", "")

    try:
        jwt_svc = get_jwt_service()
        payload = jwt_svc.validate_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalido: subject no encontrado",
            )
        return str(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token invalido: {str(e)}",
        ) from e
