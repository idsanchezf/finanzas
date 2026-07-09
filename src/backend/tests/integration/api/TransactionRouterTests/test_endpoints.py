"""Tests de integracion para los endpoints de transacciones.

Prueba el flujo completo REST contra SQLite en memoria:
- Listar con filtros, paginacion y sorting
- Obtener detalle por ID
- Cambiar categoria individual
- Clasificacion masiva
- Busqueda de comercio
- Transacciones no clasificadas

Usa TestClient (httpx.AsyncClient) + SQLite en memoria via aiosqlite.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import date
from decimal import Decimal

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.infrastructure.persistence.models import (
    Base,
    CategoriaModel,
    ExtractoModel,
    TarjetaModel,
    TransaccionModel,
    UsuarioModel,
)

pytestmark = pytest.mark.integration


# ============================================================
# Helpers — construir app con dependency overrides
# ============================================================

TEST_USER_ID = uuid.UUID("a0000000-0000-0000-0000-000000000001")
TEST_EXTRACTO_ID = uuid.UUID("b0000000-0000-0000-0000-000000000001")
TEST_CATEGORIA_ID = uuid.UUID("c0000000-0000-0000-0000-000000000001")
TEST_CATEGORIA_ALT_ID = uuid.UUID("c0000000-0000-0000-0000-000000000002")


async def _build_test_app(
    session_factory: async_sessionmaker[AsyncSession],
    usuario_id: uuid.UUID = TEST_USER_ID,
) -> FastAPI:
    """Construye un app FastAPI con el router de transacciones y overrides.

    Todas las dependencias (DB, repos, handlers) se inyectan con una
    sesion de SQLite en memoria compartida entre repositorios.
    """
    from fastapi import Depends

    from src.api.dependencies import (
        get_categoria_repo,
        get_command_handler,
        get_current_user_id,
        get_db_session,
        get_extracto_repo,
        get_tarjeta_repo,
        get_transaccion_repo,
        get_usuario_repo,
    )
    from src.api.middleware.error_handler import handle_domain_exception
    from src.api.routers.transactions import router as transactions_router
    from src.application.handlers.command_handlers import CommandHandler
    from src.domain.exceptions import DomainError
    from src.infrastructure.persistence.repositories import (
        CategoriaRepository,
        ExtractoRepository,
        TarjetaRepository,
        TransaccionRepository,
        UsuarioRepository,
    )

    app = FastAPI()
    app.include_router(transactions_router, prefix="/api/v1/transactions")

    # ---- Exception handler: DomainError -> 404/409/422 ----
    app.add_exception_handler(DomainError, handle_domain_exception)

    # ---- Override: DB session ----
    async def _override_db_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db_session] = _override_db_session

    # ---- Override: current user ----
    app.dependency_overrides[get_current_user_id] = lambda: str(usuario_id)

    # ---- Override: repos (dependen de get_db_session, que ya esta override) ----
    # FastAPI resuelve la cadena: get_db_session -> get_transaccion_repo -> get_query_handler
    # Como get_db_session esta override, todos usan nuestra sesion de test.

    # ---- Override: command handler (con event_bus=None para tests) ----
    async def _override_command_handler(
        extracto_repo: ExtractoRepository = Depends(get_extracto_repo),
        transaccion_repo: TransaccionRepository = Depends(get_transaccion_repo),
        categoria_repo: CategoriaRepository = Depends(get_categoria_repo),
        tarjeta_repo: TarjetaRepository = Depends(get_tarjeta_repo),
        usuario_repo: UsuarioRepository = Depends(get_usuario_repo),
    ) -> CommandHandler:
        return CommandHandler(
            extracto_repo=extracto_repo,
            transaccion_repo=transaccion_repo,
            categoria_repo=categoria_repo,
            presupuesto_repo=None,
            tarjeta_repo=tarjeta_repo,
            usuario_repo=usuario_repo,
            event_bus=None,
        )

    app.dependency_overrides[get_command_handler] = _override_command_handler

    return app


async def _create_test_data(session: AsyncSession) -> None:
    """Inserta datos de prueba: usuario, tarjeta, extracto, categorias, transacciones."""
    # Usuario
    session.add(
        UsuarioModel(
            id=TEST_USER_ID,
            email="test@financereport.local",
            nombre="Test User",
            auth_provider="google",
            auth_provider_id="test-google-id",
        )
    )

    # Tarjeta
    session.add(
        TarjetaModel(
            id=uuid.uuid4(),
            usuario_id=TEST_USER_ID,
            banco="Bancolombia",
            ultimos_4_digitos="1234",
            tipo="credito",
        )
    )

    # Extracto
    session.add(
        ExtractoModel(
            id=TEST_EXTRACTO_ID,
            tarjeta_id=uuid.uuid4(),
            usuario_id=TEST_USER_ID,
            estado="COMPLETED",
            periodo_inicio=date(2026, 6, 1),
            periodo_fin=date(2026, 6, 30),
            fecha_corte=date(2026, 6, 15),
            pago_total=Decimal("5000.00"),
            cupo_total=Decimal("10000.00"),
            cupo_disponible=Decimal("5000.00"),
        )
    )

    # Categorias
    session.add(
        CategoriaModel(
            id=TEST_CATEGORIA_ID,
            nombre="Alimentacion",
            icono="🍔",
            color="#FF6B6B",
            es_predefinida=True,
            palabras_clave=["restaurante", "comida"],
        )
    )
    session.add(
        CategoriaModel(
            id=TEST_CATEGORIA_ALT_ID,
            nombre="Transporte",
            icono="🚗",
            color="#4ECDC4",
            es_predefinida=True,
            palabras_clave=["gasolina", "transporte"],
        )
    )

    # Transacciones de prueba
    transacciones = [
        TransaccionModel(
            id=uuid.UUID("d0000000-0000-0000-0000-000000000001"),
            extracto_id=TEST_EXTRACTO_ID,
            usuario_id=TEST_USER_ID,
            numero_autorizacion="AUTH001",
            fecha=date(2026, 6, 5),
            comercio_original="RESTAURANTE DON PEPE",
            comercio_traducido="Don Pepe",
            valor=Decimal("45.50"),
            categoria_id=TEST_CATEGORIA_ID,
            confidence=Decimal("95.00"),
            es_abono=False,
            es_cuota=False,
        ),
        TransaccionModel(
            id=uuid.UUID("d0000000-0000-0000-0000-000000000002"),
            extracto_id=TEST_EXTRACTO_ID,
            usuario_id=TEST_USER_ID,
            numero_autorizacion="AUTH002",
            fecha=date(2026, 6, 10),
            comercio_original="NETFLIX STREAMING",
            comercio_traducido="Netflix",
            valor=Decimal("29.90"),
            categoria_id=TEST_CATEGORIA_ALT_ID,
            confidence=Decimal("88.00"),
            es_abono=False,
            es_cuota=False,
        ),
        TransaccionModel(
            id=uuid.UUID("d0000000-0000-0000-0000-000000000003"),
            extracto_id=TEST_EXTRACTO_ID,
            usuario_id=TEST_USER_ID,
            numero_autorizacion="AUTH003",
            fecha=date(2026, 6, 12),
            comercio_original="DLO*DIDI FOOD CO PAYIN",
            comercio_traducido=None,
            valor=Decimal("18.75"),
            categoria_id=None,
            confidence=Decimal("55.00"),
            es_abono=False,
            es_cuota=False,
        ),
        TransaccionModel(
            id=uuid.UUID("d0000000-0000-0000-0000-000000000004"),
            extracto_id=TEST_EXTRACTO_ID,
            usuario_id=TEST_USER_ID,
            numero_autorizacion="AUTH004",
            fecha=date(2026, 6, 15),
            comercio_original="PAGO TARJETA",
            comercio_traducido=None,
            valor=Decimal("-500.00"),
            categoria_id=None,
            confidence=Decimal("100.00"),
            es_abono=True,
            es_cuota=False,
        ),
        TransaccionModel(
            id=uuid.UUID("d0000000-0000-0000-0000-000000000005"),
            extracto_id=TEST_EXTRACTO_ID,
            usuario_id=TEST_USER_ID,
            numero_autorizacion="AUTH005",
            fecha=date(2026, 6, 3),
            comercio_original="COMPRA MUEBLES CUOTAS",
            comercio_traducido=None,
            valor=Decimal("1200.00"),
            numero_cuotas="2/12",
            cuotas_totales=12,
            cuota_actual=2,
            valor_cuota=Decimal("100.00"),
            categoria_id=None,
            confidence=Decimal("65.00"),
            es_abono=False,
            es_cuota=True,
        ),
    ]
    for t in transacciones:
        session.add(t)

    await session.flush()


# ============================================================
# Fixture: app con datos de prueba
# ============================================================


@pytest_asyncio.fixture
async def test_app() -> AsyncGenerator[FastAPI, None]:
    """Crea un app FastAPI con SQLite en memoria y datos de prueba.

    Usa un nombre de BD unico por test para evitar contaminacion.
    cache=shared permite que multiples sesiones compartan la misma BD.
    """
    import uuid as uuid_lib

    db_name = f"trans_test_{uuid_lib.uuid4().hex}"
    engine = create_async_engine(
        f"sqlite+aiosqlite:///file:{db_name}?mode=memory&cache=shared",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Insertar datos de prueba
    async with session_factory() as session:
        await _create_test_data(session)
        await session.commit()

    app = await _build_test_app(session_factory)
    yield app

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient HTTP conectado al test_app."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test/api/v1/transactions",
        follow_redirects=True,
    ) as c:
        yield c


# ============================================================
# ListTransactions — GET /
# ============================================================


class TestListTransactions:
    """Escenarios para GET / — listar transacciones con filtros."""

    async def test_Should_ReturnPaginatedResults_When_NoFilters(
        self,
        client: AsyncClient,
    ) -> None:
        """Retorna lista paginada de transacciones del usuario."""
        # Act ------------------------------------------------------------
        response = await client.get("/")

        # Assert ----------------------------------------------------------
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert data["total"] == 5
        assert len(data["items"]) == 5  # size default=50, 5 total
        assert data["page"] == 1

    async def test_Should_RespectPageSize_When_SizeParam(
        self,
        client: AsyncClient,
    ) -> None:
        """Respeta el parametro size para paginar."""
        # Act ------------------------------------------------------------
        response = await client.get("/?size=2")

        # Assert ----------------------------------------------------------
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2

    async def test_Should_ReturnSecondPage_When_Page2(
        self,
        client: AsyncClient,
    ) -> None:
        """Retorna la segunda pagina correctamente."""
        # Act ------------------------------------------------------------
        response = await client.get("/?page=2&size=2")

        # Assert ----------------------------------------------------------
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["size"] == 2
        assert data["total"] == 5
        assert len(data["items"]) == 2

    async def test_Should_FilterByExtractId_When_ExtractFilterProvided(
        self,
        client: AsyncClient,
    ) -> None:
        """Filtra transacciones por extracto_id."""
        # Act ------------------------------------------------------------
        other_id = uuid.uuid4()
        response = await client.get(f"/?extract_id={other_id}")

        # Assert ----------------------------------------------------------
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    async def test_Should_FilterByCategory_When_CategoryFilterProvided(
        self,
        client: AsyncClient,
    ) -> None:
        """Filtra transacciones por categoria_id."""
        # Act ------------------------------------------------------------
        response = await client.get(f"/?category_id={TEST_CATEGORIA_ID}")

        # Assert ----------------------------------------------------------
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["categoria_id"] == str(TEST_CATEGORIA_ID)

    async def test_Should_FilterBySearch_When_SearchTermProvided(
        self,
        client: AsyncClient,
    ) -> None:
        """Filtra por termino de busqueda en comercio."""
        # Act ------------------------------------------------------------
        response = await client.get("/?search=netflix")

        # Assert ----------------------------------------------------------
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert "netflix" in data["items"][0]["comercio"].lower()

    async def test_Should_FilterByConfidenceHigh_When_ConfidenceFilterProvided(
        self,
        client: AsyncClient,
    ) -> None:
        """Filtra por nivel de confianza HIGH."""
        # Act ------------------------------------------------------------
        response = await client.get("/?confidence=HIGH")

        # Assert ----------------------------------------------------------
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["confidence"] is None or item["confidence"] >= 90

    async def test_Should_SortByValorAsc_When_SortParamsProvided(
        self,
        client: AsyncClient,
    ) -> None:
        """Ordena transacciones por valor ascendente."""
        # Act ------------------------------------------------------------
        response = await client.get("/?sort_by=valor&order=asc")

        # Assert ----------------------------------------------------------
        assert response.status_code == 200
        data = response.json()
        valores = [item["valor"] for item in data["items"]]
        assert valores == sorted(valores)

    async def test_Should_DefaultSortByFechaDesc_When_NoSortParams(
        self,
        client: AsyncClient,
    ) -> None:
        """Orden por defecto: fecha descendente."""
        # Act ------------------------------------------------------------
        response = await client.get("/")

        # Assert ----------------------------------------------------------
        assert response.status_code == 200
        data = response.json()
        fechas = [item["fecha"] for item in data["items"] if item["fecha"]]
        assert fechas == sorted(fechas, reverse=True)


# ============================================================
# GetTransaction — GET /{id}
# ============================================================


class TestGetTransaction:
    """Escenarios para GET /{id} — detalle de transaccion."""

    TRANS_ID = uuid.UUID("d0000000-0000-0000-0000-000000000001")

    async def test_Should_ReturnTransactionDetail_When_ValidId(
        self,
        client: AsyncClient,
    ) -> None:
        """Retorna el detalle completo de una transaccion existente."""
        # Act ------------------------------------------------------------
        response = await client.get(f"/{self.TRANS_ID}")

        # Assert ----------------------------------------------------------
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(self.TRANS_ID)
        assert data["comercio"] == "RESTAURANTE DON PEPE"
        assert data["comercio_traducido"] == "Don Pepe"
        assert data["valor"] == 45.5
        assert data["categoria_id"] == str(TEST_CATEGORIA_ID)
        assert data["confidence"] == 95.0

    async def test_Should_Return404_When_TransactionNotFound(
        self,
        client: AsyncClient,
    ) -> None:
        """Retorna 404 cuando la transaccion no existe."""
        # Act ------------------------------------------------------------
        fake_id = uuid.uuid4()
        response = await client.get(f"/{fake_id}")

        # Assert ----------------------------------------------------------
        assert response.status_code == 404
        assert "Transaccion no encontrada" in response.json()["detail"]


# ============================================================
# UpdateTransactionCategory — PATCH /{id}/category
# ============================================================


class TestUpdateTransactionCategory:
    """Escenarios para PATCH /{id}/category — cambiar categoria."""

    TRANS_ID = uuid.UUID("d0000000-0000-0000-0000-000000000002")

    async def test_Should_UpdateCategory_When_ValidData(
        self,
        client: AsyncClient,
    ) -> None:
        """Cambia la categoria de una transaccion exitosamente."""
        # Act ------------------------------------------------------------
        response = await client.patch(
            f"/{self.TRANS_ID}/category",
            json={"category_id": str(TEST_CATEGORIA_ID)},
        )

        # Assert ----------------------------------------------------------
        assert response.status_code == 200
        data = response.json()
        assert data["transaccion_id"] == str(self.TRANS_ID)
        assert data["categoria_id"] == str(TEST_CATEGORIA_ID)
        assert data["confidence"] == 100.0

        # Verify — la transaccion ahora tiene la nueva categoria
        get_resp = await client.get(f"/{self.TRANS_ID}")
        assert get_resp.json()["categoria_id"] == str(TEST_CATEGORIA_ID)

    async def test_Should_Return400_When_CategoryIdMissing(
        self,
        client: AsyncClient,
    ) -> None:
        """Retorna 400 cuando falta category_id en el body."""
        # Act ------------------------------------------------------------
        response = await client.patch(
            f"/{self.TRANS_ID}/category",
            json={},
        )

        # Assert ----------------------------------------------------------
        assert response.status_code == 400
        assert "category_id" in response.json()["detail"].lower()

    async def test_Should_Return404_When_TransactionNotFound(
        self,
        client: AsyncClient,
    ) -> None:
        """Retorna 404 cuando la transaccion no existe."""
        # Act ------------------------------------------------------------
        fake_id = uuid.uuid4()
        response = await client.patch(
            f"/{fake_id}/category",
            json={"category_id": str(TEST_CATEGORIA_ID)},
        )

        # Assert ----------------------------------------------------------
        assert response.status_code == 404


# ============================================================
# BulkUpdateCategory — PATCH /bulk/category
# ============================================================


class TestBulkUpdateCategory:
    """Escenarios para PATCH /bulk/category — clasificacion masiva."""

    TRANS_IDS = [
        uuid.UUID("d0000000-0000-0000-0000-000000000003"),
        uuid.UUID("d0000000-0000-0000-0000-000000000005"),
    ]

    async def test_Should_UpdateMultipleCategories_When_ValidData(
        self,
        client: AsyncClient,
    ) -> None:
        """Actualiza la categoria de multiples transacciones a la vez."""
        # Act ------------------------------------------------------------
        response = await client.patch(
            "/bulk/category",
            json={
                "transaction_ids": [str(tid) for tid in self.TRANS_IDS],
                "category_id": str(TEST_CATEGORIA_ALT_ID),
            },
        )

        # Assert ----------------------------------------------------------
        assert response.status_code == 200
        data = response.json()
        assert data["updated_count"] == 2

        # Verify — ambas transacciones ahora tienen la nueva categoria
        for tid in self.TRANS_IDS:
            get_resp = await client.get(f"/{tid}")
            assert get_resp.json()["categoria_id"] == str(TEST_CATEGORIA_ALT_ID)

    async def test_Should_Return400_When_MissingTransactionIds(
        self,
        client: AsyncClient,
    ) -> None:
        """Retorna 400 cuando faltan los transaction_ids."""
        # Act ------------------------------------------------------------
        response = await client.patch(
            "/bulk/category",
            json={"category_id": str(TEST_CATEGORIA_ID)},
        )

        # Assert ----------------------------------------------------------
        assert response.status_code == 400
        assert "transaction_ids" in response.json()["detail"].lower()

    async def test_Should_Return400_When_MissingCategoryId(
        self,
        client: AsyncClient,
    ) -> None:
        """Retorna 400 cuando falta el category_id."""
        # Act ------------------------------------------------------------
        response = await client.patch(
            "/bulk/category",
            json={"transaction_ids": [str(uuid.uuid4())]},
        )

        # Assert ----------------------------------------------------------
        assert response.status_code == 400


# ============================================================
# GetUnclassified — GET /unclassified/list
# ============================================================


class TestGetUnclassified:
    """Escenarios para GET /unclassified/list — transacciones con confianza baja."""

    async def test_Should_ReturnUnclassifiedTransactions_When_LowConfidence(
        self,
        client: AsyncClient,
    ) -> None:
        """Retorna transacciones con confianza < 70% o sin clasificar."""
        # Act ------------------------------------------------------------
        response = await client.get(f"/unclassified/list?extract_id={TEST_EXTRACTO_ID}")

        # Assert ----------------------------------------------------------
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "count" in data
        assert data["count"] >= 1
        # Transaccion #3 tiene confidence=55 y #5 tiene 65
        for item in data["items"]:
            assert "comercio" in item
            assert "valor" in item


# ============================================================
# SearchTransactions — GET /search
# ============================================================


class TestSearchTransactions:
    """Escenarios para GET /search — busqueda full-text por comercio."""

    async def test_Should_ReturnMatchingTransactions_When_SearchTerm(
        self,
        client: AsyncClient,
    ) -> None:
        """Busca transacciones que coincidan con el termino de busqueda."""
        # Act ------------------------------------------------------------
        response = await client.get("/search?q=didi")

        # Assert ----------------------------------------------------------
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1
        item = data["items"][0]
        assert "didi" in item["comercio"].lower()

    async def test_Should_ReturnEmpty_When_NoMatch(
        self,
        client: AsyncClient,
    ) -> None:
        """Retorna lista vacia cuando no hay coincidencias."""
        # Act ------------------------------------------------------------
        response = await client.get("/search?q=xyznoexiste")

        # Assert ----------------------------------------------------------
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0

    async def test_Should_Return400_When_SearchTermTooShort(
        self,
        client: AsyncClient,
    ) -> None:
        """Retorna 422 cuando el termino es demasiado corto (< 2 chars)."""
        # Act ------------------------------------------------------------
        response = await client.get("/search?q=a")

        # Assert ----------------------------------------------------------
        assert response.status_code == 422
