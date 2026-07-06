"""JWT Service — Generacion y validacion de tokens JWT (access + refresh).

Usa python-jose con HMAC-SHA256 (HS256) para firmar.
Access token: 15 minutos TTL por defecto.
Refresh token: 7 dias TTL por defecto.
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt


class JWTService:
    """Servicio de generacion y validacion de JWT tokens."""

    def __init__(
        self,
        secret: str | None = None,
        access_token_ttl: int = 900,  # 15 minutos
        refresh_token_ttl: int = 604800,  # 7 dias
        issuer: str = "finance-report",
        algorithm: str = "HS256",
    ) -> None:
        self.secret = secret or os.getenv("JWT_SECRET", "dev-secret")
        self.access_token_ttl = access_token_ttl
        self.refresh_token_ttl = refresh_token_ttl
        self.issuer = issuer
        self.algorithm = algorithm

    # ================================================================
    # Access Tokens
    # ================================================================

    def generate_access_token(self, user_id: str, email: str, nombre: str) -> str:
        """Genera un access token JWT.

        Args:
            user_id: UUID del usuario.
            email: Email del usuario.
            nombre: Nombre del usuario.

        Returns:
            JWT access token firmado.
        """
        now = datetime.now(UTC)
        payload = {
            "sub": user_id,
            "email": email,
            "nombre": nombre,
            "type": "access",
            "iss": self.issuer,
            "iat": now,
            "exp": now + timedelta(seconds=self.access_token_ttl),
            "jti": str(uuid.uuid4()),
        }
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def validate_access_token(self, token: str) -> dict:
        """Valida un access token y retorna sus claims.

        Args:
            token: JWT access token.

        Returns:
            Diccionario con los claims del token.

        Raises:
            JWTError: Si el token es invalido, expirado o no es access token.
        """
        payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])

        if payload.get("type") != "access":
            raise JWTError("No es un access token valido")

        return payload

    # ================================================================
    # Refresh Tokens
    # ================================================================

    def generate_refresh_token(self, user_id: str) -> str:
        """Genera un refresh token JWT.

        Args:
            user_id: UUID del usuario.

        Returns:
            JWT refresh token firmado.
        """
        now = datetime.now(UTC)
        payload = {
            "sub": user_id,
            "type": "refresh",
            "iss": self.issuer,
            "iat": now,
            "exp": now + timedelta(seconds=self.refresh_token_ttl),
            "jti": str(uuid.uuid4()),
        }
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def validate_refresh_token(self, token: str) -> dict:
        """Valida un refresh token y retorna sus claims.

        Args:
            token: JWT refresh token.

        Returns:
            Diccionario con los claims del token.

        Raises:
            JWTError: Si el token es invalido, expirado o no es refresh token.
        """
        payload = jwt.decode(token, self.secret, algorithms=[self.algorithm])

        if payload.get("type") != "refresh":
            raise JWTError("No es un refresh token valido")

        return payload
