"""Tests para JWTService.validate_access_token — RED phase."""

from __future__ import annotations

import uuid

import pytest
from jose import JWTError

from src.infrastructure.auth.jwt_service import JWTService


class TestValidateAccessToken:
    """Escenarios para el metodo validate_access_token de JWTService."""

    def _make_service(self, secret: str | None = None) -> JWTService:
        return JWTService(
            secret=secret or "test-secret",
            access_token_ttl=900,
            refresh_token_ttl=604800,
            issuer="finance-report-test",
        )

    def test_Should_ReturnPayload_When_ValidTokenProvided(self) -> None:
        """Valida un token valido y retorna sus claims."""
        # Arrange --------------------------------------------------------
        svc = self._make_service()
        user_id = str(uuid.uuid4())
        token = svc.generate_access_token(
            user_id=user_id, email="test@example.com", nombre="Test User"
        )

        # Act ------------------------------------------------------------
        payload = svc.validate_access_token(token)

        # Assert ----------------------------------------------------------
        assert payload["sub"] == user_id
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_Should_RaiseJWTError_When_TokenExpired(self) -> None:
        """Lanza JWTError cuando el token ha expirado."""
        # Arrange --------------------------------------------------------
        svc = self._make_service(secret="exp-test-secret")
        svc.access_token_ttl = -1  # Token que expira inmediatamente
        user_id = str(uuid.uuid4())
        token = svc.generate_access_token(
            user_id=user_id, email="test@example.com", nombre="Test"
        )

        # Act & Assert ----------------------------------------------------
        with pytest.raises(JWTError):
            svc.validate_access_token(token)

    def test_Should_RaiseJWTError_When_InvalidSignature(self) -> None:
        """Lanza JWTError cuando el token tiene firma invalida."""
        # Arrange --------------------------------------------------------
        svc = self._make_service(secret="secret-a")
        user_id = str(uuid.uuid4())
        token = svc.generate_access_token(
            user_id=user_id, email="test@example.com", nombre="Test"
        )

        # Crear servicio con secreto diferente para validar
        svc_b = JWTService(
            secret="secret-b",
            access_token_ttl=900,
            refresh_token_ttl=604800,
            issuer="finance-report-test",
        )

        # Act & Assert ----------------------------------------------------
        with pytest.raises(JWTError):
            svc_b.validate_access_token(token)

    def test_Should_RaiseJWTError_When_NotAccessToken(self) -> None:
        """Lanza JWTError cuando el token no es de tipo 'access'."""
        # Arrange --------------------------------------------------------
        svc = self._make_service()
        user_id = str(uuid.uuid4())
        refresh_token = svc.generate_refresh_token(user_id=user_id)

        # Act & Assert ----------------------------------------------------
        with pytest.raises(JWTError, match="No es un access token"):
            svc.validate_access_token(refresh_token)

    def test_Should_RaiseJWTError_When_TokenMalformed(self) -> None:
        """Lanza JWTError cuando el token esta malformado."""
        # Arrange --------------------------------------------------------
        svc = self._make_service()

        # Act & Assert ----------------------------------------------------
        with pytest.raises(JWTError):
            svc.validate_access_token("not-a-valid-jwt")
