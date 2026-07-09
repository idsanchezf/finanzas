"""Tests de integracion para los endpoints de autenticacion.

Prueba el flujo completo: login -> refresh -> logout -> /me.
Construye un app FastAPI minimal con solo el router de auth
y dependency overrides para mockear la capa de BD.
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.api.routers.auth import router as auth_router


# ============================================================
# Mock helpers
# ============================================================
class MockUsuario:
    """Usuario mock para pruebas."""

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid.uuid4())
        self.email = kwargs.get("email", "dev@financereport.local")
        self.nombre = kwargs.get("nombre", "Dev User")
        self.avatar_url = kwargs.get("avatar_url")


class MockRefreshToken:
    """Refresh token mock."""

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", uuid.uuid4())
        self.usuario_id = kwargs.get("usuario_id", uuid.uuid4())
        self.token_jti = kwargs.get("token_jti", str(uuid.uuid4()))
        self.expires_at = kwargs.get("expires_at", datetime.now(UTC))
        self.revoked = kwargs.get("revoked", False)


# ============================================================
# App builder con dependency overrides
# ============================================================
def _build_app(
    usuario_repo_mock: Any = None,
    refresh_token_repo_mock: Any = None,
    google_oauth_svc_mock: Any = None,
) -> FastAPI:
    """Crea un app FastAPI minimal con mocks inyectados via dependency_overrides."""
    from src.api.dependencies import (
        get_db_session,
        get_google_oauth_service,
        get_refresh_token_repo,
        get_usuario_repo,
    )

    app = FastAPI()
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Autenticacion"])

    # Mock DB session
    app.dependency_overrides[get_db_session] = lambda: AsyncMock()

    # Mock repos y servicios si se proveen
    if usuario_repo_mock is not None:
        app.dependency_overrides[get_usuario_repo] = lambda: usuario_repo_mock
    if refresh_token_repo_mock is not None:
        app.dependency_overrides[get_refresh_token_repo] = lambda: refresh_token_repo_mock
    if google_oauth_svc_mock is not None:
        app.dependency_overrides[get_google_oauth_service] = lambda: google_oauth_svc_mock

    return app


@asynccontextmanager
async def _client(app: FastAPI):
    """Context manager para AsyncClient con un app dado."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ============================================================
# Helpers para construir mocks comunes
# ============================================================
def _mock_usuario_repo(usuario_existente: MockUsuario | None = None):
    """Repo de usuarios que guarda y busca."""
    repo = MagicMock()
    repo.get_by_email = AsyncMock(return_value=usuario_existente)
    repo.save = AsyncMock(return_value=usuario_existente or MockUsuario())
    repo.get_by_id = AsyncMock(return_value=usuario_existente or MockUsuario())
    return repo


def _mock_google_oauth():
    """Google OAuth que siempre valida en dev."""
    svc = MagicMock()
    svc.validate_id_token = AsyncMock(
        return_value={
            "valid": True,
            "email": "dev@financereport.local",
            "nombre": "Dev User",
            "avatar_url": None,
            "provider": "google",
            "provider_id": "dev-google-id",
        }
    )
    return svc


def _mock_rt_repo():
    """Refresh token repo que siempre guarda y encuentra."""
    repo = MagicMock()
    repo.save = AsyncMock(return_value=MockRefreshToken())
    repo.find_valid_by_jti = AsyncMock(return_value=MockRefreshToken())
    repo.revoke = AsyncMock(return_value=True)
    repo.revoke_all_for_user = AsyncMock(return_value=1)
    return repo


# ============================================================
# Tests
# ============================================================
class TestLoginEndpoint:
    """Escenarios para POST /api/v1/auth/login."""

    async def test_Should_ReturnTokens_When_ValidGoogleToken(self, monkeypatch) -> None:
        """Login exitoso con id_token valido de Google (modo dev)."""
        # Arrange --------------------------------------------------------
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("JWT_SECRET", "test-secret-for-integration")

        app = _build_app(
            usuario_repo_mock=_mock_usuario_repo(),
            refresh_token_repo_mock=_mock_rt_repo(),
            google_oauth_svc_mock=_mock_google_oauth(),
        )

        # Act ------------------------------------------------------------
        async with _client(app) as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"provider": "google", "id_token": "dev-token"},
            )

        # Assert ----------------------------------------------------------
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 900
        assert "user" in data
        assert data["user"]["email"] == "dev@financereport.local"

    async def test_Should_Return400_When_MissingProvider(self) -> None:
        """Retorna 400 cuando falta el provider en el body."""
        # Arrange --------------------------------------------------------
        app = _build_app()

        # Act ------------------------------------------------------------
        async with _client(app) as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"id_token": "some-token"},
            )

        # Assert ----------------------------------------------------------
        assert response.status_code == 400
        assert "provider" in response.json()["detail"].lower()

    async def test_Should_Return400_When_UnsupportedProvider(self) -> None:
        """Retorna 400 cuando el provider no es soportado."""
        # Arrange --------------------------------------------------------
        app = _build_app()

        # Act ------------------------------------------------------------
        async with _client(app) as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"provider": "facebook", "id_token": "token"},
            )

        # Assert ----------------------------------------------------------
        assert response.status_code == 400
        assert "no soportado" in response.json()["detail"].lower()


