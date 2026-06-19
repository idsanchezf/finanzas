"""Tests de integracion para los endpoints de extractos.

Prueba el flujo completo: upload Excel -> listar -> detalle -> status -> eliminar.
Usa FastAPI TestClient con Dependency Overrides, SQLite en memoria y mocks
para dependencias externas (R2 Storage, JWT, bus de eventos).
"""

from __future__ import annotations

import os
import uuid
from contextlib import asynccontextmanager
from io import BytesIO
from typing import Any
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.api.routers.extracts import router as extracts_router
from src.infrastructure.persistence.models import Base, ExtractoModel


# ============================================================
# Helpers
# ============================================================
def _create_test_excel() -> bytes:
    """Crea un archivo Excel de prueba con formato generico."""
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active

    # Metadata
    ws["A1"] = "Informacion cliente"
    ws["A2"] = "Nombre: Test User"
    ws["A3"] = "Tarjeta: ****1234"

    # Headers de transacciones
    ws["A5"] = "Fecha"
    ws["B5"] = "Descripcion"
    ws["C5"] = "Valor"

    # Transacciones
    ws["A6"] = "01/06/2026"
    ws["B6"] = "RESTAURANTE DON PEPE"
    ws["C6"] = "45,500.00"

    ws["A7"] = "03/06/2026"
    ws["B7"] = "SUPERMERCADO LA 14"
    ws["C7"] = "120,000.00"

    ws["A8"] = "05/06/2026"
    ws["B8"] = "UBER TRIP"
    ws["C8"] = "15,800.00"

    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


# ============================================================
# Mock helpers
# ============================================================
class MockStorageClient:
    """Mock del cliente R2 Storage."""

    def upload_file(self, bucket: str, key: str, file_content: bytes | None = None, file_path: str | None = None) -> str:
        return f"https://r2.test/{bucket}/{key}"

    def download_file(self, bucket: str, key: str) -> bytes:
        return b"mock-content"

    def delete_file(self, bucket: str, key: str) -> None:
        pass


# ============================================================
# App builder con dependency overrides
# ============================================================
def _build_app(
    session_factory: async_sessionmaker[AsyncSession] | None = None,
    mock_current_user_id: str = "00000000-0000-0000-0000-000000000001",
    mock_storage_client: Any = None,
) -> FastAPI:
    """Crea un app FastAPI minimal con mocks inyectados via dependency_overrides."""
    from src.api.dependencies import (
        get_current_user_id,
        get_db_session,
        get_storage_client,
    )

    app = FastAPI()
    app.include_router(extracts_router, prefix="/api/v1/extracts", tags=["Extractos"])

    # Override: current user
    app.dependency_overrides[get_current_user_id] = lambda: mock_current_user_id

    # Override: storage client (mock)
    if mock_storage_client is not None:
        app.dependency_overrides[get_storage_client] = lambda: mock_storage_client

    # Override: DB session
    if session_factory is not None:

        async def override_get_db_session():
            async with session_factory() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise
                finally:
                    await session.close()

        app.dependency_overrides[get_db_session] = override_get_db_session
    else:
        app.dependency_overrides[get_db_session] = lambda: AsyncMock()

    return app


