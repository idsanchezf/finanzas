"""Tests para JWTService.generate_access_token — RED phase."""

from __future__ import annotations

import os
import uuid

import pytest
from jose import jwt

from src.infrastructure.auth.jwt_service import JWTService


class TestGenerateAccessToken:
    """Escenarios para el metodo generate_access_token de JWTService."""

    def _make_service(self, secret: str | None = None, ttl: int = 900) -> JWTService:
        """Fabrica de JWTService con valores por defecto o inyectados."""
        return JWTService(
            secret=secret or "test-secret",
            access_token_ttl=ttl,
            refresh_token_ttl=604800,
            issuer="finance-report-test",
        )

    def test_Should_ReturnValidJWT_When_UserDataProvided(self) -> None:
        """Genera un access token JWT firmado con los claims del usuario."""
        # Arrange --------------------------------------------------------
        svc = self._make_service()
        user_id = str(uuid.uuid4())
        email = "test@example.com"
        nombre = "Test User"

        # Act ------------------------------------------------------------
        token = svc.generate_access_token(
            user_id=user_id, email=email, nombre=nombre
        )

        # Assert ----------------------------------------------------------
        assert isinstance(token, str)
        assert token.count(".") == 2  # header.payload.signature

        # Decodificar y verificar claims
        payload = jwt.decode(token, "test-secret", algorithms=["HS256"])
        assert payload["sub"] == user_id
        assert payload["email"] == email
        assert payload["nombre"] == nombre
        assert payload["type"] == "access"
        assert payload["iss"] == "finance-report-test"
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload

    def test_Should_ExpireAfterTTL_When_TokenCreated(self) -> None:
        """El token debe expirar despues del TTL configurado."""
        # Arrange --------------------------------------------------------
        svc = self._make_service(ttl=1)  # 1 segundo
        user_id = str(uuid.uuid4())

        # Act ------------------------------------------------------------
        token = svc.generate_access_token(user_id=user_id, email="e@e.com", nombre="N")

        # Assert ----------------------------------------------------------
        import time
        time.sleep(2)

        # Debe fallar porque expiro
        with pytest.raises(Exception):
            jwt.decode(token, "test-secret", algorithms=["HS256"])

    def test_Should_ContainUniqueJTI_When_MultipleTokensGenerated(self) -> None:
        """Cada token debe tener un JTI (JWT ID) unico."""
        # Arrange --------------------------------------------------------
        svc = self._make_service()
        user_id = str(uuid.uuid4())

        # Act ------------------------------------------------------------
        token1 = svc.generate_access_token(user_id=user_id, email="a@a.com", nombre="A")
        token2 = svc.generate_access_token(user_id=user_id, email="a@a.com", nombre="A")

        # Assert ----------------------------------------------------------
        payload1 = jwt.decode(token1, "test-secret", algorithms=["HS256"])
        payload2 = jwt.decode(token2, "test-secret", algorithms=["HS256"])
        assert payload1["jti"] != payload2["jti"]
