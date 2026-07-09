"""Tests para GoogleOAuthService.validate_id_token — RED phase."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from src.infrastructure.auth.google_oauth_service import GoogleOAuthService


class TestValidateIdToken:
    """Escenarios para el metodo validate_id_token de GoogleOAuthService."""

    # ------------------------------------------------------------------
    # Helper: payload que simula la respuesta de Google tokeninfo
    # ------------------------------------------------------------------
    def _make_service(self) -> GoogleOAuthService:
        return GoogleOAuthService()

    def _google_payload(self, **overrides) -> dict:
        """Fabrica un payload tipico de Google tokeninfo."""
        base = {
            "iss": "https://accounts.google.com",
            "sub": "1234567890",
            "email": "user@gmail.com",
            "email_verified": "true",
            "name": "Test User",
            "picture": "https://lh3.googleusercontent.com/photo.jpg",
            "given_name": "Test",
            "family_name": "User",
            "locale": "es",
        }
        base.update(overrides)
        return base

    async def test_Should_ExtractUserInfo_When_ValidGooglePayload(self) -> None:
        """Extrae email, nombre y avatar de la respuesta de Google."""
        # Arrange --------------------------------------------------------
        svc = self._make_service()
        payload = self._google_payload()

        with patch.object(svc, "_fetch_token_info", AsyncMock(return_value=payload)):
            # Act ------------------------------------------------------------
            user_info = await svc.validate_id_token("fake-google-id-token")

        # Assert ----------------------------------------------------------
        assert user_info["valid"] is True
        assert user_info["email"] == "user@gmail.com"
        assert user_info["nombre"] == "Test User"
        assert user_info["avatar_url"] == "https://lh3.googleusercontent.com/photo.jpg"
        assert user_info["provider"] == "google"
        assert user_info["provider_id"] == "1234567890"

    async def test_Should_ReturnError_When_InvalidIssuer(self) -> None:
        """Retorna error si el issuer no es Google."""
        # Arrange --------------------------------------------------------
        svc = self._make_service()
        payload = self._google_payload(iss="https://accounts.evil.com")

        with patch.object(svc, "_fetch_token_info", AsyncMock(return_value=payload)):
            # Act ------------------------------------------------------------
            result = await svc.validate_id_token("fake-token")

        # Assert ----------------------------------------------------------
        assert result["valid"] is False
        assert "error" in result
        assert "issuer" in result["error"].lower()

    async def test_Should_ReturnError_When_EmailNotVerified(self) -> None:
        """Retorna error si el email no esta verificado por Google."""
        # Arrange --------------------------------------------------------
        svc = self._make_service()
        payload = self._google_payload(email_verified="false")

        with patch.object(svc, "_fetch_token_info", AsyncMock(return_value=payload)):
            # Act ------------------------------------------------------------
            result = await svc.validate_id_token("fake-token")

        # Assert ----------------------------------------------------------
        assert result["valid"] is False
        assert "error" in result
        assert "verificado" in result["error"].lower()

    async def test_Should_ReturnError_When_GoogleAPIUnreachable(self) -> None:
        """Retorna error cuando la API de Google no responde."""
        # Arrange --------------------------------------------------------
        svc = self._make_service()

        with patch.object(
            svc, "_fetch_token_info", AsyncMock(side_effect=Exception("Connection timeout"))
        ):
            # Act ------------------------------------------------------------
            result = await svc.validate_id_token("fake-token")

        # Assert ----------------------------------------------------------
        assert result["valid"] is False
        assert "error" in result
        assert "timeout" in result["error"].lower()
