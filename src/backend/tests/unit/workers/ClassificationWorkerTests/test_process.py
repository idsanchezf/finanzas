"""Tests para el worker de clasificacion de transacciones.

Verifica que ClassificationService:
- Clasifique transacciones usando el clasificador de reglas
- Persista los resultados en BD
- Marque transacciones con baja confianza para revision
- Actualice el progreso del extracto

Convencion TDD:
- Carpeta: ClassificationWorkerTests/
- Archivo: test_process.py (metodo process_extract)
"""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.domain.entities.categoria import Categoria
from src.infrastructure.excel.clasificador_reglas import ClasificadorReglas
from src.infrastructure.persistence.models import (
    CategoriaModel,
    ExtractoModel,
    TransaccionModel,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_categoria_model(cat: Categoria) -> CategoriaModel:
    """Convierte entidad Categoria a modelo ORM."""
    return CategoriaModel(
        id=cat.id,
        nombre=cat.nombre,
        icono=cat.icono,
        color=cat.color,
        parent_id=cat.parent_id,
        es_predefinida=cat.es_predefinida,
        usuario_id=cat.usuario_id,
        palabras_clave=cat.palabras_clave,
    )


def _make_txn_model(
    extracto_id: UUID,
    usuario_id: UUID,
    comercio: str,
    valor: Decimal = Decimal("35000.00"),
) -> TransaccionModel:
    """Crea un modelo de transaccion sin clasificar."""
    return TransaccionModel(
        id=uuid4(),
        extracto_id=extracto_id,
        usuario_id=usuario_id,
        fecha=None,
        comercio_original=comercio,
        valor=valor,
        categoria_id=None,
        confidence=None,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def categorias():
    """14 categorias predefinidas con sus palabras clave."""
    return Categoria.precargadas()


@pytest.fixture
def categoria_models(categorias):
    """Convierte entidades Categoria a modelos ORM."""
    return [_make_categoria_model(c) for c in categorias]


@pytest.fixture
def extracto_id():
    return uuid4()


@pytest.fixture
def usuario_id():
    return uuid4()


@pytest.fixture
def transacciones_sin_clasificar(extracto_id, usuario_id):
    """Transacciones de prueba sin categoria asignada."""
    return [
        _make_txn_model(extracto_id, usuario_id, "DLO*DIDI FOOD CO PAYIN"),
        _make_txn_model(extracto_id, usuario_id, "UBER *TRIP HELP.UBER.COM", Decimal("18500.00")),
        _make_txn_model(extracto_id, usuario_id, "ABCXYZ_MNOPQR_123456_NOMATCH", Decimal("50000.00")),
    ]


@pytest.fixture
def extracto_model(extracto_id, usuario_id):
    return ExtractoModel(
        id=extracto_id,
        tarjeta_id=uuid4(),
        usuario_id=usuario_id,
        estado="PARSING",
    )


@pytest.fixture
def mock_session():
    """Mock de AsyncSession de SQLAlchemy."""
    session = MagicMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    session.rollback = AsyncMock()
    session.execute = AsyncMock()
    session.merge = AsyncMock()
    session.close = AsyncMock()
    return session


# ===========================================================================
# Test del metodo process_extract
# ===========================================================================
class TestProcessExtract:
    """Verifica la clasificacion de transacciones de un extracto."""

    @pytest.fixture
    def sut(self):
        """SUT: ClassificationService con clasificador real y repos mockeados."""
        from src.workers.classification_service import ClassificationService

        # Crear un session factory mock que retorne el mock_session
        mock_sf = MagicMock(spec=async_sessionmaker)
        mock_sf.return_value.__aenter__ = AsyncMock(return_value=MagicMock(spec=AsyncSession))
        mock_sf.return_value.__aexit__ = AsyncMock(return_value=None)

        service = ClassificationService(
            session_factory=mock_sf,
            clasificador=ClasificadorReglas(),
        )
        return service

    @pytest.fixture
    def mock_repos(self, monkeypatch, mock_session):
        """Mockea los repositorios para que usen mock_session y retornen datos de prueba."""
        from src.infrastructure.persistence.repositories import categoria_repo as cr_mod
        from src.infrastructure.persistence.repositories import extracto_repo as er_mod
        from src.infrastructure.persistence.repositories import transaccion_repo as tr_mod

        # Guardamos referencias para que los tests las configuren
        mocks = {
            "categoria_get_all": AsyncMock(),
            "transaccion_get_by_id": AsyncMock(),
            "transaccion_save": AsyncMock(),
            "extracto_get_by_id": AsyncMock(),
            "extracto_save": AsyncMock(),
        }

        # Patch CategoriaRepository
        original_init = cr_mod.CategoriaRepository.__init__

        def _cr_init(self_repo, session):
            original_init(self_repo, session)
            self_repo.get_all = mocks["categoria_get_all"]

        monkeypatch.setattr(cr_mod.CategoriaRepository, "__init__", _cr_init)

        # Patch TransaccionRepository
        original_txn_init = tr_mod.TransaccionRepository.__init__

        def _tr_init(self_repo, session):
            original_txn_init(self_repo, session)
            self_repo.get_by_id = mocks["transaccion_get_by_id"]
            self_repo.save = mocks["transaccion_save"]

        monkeypatch.setattr(tr_mod.TransaccionRepository, "__init__", _tr_init)

        # Patch ExtractoRepository
        original_ext_init = er_mod.ExtractoRepository.__init__

        def _er_init(self_repo, session):
            original_ext_init(self_repo, session)
            self_repo.get_by_id = mocks["extracto_get_by_id"]
            self_repo.save = mocks["extracto_save"]

        monkeypatch.setattr(er_mod.ExtractoRepository, "__init__", _er_init)

        return mocks

    # ------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_Should_ClassifyTransactions_When_ValidMerchants(
        self, sut, extracto_id, usuario_id,
        transacciones_sin_clasificar, categoria_models, extracto_model,
        mock_repos,
    ):
        """Happy path: clasifica correctamente usando el clasificador de reglas."""
        # Arrange --------------------------------------------------------
        # Configurar mocks para este test
        txn_list = transacciones_sin_clasificar

        # get_by_id: retorna la transaccion segun su indice
        async def _get_by_id(txn_id):
            for t in txn_list:
                if t.id == txn_id:
                    return t
            return None

        mock_repos["categoria_get_all"].return_value = categoria_models
        mock_repos["transaccion_get_by_id"].side_effect = _get_by_id
        mock_repos["extracto_get_by_id"].return_value = extracto_model

        # Act ------------------------------------------------------------
        result = await sut.process_extract(
            extract_id=extracto_id,
            transaction_ids=[t.id for t in txn_list],
            user_id=usuario_id,
        )

        # Assert ----------------------------------------------------------
        assert len(result) == 3

        # DIDI debe ser Alimentacion (confianza >= 55)
        didi_result = next(r for r in result if r["transaction_id"] == txn_list[0].id)
        assert didi_result["category_id"] is not None
        assert didi_result["confidence"] >= 50

        # UBER debe ser Transporte
        uber_result = next(r for r in result if r["transaction_id"] == txn_list[1].id)
        assert uber_result["category_id"] is not None
        assert uber_result["confidence"] >= 50

        # Tercera transaccion (no match) no debe clasificarse
        unknown_result = next(r for r in result if r["transaction_id"] == txn_list[2].id)
        assert unknown_result["category_id"] is None
        assert unknown_result["confidence"] == Decimal("0.00")

        # Verificar que se persistio
        assert mock_repos["transaccion_save"].call_count == 3

    # ------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_Should_MarkLowConfidence_When_BelowThreshold(
        self, sut, extracto_id, usuario_id,
        categoria_models, extracto_model,
        mock_repos,
    ):
        """Transacciones con confianza baja (<70%) se registran como tal."""
        # Arrange --------------------------------------------------------
        # Comercio que matchea solo 1 keyword generica (baja especificidad)
        # "pago" es keyword de "Otros" - solo 1 match, sin bonus
        weird_txn = _make_txn_model(extracto_id, usuario_id, "PAGO ABCDEF")

        async def _get_by_id(txn_id):
            return weird_txn if txn_id == weird_txn.id else None

        mock_repos["categoria_get_all"].return_value = categoria_models
        mock_repos["transaccion_get_by_id"].side_effect = _get_by_id
        mock_repos["extracto_get_by_id"].return_value = extracto_model

        # Act ------------------------------------------------------------
        result = await sut.process_extract(
            extract_id=extracto_id,
            transaction_ids=[weird_txn.id],
            user_id=usuario_id,
        )

        # Assert ----------------------------------------------------------
        assert len(result) == 1
        r = result[0]
        # Debe clasificarse (matchea "pago" en Otros, solo 1 keyword)
        assert r["category_id"] is not None
        # Confianza debe ser baja (<70) porque solo matchea 1 keyword generica
        assert r["confidence"] < 70, f"Expected low confidence, got {r['confidence']}"
        assert sut.is_low_confidence(r["confidence"]) is True

    # ------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_Should_NotClassify_When_NoMatch(
        self, sut, extracto_id, usuario_id,
        categoria_models, extracto_model,
        mock_repos,
    ):
        """Comercios sin match no deben clasificarse (categoria_id=None)."""
        # Arrange --------------------------------------------------------
        no_match_txn = _make_txn_model(extracto_id, usuario_id, "XYZZY_NOMATCH_ABCDEFGH")

        async def _get_by_id(txn_id):
            return no_match_txn if txn_id == no_match_txn.id else None

        mock_repos["categoria_get_all"].return_value = categoria_models
        mock_repos["transaccion_get_by_id"].side_effect = _get_by_id
        mock_repos["extracto_get_by_id"].return_value = extracto_model

        # Act ------------------------------------------------------------
        result = await sut.process_extract(
            extract_id=extracto_id,
            transaction_ids=[no_match_txn.id],
            user_id=usuario_id,
        )

        # Assert ----------------------------------------------------------
        assert len(result) == 1
        assert result[0]["category_id"] is None
        assert result[0]["confidence"] == Decimal("0.00")
        assert result[0]["source"] == "none"

    # ------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_Should_UpdateExtractoStatus_When_Processing(
        self, sut, extracto_id, usuario_id,
        transacciones_sin_clasificar, categoria_models, extracto_model,
        mock_repos,
    ):
        """El extracto debe pasar a CLASSIFYING y luego a COMPLETED."""
        # Arrange --------------------------------------------------------
        txn_list = transacciones_sin_clasificar

        async def _get_by_id(txn_id):
            for t in txn_list:
                if t.id == txn_id:
                    return t
            return None

        mock_repos["categoria_get_all"].return_value = categoria_models
        mock_repos["transaccion_get_by_id"].side_effect = _get_by_id
        mock_repos["extracto_get_by_id"].return_value = extracto_model

        # Capturar las llamadas a extracto_save (guardar copia del estado en ese momento)
        saved_extractos = []

        async def _capture_save(extracto):
            # Guardar una copia del estado en este instante (evita mutacion posterior)
            saved_extractos.append({
                "estado": extracto.estado,
                "progress_pct": extracto.progress_pct,
            })
            return extracto

        mock_repos["extracto_save"].side_effect = _capture_save

        # Act ------------------------------------------------------------
        await sut.process_extract(
            extract_id=extracto_id,
            transaction_ids=[t.id for t in txn_list],
            user_id=usuario_id,
        )

        # Assert ----------------------------------------------------------
        # Debe haberse guardado el extracto al menos 2 veces (CLASSIFYING + COMPLETED)
        assert len(saved_extractos) >= 2, f"Expected >=2 extracts saves, got {len(saved_extractos)}"

        # Primer save: estado CLASSIFYING
        assert saved_extractos[0]["estado"] == "CLASSIFYING", \
            f"First save should be CLASSIFYING, got {saved_extractos[0]}"

        # Ultimo save: estado COMPLETED
        assert saved_extractos[-1]["estado"] == "COMPLETED"
        assert saved_extractos[-1]["progress_pct"] == 100

    # ------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_Should_HandleEmptyTransactionList_When_NoTransactions(
        self, sut, extracto_id, usuario_id,
        categoria_models, extracto_model,
        mock_repos,
    ):
        """No debe fallar si la lista de transacciones esta vacia."""
        # Arrange --------------------------------------------------------
        mock_repos["categoria_get_all"].return_value = categoria_models
        mock_repos["extracto_get_by_id"].return_value = extracto_model

        # Act ------------------------------------------------------------
        result = await sut.process_extract(
            extract_id=extracto_id,
            transaction_ids=[],
            user_id=usuario_id,
        )

        # Assert ----------------------------------------------------------
        assert result == []
        # Save no deberia llamarse para transacciones
        mock_repos["transaccion_save"].assert_not_called()

    # ------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_Should_ReturnEmpty_When_ExtractNotFound(
        self, sut, extracto_id, usuario_id,
        mock_repos,
    ):
        """Retorna lista vacia si el extracto no existe."""
        # Arrange --------------------------------------------------------
        mock_repos["extracto_get_by_id"].return_value = None

        # Act ------------------------------------------------------------
        result = await sut.process_extract(
            extract_id=extracto_id,
            transaction_ids=[uuid4()],
            user_id=usuario_id,
        )

        # Assert ----------------------------------------------------------
        assert result == []