class TestRefreshEndpoint:
    """Escenarios para POST /api/v1/auth/refresh."""

    async def test_Should_ReturnNewAccessToken_When_ValidRefreshToken(self, monkeypatch) -> None:
        """Renueva access token con refresh token valido."""
        # Arrange --------------------------------------------------------
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("JWT_SECRET", "test-secret-for-integration")

        usuario = MockUsuario()
        app = _build_app(
            usuario_repo_mock=_mock_usuario_repo(usuario),
            refresh_token_repo_mock=_mock_rt_repo(),
            google_oauth_svc_mock=_mock_google_oauth(),
        )

        async with _client(app) as client:
            # Login primero para obtener refresh token
            login_resp = await client.post(
                "/api/v1/auth/login",
                json={"provider": "google", "id_token": "dev-token"},
            )
            refresh_token = login_resp.json()["refresh_token"]

        # Act ------------------------------------------------------------
        async with _client(app) as client:
            response = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh_token},
            )

        # Assert ----------------------------------------------------------
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_Should_Return400_When_RefreshTokenMissing(self) -> None:
        """Retorna 400 cuando no se envia refresh_token."""
        # Arrange --------------------------------------------------------
        app = _build_app()

        # Act ------------------------------------------------------------
        async with _client(app) as client:
            response = await client.post(
                "/api/v1/auth/refresh",
                json={},
            )

        # Assert ----------------------------------------------------------
        assert response.status_code == 400

    async def test_Should_Return401_When_RefreshTokenInvalid(self, monkeypatch) -> None:
        """Retorna 401 cuando el refresh token es invalido."""
        # Arrange --------------------------------------------------------
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("JWT_SECRET", "test-secret-for-integration")

        app = _build_app()

        # Act ------------------------------------------------------------
        async with _client(app) as client:
            response = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "invalid.token.here"},
            )

        # Assert ----------------------------------------------------------
        assert response.status_code == 401


class TestLogoutEndpoint:
    """Escenarios para POST /api/v1/auth/logout."""

    async def test_Should_ReturnSuccess_When_ValidRefreshToken(self, monkeypatch) -> None:
        """Logout exitoso con refresh token valido."""
        # Arrange --------------------------------------------------------
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("JWT_SECRET", "test-secret-for-integration")

        app = _build_app(
            usuario_repo_mock=_mock_usuario_repo(),
            refresh_token_repo_mock=_mock_rt_repo(),
            google_oauth_svc_mock=_mock_google_oauth(),
        )

        async with _client(app) as client:
            login_resp = await client.post(
                "/api/v1/auth/login",
                json={"provider": "google", "id_token": "dev-token"},
            )
            refresh_token = login_resp.json()["refresh_token"]

        # Act ------------------------------------------------------------
        async with _client(app) as client:
            response = await client.post(
                "/api/v1/auth/logout",
                json={"refresh_token": refresh_token},
            )

        # Assert ----------------------------------------------------------
        assert response.status_code == 200
        assert response.json()["status"] == "logged_out"

    async def test_Should_ReturnSuccess_When_InvalidToken(self) -> None:
        """Logout retorna exito incluso con token invalido."""
        # Arrange --------------------------------------------------------
        app = _build_app()

        # Act ------------------------------------------------------------
        async with _client(app) as client:
            response = await client.post(
                "/api/v1/auth/logout",
                json={"refresh_token": "garbage-token"},
            )

        # Assert ----------------------------------------------------------
        assert response.status_code == 200
        assert response.json()["status"] == "logged_out"


class TestMeEndpoint:
    """Escenarios para GET /api/v1/auth/me."""

    async def test_Should_ReturnUserData_When_Authenticated(self, monkeypatch) -> None:
        """Retorna datos del usuario autenticado via header en modo dev."""
        # Arrange --------------------------------------------------------
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("JWT_SECRET", "test-secret-for-integration")

        app = _build_app()

        # Act ------------------------------------------------------------
        async with _client(app) as client:
            response = await client.get("/api/v1/auth/me")

        # Assert ----------------------------------------------------------
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "nombre" in data
        assert "email" in data
