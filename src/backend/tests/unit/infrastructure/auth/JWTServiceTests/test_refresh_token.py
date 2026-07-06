"""Tests para JWTService (refresh tokens) — RED phase."""

from __future__ import annotations

import uuid

import pytest
from jose import JWTError

from src.infrastructure.auth.jwt_service import JWTService


class TestGenerateRefreshToken:
    """Escenarios para el metodo generate_refresh_token de JWTService."""

    def _make_service(self, secret: str | None = None) -> JWTService:
        return JWTService(
            secret=secret or "test-secret",
            access_token_ttl=900,
            refresh_token_ttl=604800,
            issuer="finance-report-test",
        )

    def test_Should_ReturnValidRefreshToken_When_UserIdProvided(self) -> None:
        """Genera un refresh token JWT con el user_id."""
        # Arrange --------------------------------------------------------
        svc = self._make_service()
        user_id = str(uuid.uuid4())

        # Act ------------------------------------------------------------
        token = svc.generate_refresh_token(user_id=user_id)

        # Assert ----------------------------------------------------------
        from jose import jwt

        payload = jwt.decode(token, "test-secret", algorithms=["HS256"])
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
        assert payload["iss"] == "finance-report-test"
        assert "exp" in payload
        assert "jti" in payload

    def test_Should_HaveLongerTTL_When_RefreshTokenGenerated(self) -> None:
        """El refresh token debe tener un TTL mas largo que el access token."""
        # Arrange --------------------------------------------------------
        svc = self._make_service()

        # Act ------------------------------------------------------------
        refresh = svc.generate_refresh_token(user_id=str(uuid.uuid4()))

        # Assert ----------------------------------------------------------
        from jose import jwt

        payload = jwt.decode(refresh, "test-secret", algorithms=["HS256"])
        assert payload["type"] == "refresh"


class TestValidateRefreshToken:
    """Escenarios para validate_refresh_token."""

    def _make_service(self, secret: str | None = None) -> JWTService:
        return JWTService(
            secret=secret or "test-secret",
            access_token_ttl=900,
            refresh_token_ttl=604800,
            issuer="finance-report-test",
        )

    def test_Should_ReturnPayload_When_ValidRefreshToken(self) -> None:
        """Valida un refresh token valido."""
        # Arrange --------------------------------------------------------
        svc = self._make_service()
        refresh = svc.generate_refresh_token(user_id=str(uuid.uuid4()))

        # Act ------------------------------------------------------------
        payload = svc.validate_refresh_token(refresh)

        # Assert ----------------------------------------------------------
        assert payload["type"] == "refresh"

    def test_Should_RaiseJWTError_When_AccessTokenUsedAsRefresh(self) -> None:
        """Lanza error si se intenta validar un access token como refresh."""
        # Arrange --------------------------------------------------------
        svc = self._make_service()
        access = svc.generate_access_token(
            user_id=str(uuid.uuid4()), email="t@t.com", nombre="T"
        )

        # Act & Assert ----------------------------------------------------
        with pytest.raises(JWTError, match="No es un refresh token"):
            svc.validate_refresh_token(access)

    def test_Should_RaiseJWTError_When_RefreshTokenExpired(self) -> None:
        """Lanza JWTError cuando el refresh token expiro."""
        # Arrange --------------------------------------------------------
        svc = self._make_service()
        svc.refresh_token_ttl = -1
        refresh = svc.generate_refresh_token(user_id=str(uuid.uuid4()))

        # Act & Assert ----------------------------------------------------
        with pytest.raises(JWTError):
            svc.validate_refresh_token(refresh)