@asynccontextmanager
async def _client(app: FastAPI):
    """Context manager para AsyncClient."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ============================================================
# Fixtures con SQLite en memoria/archivo
# ============================================================
@pytest_asyncio.fixture
async def session_factory():
    """Fabrica de sesiones async para SQLite.

    Usa un archivo temporal para que multiples sesiones (test y API handler)
    compartan la misma base de datos. Se limpia automaticamente al final.
    """
    import os
    import tempfile

    db_fd, db_path = tempfile.mkstemp(suffix=".db", prefix="test_finance_")
    os.close(db_fd)  # cerramos el fd, solo usamos el path

    db_url = f"sqlite+aiosqlite:///{db_path}"

    engine = create_async_engine(
        db_url,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    yield factory

    await engine.dispose()

    # Limpiar archivo temporal
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest_asyncio.fixture
async def app(session_factory):
    """App FastAPI con BD SQLite y storage mockeado."""
    mock_storage = MockStorageClient()

    app = _build_app(
        session_factory=session_factory,
        mock_storage_client=mock_storage,
    )

    # Configurar variables de entorno para modo dev
    os.environ["ENVIRONMENT"] = "development"

    yield app

    # Cleanup: remover los overrides para evitar leaks entre tests
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def app_no_db():
    """App FastAPI sin BD real (mocks para tests de validacion)."""
    app = _build_app(mock_storage_client=MockStorageClient())
    yield app
    app.dependency_overrides.clear()


# ============================================================
# Test: POST /api/v1/extracts/upload
# ============================================================
class TestUploadEndpoint:
    """Escenarios para POST /api/v1/extracts/upload."""

    @pytest.mark.asyncio
    async def test_Should_Return201_When_ValidExcelFile(self, app: FastAPI) -> None:
        """Sube un archivo Excel valido y retorna extracto creado."""
        # Arrange --------------------------------------------------------
        test_excel = _create_test_excel()
        tarjeta_id = str(uuid.uuid4())

        # Act ------------------------------------------------------------
        async with _client(app) as client:
            response = await client.post(
                "/api/v1/extracts/upload",
                params={"tarjeta_id": tarjeta_id},
                files={"file": ("test_extracto.xlsx", test_excel, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )

        # Assert ----------------------------------------------------------
        assert response.status_code == 201
        data = response.json()
        assert "extracto_id" in data
        assert "estado" in data
        assert "progress_pct" in data
        assert data["progress_pct"] == 100

    @pytest.mark.asyncio
    async def test_Should_Return400_When_NonExcelFile(self, app_no_db: FastAPI) -> None:
        """Retorna 400 cuando el archivo no es Excel."""
        # Arrange --------------------------------------------------------
        tarjeta_id = str(uuid.uuid4())

        # Act ------------------------------------------------------------
        async with _client(app_no_db) as client:
            response = await client.post(
                "/api/v1/extracts/upload",
                params={"tarjeta_id": tarjeta_id},
                files={"file": ("documento.txt", b"contenido texto", "text/plain")},
            )

        # Assert ----------------------------------------------------------
        assert response.status_code == 400
        assert "excel" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_Should_Return400_When_FileTooLarge(self, app_no_db: FastAPI) -> None:
        """Retorna 400 cuando el archivo excede 10MB."""
        # Arrange --------------------------------------------------------
        tarjeta_id = str(uuid.uuid4())
        large_content = b"x" * (11 * 1024 * 1024)  # 11 MB

        # Act ------------------------------------------------------------
        async with _client(app_no_db) as client:
            response = await client.post(
                "/api/v1/extracts/upload",
                params={"tarjeta_id": tarjeta_id},
                files={"file": ("large.xlsx", large_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )

        # Assert ----------------------------------------------------------
        assert response.status_code == 400
        assert "tama" in response.json()["detail"].lower()  # "tamano" en espanol


# ============================================================
# Test: GET /api/v1/extracts
# ============================================================
class TestListExtractsEndpoint:
    """Escenarios para GET /api/v1/extracts."""

    @pytest.mark.asyncio
    async def test_Should_ListExtracts_When_UserHasExtracts(
        self, app: FastAPI, session_factory,
    ) -> None:
        """Lista extractos del usuario con paginacion."""
        # Arrange --------------------------------------------------------
        user_id = uuid.uuid4()
        # Semilla: crear extractos manualmente en BD
        async with session_factory() as session:
            for i in range(3):
                model = ExtractoModel(
                    id=uuid.uuid4(),
                    tarjeta_id=uuid.uuid4(),
                    usuario_id=user_id,
                    estado="COMPLETED",
                )
                session.add(model)
            await session.commit()

        # Override para que get_current_user_id retorne nuestro user_id
        from src.api.dependencies import get_current_user_id
        app.dependency_overrides[get_current_user_id] = lambda: str(user_id)

        # Act ------------------------------------------------------------
        async with _client(app) as client:
            response = await client.get("/api/v1/extracts", params={"page": 1, "size": 10})

        # Assert ----------------------------------------------------------
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 3
        assert len(data["items"]) == 3
        for item in data["items"]:
            assert "id" in item
            assert "estado" in item
            assert item["estado"] == "COMPLETED"

    @pytest.mark.asyncio
    async def test_Should_ReturnEmptyList_When_NoExtracts(
        self, app: FastAPI,
    ) -> None:
        """Retorna lista vacia cuando el usuario no tiene extractos."""
        # Arrange --------------------------------------------------------
        test_user_id = str(uuid.uuid4())
        from src.api.dependencies import get_current_user_id
        app.dependency_overrides[get_current_user_id] = lambda: test_user_id

        # Act ------------------------------------------------------------
        async with _client(app) as client:
            response = await client.get("/api/v1/extracts", params={"page": 1, "size": 10})

        # Assert ----------------------------------------------------------
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_Should_PaginateCorrectly(self, app: FastAPI, session_factory) -> None:
        """Respeta los parametros de paginacion page y size."""
        # Arrange --------------------------------------------------------
        user_id = uuid.uuid4()
        async with session_factory() as session:
            for i in range(5):
                model = ExtractoModel(
                    id=uuid.uuid4(),
                    tarjeta_id=uuid.uuid4(),
                    usuario_id=user_id,
                    estado="COMPLETED",
                )
                session.add(model)
            await session.commit()

        from src.api.dependencies import get_current_user_id
        app.dependency_overrides[get_current_user_id] = lambda: str(user_id)

        # Act ------------------------------------------------------------
        async with _client(app) as client:
            response = await client.get("/api/v1/extracts", params={"page": 1, "size": 2})

        # Assert ----------------------------------------------------------
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["size"] == 2


# ============================================================
# Test: GET /api/v1/extracts/{id}
# ============================================================
class TestGetExtractEndpoint:
    """Escenarios para GET /api/v1/extracts/{id}."""

    @pytest.mark.asyncio
    async def test_Should_ReturnExtractDetail_When_ValidId(
        self, app: FastAPI, session_factory,
    ) -> None:
        """Retorna el detalle completo de un extracto por ID."""
        # Arrange --------------------------------------------------------
        extracto_id = uuid.uuid4()
        tarjeta_id = uuid.uuid4()
        user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        async with session_factory() as session:
            model = ExtractoModel(
                id=extracto_id,
                tarjeta_id=tarjeta_id,
                usuario_id=user_id,
                estado="COMPLETED",
            )
            session.add(model)
            await session.commit()

        # Act ------------------------------------------------------------
        async with _client(app) as client:
            response = await client.get(f"/api/v1/extracts/{extracto_id}")

        # Assert ----------------------------------------------------------
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(extracto_id)
        assert data["estado"] == "COMPLETED"
        assert data["tarjeta_id"] == str(tarjeta_id)

    @pytest.mark.asyncio
    async def test_Should_Return404_When_ExtractNotFound(self, app: FastAPI) -> None:
        """Retorna 404 cuando el extracto no existe."""
        # Arrange --------------------------------------------------------
        fake_id = str(uuid.uuid4())

        # Act ------------------------------------------------------------
        async with _client(app) as client:
            response = await client.get(f"/api/v1/extracts/{fake_id}")

        # Assert ----------------------------------------------------------
        assert response.status_code == 404
        assert "extracto no encontrado" in response.json()["detail"].lower()


# ============================================================
# Test: GET /api/v1/extracts/{id}/status
# ============================================================
class TestGetExtractStatusEndpoint:
    """Escenarios para GET /api/v1/extracts/{id}/status."""

    @pytest.mark.asyncio
    async def test_Should_ReturnStatus_When_ValidId(
        self, app: FastAPI, session_factory,
    ) -> None:
        """Retorna el estado de procesamiento."""
        # Arrange --------------------------------------------------------
        extracto_id = uuid.uuid4()
        async with session_factory() as session:
            model = ExtractoModel(
                id=extracto_id,
                tarjeta_id=uuid.uuid4(),
                usuario_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                estado="PARSING",
                progress_pct=45,
            )
            session.add(model)
            await session.commit()

        # Act ------------------------------------------------------------
        async with _client(app) as client:
            response = await client.get(f"/api/v1/extracts/{extracto_id}/status")

        # Assert ----------------------------------------------------------
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PARSING"
        assert data["progress_pct"] == 45
        assert data["message"] is None

    @pytest.mark.asyncio
    async def test_Should_ReturnErrorMessage_When_ExtractInError(
        self, app: FastAPI, session_factory,
    ) -> None:
        """Incluye mensaje de error cuando el extracto esta en estado ERROR."""
        # Arrange --------------------------------------------------------
        extracto_id = uuid.uuid4()
        async with session_factory() as session:
            model = ExtractoModel(
                id=extracto_id,
                tarjeta_id=uuid.uuid4(),
                usuario_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                estado="ERROR",
                error_message="Archivo corrupto: formato no soportado",
                progress_pct=0,
            )
            session.add(model)
            await session.commit()

        # Act ------------------------------------------------------------
        async with _client(app) as client:
            response = await client.get(f"/api/v1/extracts/{extracto_id}/status")

        # Assert ----------------------------------------------------------
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ERROR"
        assert data["message"] is not None
        assert "corrupto" in data["message"]

    @pytest.mark.asyncio
    async def test_Should_Return404_When_NotFound(self, app: FastAPI) -> None:
        """Retorna 404 cuando el extracto no existe."""
        # Arrange --------------------------------------------------------
        fake_id = str(uuid.uuid4())

        # Act ------------------------------------------------------------
        async with _client(app) as client:
            response = await client.get(f"/api/v1/extracts/{fake_id}/status")

        # Assert ----------------------------------------------------------
        assert response.status_code == 404
        assert "extracto no encontrado" in response.json()["detail"].lower()


# ============================================================
# Test: DELETE /api/v1/extracts/{id}
# ============================================================
class TestDeleteExtractEndpoint:
    """Escenarios para DELETE /api/v1/extracts/{id}."""

    @pytest.mark.asyncio
    async def test_Should_Return204_When_ExtractDeleted(
        self, app: FastAPI, session_factory,
    ) -> None:
        """Elimina un extracto existente y retorna 204."""
        # Arrange --------------------------------------------------------
        extracto_id = uuid.uuid4()
        async with session_factory() as session:
            model = ExtractoModel(
                id=extracto_id,
                tarjeta_id=uuid.uuid4(),
                usuario_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                estado="COMPLETED",
            )
            session.add(model)
            await session.commit()

        # Act ------------------------------------------------------------
        async with _client(app) as client:
            response = await client.delete(f"/api/v1/extracts/{extracto_id}")

        # Assert ----------------------------------------------------------
        assert response.status_code == 204

        # Verificar que realmente se elimino
        async with session_factory() as session:
            from sqlalchemy import select
            stmt = select(ExtractoModel).where(ExtractoModel.id == extracto_id)
            result = await session.execute(stmt)
            deleted = result.scalar_one_or_none()
            assert deleted is None
