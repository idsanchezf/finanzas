"""Repositorio concreto de Usuarios — SQLAlchemy 2.0 async."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.repositories import IUsuarioRepository
from src.infrastructure.persistence.models import UsuarioModel


class UsuarioRepository(IUsuarioRepository):
    """Implementacion concreta del repositorio de usuarios."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, usuario_id: uuid.UUID) -> UsuarioModel | None:
        stmt = select(UsuarioModel).where(UsuarioModel.id == usuario_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> UsuarioModel | None:
        stmt = select(UsuarioModel).where(UsuarioModel.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_auth_provider(self, provider: str, provider_id: str) -> UsuarioModel | None:
        stmt = select(UsuarioModel).where(
            UsuarioModel.auth_provider == provider,
            UsuarioModel.auth_provider_id == provider_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def save(self, usuario: Any) -> Any:
        if hasattr(usuario, "_sa_instance_state"):
            await self.session.merge(usuario)
        else:
            modelo = UsuarioModel(
                id=usuario.id,
                email=usuario.email,
                nombre=usuario.nombre,
                avatar_url=usuario.avatar_url,
                auth_provider=usuario.auth_provider.value
                if hasattr(usuario.auth_provider, "value")
                else usuario.auth_provider,
                auth_provider_id=usuario.auth_provider_id,
                tfa_enabled=usuario.tfa_enabled,
                preferencias_json=usuario.preferencias,
            )
            self.session.add(modelo)
            usuario = modelo
        await self.session.flush()
        return usuario

    async def delete(self, usuario_id: uuid.UUID) -> None:
        usuario = await self.get_by_id(usuario_id)
        if usuario:
            await self.session.delete(usuario)
            await self.session.flush()
