"""Repositorio concreto de Refresh Tokens — SQLAlchemy 2.0 async."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.models import RefreshTokenModel


class RefreshTokenRepository:
    """Repositorio para gestionar refresh tokens persistidos.

    Almacena el JTI (JWT ID) del refresh token para poder revocarlo
    y evitar reutilizacion tras logout.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(
        self, usuario_id: uuid.UUID, token_jti: str, expires_at: datetime
    ) -> RefreshTokenModel:
        """Guarda un nuevo refresh token.

        Args:
            usuario_id: UUID del usuario dueno del token.
            token_jti: JWT ID unico del refresh token.
            expires_at: Fecha de expiracion del token.

        Returns:
            El modelo RefreshTokenModel creado.
        """
        modelo = RefreshTokenModel(
            usuario_id=usuario_id,
            token_jti=token_jti,
            expires_at=expires_at,
        )
        self.session.add(modelo)
        await self.session.flush()
        return modelo

    async def find_valid_by_jti(self, token_jti: str) -> RefreshTokenModel | None:
        """Busca un refresh token por su JTI que no este revocado ni expirado.

        Args:
            token_jti: JWT ID del refresh token.

        Returns:
            RefreshTokenModel si existe y es valido, None en caso contrario.
        """
        stmt = select(RefreshTokenModel).where(
            RefreshTokenModel.token_jti == token_jti,
            RefreshTokenModel.revoked == False,
            RefreshTokenModel.expires_at > datetime.now(timezone.utc),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke(self, token_jti: str) -> bool:
        """Revoca un refresh token por su JTI.

        Args:
            token_jti: JWT ID del refresh token a revocar.

        Returns:
            True si se revoco al menos un token, False si no se encontro.
        """
        stmt = (
            update(RefreshTokenModel)
            .where(RefreshTokenModel.token_jti == token_jti)
            .values(revoked=True)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0

    async def revoke_all_for_user(self, usuario_id: uuid.UUID) -> int:
        """Revoca todos los refresh tokens de un usuario.

        Args:
            usuario_id: UUID del usuario.

        Returns:
            Numero de tokens revocados.
        """
        stmt = (
            update(RefreshTokenModel)
            .where(
                RefreshTokenModel.usuario_id == usuario_id,
                RefreshTokenModel.revoked == False,
            )
            .values(revoked=True)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount
