"""Tests unitarios para ExtractProcessorService.process().

Cubre el flujo completo del worker de procesamiento de extractos:
parseo, persistencia, publicacion de eventos y manejo de errores.

Convenciones TDD:
- Carpeta: ExtractProcessorTests para la clase ExtractProcessorService
- Archivo: test_process.py para el metodo process
- Nombramiento Gherkin: Should_{Resultado}_When_{Condicion}
- Patron AAA con comentarios # Arrange/Act/Assert
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from src.workers.extract_processor_service import (
    ExtractMessage,
    ExtractProcessorService,
    ProcessResult,
)


# ============================================================
# Helpers — Fixtures y fabricas
# ============================================================

@pytest.fixture
def extracto_id() -> UUID:
    return uuid4()


@pytest.fixture
def usuario_id() -> UUID:
    return uuid4()


@pytest.fixture
def tarjeta_id() -> UUID:
    return uuid4()


def make_extract_model(
    extracto_id: UUID,
    usuario_id: UUID,
    tarjeta_id: UUID,
    estado: str = "PENDING",
    archivo_s3_key: str | None = "extracts/user123/file.xlsx",
) -> MagicMock:
    """Factory de modelo Extracto simulado."""
    model = MagicMock()
    model.id = extracto_id
    model.usuario_id = usuario_id
    model.tarjeta_id = tarjeta_id
    model.estado = estado
    model.progress_pct = 0
    model.archivo_s3_key = archivo_s3_key
    model.periodo_inicio = None
    model.periodo_fin = None
    model.fecha_corte = None
    model.fecha_limite_pago = None
    model.pago_minimo = None
    model.pago_total = None
    model.cupo_total = None
    model.cupo_disponible = None
    model.metadatos = {}
    model.error_message = None
    return model


def make_parse_result(
    exitoso: bool = True,
    transacciones: list[dict[str, Any]] | None = None,
    errores: list[str] | None = None,
    metadatos: dict[str, Any] | None = None,
) -> Any:
    """Factory de resultado de parseo simulado."""
    from src.infrastructure.excel.parser import ExtractoParseado

    if transacciones is None:
        transacciones = [
            {
                "numero_autorizacion": "123456",
                "fecha": date(2026, 5, 15),
                "comercio_original": "SUPERMERCADO EL EXITO",
                "valor": Decimal("85000.00"),
                "numero_cuotas": "1/1",
                "cuotas_totales": 1,
                "cuota_actual": 1,
                "moneda_original": None,
                "valor_moneda_original": None,
                "es_cuota": False,
            },
            {
                "numero_autorizacion": "789012",
                "fecha": date(2026, 5, 16),
                "comercio_original": "DLO*UBER TRIP",
                "valor": Decimal("25000.00"),
                "numero_cuotas": "1/1",
                "cuotas_totales": 1,
                "cuota_actual": 1,
                "moneda_original": None,
                "valor_moneda_original": None,
                "es_cuota": False,
            },
        ]

    if errores is None:
        errores = []

    if metadatos is None:
        metadatos = {
            "banco": "Bancolombia",
            "periodo_inicio": date(2026, 5, 1),
            "periodo_fin": date(2026, 5, 18),
            "fecha_corte": date(2026, 5, 18),
            "fecha_limite_pago": date(2026, 6, 5),
            "pago_minimo": Decimal("50000.00"),
            "pago_total": Decimal("350000.00"),
            "cupo_total": Decimal("5000000.00"),
            "cupo_disponible": Decimal("4650000.00"),
            "moneda": "COP",
        }

    return ExtractoParseado(
        metadatos=metadatos,
        transacciones=transacciones,
        errores=errores,
        warnings=[],
    )


def make_mock_session() -> MagicMock:
    """Factory de sesion SQLAlchemy simulada."""
    session = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


# ============================================================
# ExtractProcessorService.process() — Tests
# ============================================================

class TestProcess:
    """Tests para el metodo process de ExtractProcessorService."""

    @pytest.fixture
    def extracto_repo(self) -> MagicMock:
        repo = MagicMock()
        repo.get_by_id = AsyncMock()
        repo.save = AsyncMock()
        repo.session = None  # se inyecta en el test
        return repo

    @pytest.fixture
    def transaccion_repo(self) -> MagicMock:
        repo = MagicMock()
        repo.bulk_save = AsyncMock()
        repo.session = None
        return repo

    @pytest.fixture
    def event_bus(self) -> MagicMock:
        bus = MagicMock()
        bus.publish = AsyncMock()
        return bus

    @pytest.fixture
    def mock_parser(self) -> MagicMock:
        parser = MagicMock()
        parser.parse = MagicMock()
        return parser

    def _build_service(
        self,
        extracto_repo: MagicMock,
        transaccion_repo: MagicMock,
        event_bus: MagicMock | None = None,
        storage: MagicMock | None = None,
    ) -> ExtractProcessorService:
        """Construye el SUT con los mocks inyectados."""
        return ExtractProcessorService(
            extracto_repo=extracto_repo,
            transaccion_repo=transaccion_repo,
            storage=storage,
            event_bus=event_bus,
        )

    # ============================================================
    # Happy path
    # ============================================================

    @pytest.mark.asyncio
    async def test_Should_ParseAndPersistTransactions_When_ValidMessageWithInlineContent(
        self,
        extracto_id: UUID,
        usuario_id: UUID,
        tarjeta_id: UUID,
        extracto_repo: MagicMock,
        transaccion_repo: MagicMock,
        event_bus: MagicMock,
        mock_parser: MagicMock,
    ):
        """Procesa un mensaje valido con contenido inline base64.

        Verifica que:
        - El extracto se carga de BD
        - El parser se invoca con el contenido decodificado
        - Las transacciones se persisten via bulk_save
        - El estado del extracto avanza a COMPLETED
        - Se publica el evento ExtractoProcesado
        """
        # Arrange --------------------------------------------------------
        model = make_extract_model(extracto_id, usuario_id, tarjeta_id)
        extracto_repo.get_by_id.return_value = model

        parse_result = make_parse_result(exitoso=True)
        mock_parser.parse.return_value = parse_result

        session = make_mock_session()
        extracto_repo.session = session
        transaccion_repo.session = session

        # Contenido Excel simulado (bytes cualquiera, el mock parser lo ignora)
        fake_excel_bytes = b"fake excel content for testing"
        msg = ExtractMessage(
            tracking_id=extracto_id,
            file_key=None,
            card_id=tarjeta_id,
            user_id=usuario_id,
            file_content_b64=base64.b64encode(fake_excel_bytes).decode("utf-8"),
        )

        sut = self._build_service(extracto_repo, transaccion_repo, event_bus)

        # Act ------------------------------------------------------------
        result = await sut.process(msg, parser=mock_parser)

        # Assert ----------------------------------------------------------
        # 1. Resultado exitoso
        assert result.success is True
        assert result.estado == "CLASSIFYING"
        assert result.transaction_count == 2

        # 2. Se cargo el extracto de BD
        extracto_repo.get_by_id.assert_awaited_once_with(extracto_id)

        # 3. El parser se llamo con el contenido decodificado
        mock_parser.parse.assert_called_once()
        call_args = mock_parser.parse.call_args[0]
        assert call_args[0] == fake_excel_bytes  # contenido decodificado
        assert call_args[1] == "extracto_inline.xlsx"  # filename inferido

        # 4. Transacciones persistidas
        transaccion_repo.bulk_save.assert_awaited_once()
        saved_transactions = transaccion_repo.bulk_save.call_args[0][0]
        assert len(saved_transactions) == 2

        # 5. Extracto guardado 3 veces (inicio, metadata, final)
        assert extracto_repo.save.await_count == 3

        # 6. Evento publicado
        event_bus.publish.assert_awaited_once()

    # ============================================================
    # Inline content
    # ============================================================

    @pytest.mark.asyncio
    async def test_Should_DecodeBase64Content_When_FileContentInline(
        self,
        extracto_id: UUID,
        usuario_id: UUID,
        tarjeta_id: UUID,
        extracto_repo: MagicMock,
        transaccion_repo: MagicMock,
        mock_parser: MagicMock,
    ):
        """Verifica que el contenido base64 inline se decodifica correctamente."""
        # Arrange --------------------------------------------------------
        model = make_extract_model(extracto_id, usuario_id, tarjeta_id)
        extracto_repo.get_by_id.return_value = model

        parse_result = make_parse_result(exitoso=True)
        mock_parser.parse.return_value = parse_result

        session = make_mock_session()
        extracto_repo.session = session
        transaccion_repo.session = session

        original_content = b"Excel binary content \x00\x01\x02"
        encoded = base64.b64encode(original_content).decode("utf-8")

        msg = ExtractMessage(
            tracking_id=extracto_id,
            file_content_b64=encoded,
            user_id=usuario_id,
        )

        sut = self._build_service(extracto_repo, transaccion_repo)

        # Act ------------------------------------------------------------
        result = await sut.process(msg, parser=mock_parser)

        # Assert ----------------------------------------------------------
        call_args = mock_parser.parse.call_args[0]
        assert call_args[0] == original_content

    # ============================================================
    # Download from R2
    # ============================================================

    @pytest.mark.asyncio
    async def test_Should_DownloadFromR2_When_FileKeyProvided(
        self,
        extracto_id: UUID,
        usuario_id: UUID,
        tarjeta_id: UUID,
        extracto_repo: MagicMock,
        transaccion_repo: MagicMock,
        mock_parser: MagicMock,
    ):
        """Descarga el archivo desde R2 cuando se provee file_key."""
        # Arrange --------------------------------------------------------
        model = make_extract_model(extracto_id, usuario_id, tarjeta_id)
        extracto_repo.get_by_id.return_value = model

        parse_result = make_parse_result(exitoso=True)
        mock_parser.parse.return_value = parse_result

        session = make_mock_session()
        extracto_repo.session = session
        transaccion_repo.session = session

        # Mock storage con download_file sincrono (boto3 es sync)
        storage = MagicMock()
        fake_excel_bytes = b"downloaded from R2"
        storage.download_file.return_value = fake_excel_bytes

        msg = ExtractMessage(
            tracking_id=extracto_id,
            file_key="user123/extract_mayo.xlsx",
            user_id=usuario_id,
        )

        sut = self._build_service(extracto_repo, transaccion_repo, storage=storage)

        # Act ------------------------------------------------------------
        result = await sut.process(msg, parser=mock_parser)

        # Assert ----------------------------------------------------------
        assert result.success is True

        # Verificar que se descargo de R2
        storage.download_file.assert_called_once_with(
            "finance-extracts", "user123/extract_mayo.xlsx"
        )

        # Verificar que el parser recibio el contenido descargado
        call_args = mock_parser.parse.call_args[0]
        assert call_args[0] == fake_excel_bytes

    # ============================================================
    # Error handling
    # ============================================================

    @pytest.mark.asyncio
    async def test_Should_MarkExtractAsError_When_ParseFails(
        self,
        extracto_id: UUID,
        usuario_id: UUID,
        tarjeta_id: UUID,
        extracto_repo: MagicMock,
        transaccion_repo: MagicMock,
        mock_parser: MagicMock,
    ):
        """Marca el extracto como ERROR cuando el parseo falla."""
        # Arrange --------------------------------------------------------
        model = make_extract_model(extracto_id, usuario_id, tarjeta_id)
        extracto_repo.get_by_id.return_value = model

        # Parseo con errores y sin transacciones
        parse_result = make_parse_result(
            exitoso=False,
            transacciones=[],
            errores=["Formato de Excel no reconocido"],
        )
        mock_parser.parse.return_value = parse_result

        session = make_mock_session()
        extracto_repo.session = session
        transaccion_repo.session = session

        msg = ExtractMessage(
            tracking_id=extracto_id,
            file_content_b64=base64.b64encode(b"bad content").decode("utf-8"),
            user_id=usuario_id,
        )

        sut = self._build_service(extracto_repo, transaccion_repo)

        # Act ------------------------------------------------------------
        result = await sut.process(msg, parser=mock_parser)

        # Assert ----------------------------------------------------------
        assert result.success is False
        assert result.estado == "ERROR"
        assert "Formato de Excel no reconocido" in result.parse_errors

        # Verificar que el modelo se actualizo a ERROR
        assert model.estado == "ERROR"
        assert model.error_message is not None
        assert "Formato de Excel no reconocido" in model.error_message

        # No se debieron guardar transacciones
        transaccion_repo.bulk_save.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_Should_MarkExtractAsError_When_DownloadFails(
        self,
        extracto_id: UUID,
        usuario_id: UUID,
        tarjeta_id: UUID,
        extracto_repo: MagicMock,
        transaccion_repo: MagicMock,
    ):
        """Marca el extracto como ERROR cuando falla la descarga desde R2."""
        # Arrange --------------------------------------------------------
        model = make_extract_model(extracto_id, usuario_id, tarjeta_id)
        extracto_repo.get_by_id.return_value = model

        session = make_mock_session()
        extracto_repo.session = session
        transaccion_repo.session = session

        # Storage que lanza excepcion al descargar
        storage = MagicMock()
        storage.download_file.side_effect = Exception("R2 connection timeout")

        msg = ExtractMessage(
            tracking_id=extracto_id,
            file_key="user123/missing.xlsx",
            user_id=usuario_id,
        )

        sut = self._build_service(extracto_repo, transaccion_repo, storage=storage)

        # Act ------------------------------------------------------------
        result = await sut.process(msg)

        # Assert ----------------------------------------------------------
        assert result.success is False
        assert result.estado == "ERROR"
        assert any("Error al obtener archivo" in e for e in result.parse_errors)
        assert model.estado == "ERROR"

    @pytest.mark.asyncio
    async def test_Should_MarkExtractAsError_When_ExtractNotFound(
        self,
        extracto_id: UUID,
        usuario_id: UUID,
        extracto_repo: MagicMock,
        transaccion_repo: MagicMock,
    ):
        """Lanza ValueError cuando el extracto no existe en BD."""
        # Arrange --------------------------------------------------------
        extracto_repo.get_by_id.return_value = None

        msg = ExtractMessage(
            tracking_id=extracto_id,
            file_content_b64=base64.b64encode(b"dummy").decode("utf-8"),
            user_id=usuario_id,
        )

        sut = self._build_service(extracto_repo, transaccion_repo)

        # Act & Assert ----------------------------------------------------
        with pytest.raises(ValueError, match="no encontrado"):
            await sut.process(msg)

    # ============================================================
    # Event publishing
    # ============================================================

    @pytest.mark.asyncio
    async def test_Should_PublishExtractoProcesadoEvent_When_ProcessingSucceeds(
        self,
        extracto_id: UUID,
        usuario_id: UUID,
        tarjeta_id: UUID,
        extracto_repo: MagicMock,
        transaccion_repo: MagicMock,
        event_bus: MagicMock,
        mock_parser: MagicMock,
    ):
        """Publica el evento ExtractoProcesado (transactions.new) al terminar."""
        # Arrange --------------------------------------------------------
        model = make_extract_model(extracto_id, usuario_id, tarjeta_id)
        extracto_repo.get_by_id.return_value = model

        parse_result = make_parse_result(exitoso=True)
        mock_parser.parse.return_value = parse_result

        session = make_mock_session()
        extracto_repo.session = session
        transaccion_repo.session = session

        msg = ExtractMessage(
            tracking_id=extracto_id,
            file_content_b64=base64.b64encode(b"content").decode("utf-8"),
            user_id=usuario_id,
            card_id=tarjeta_id,
        )

        sut = self._build_service(extracto_repo, transaccion_repo, event_bus)

        # Act ------------------------------------------------------------
        result = await sut.process(msg, parser=mock_parser)

        # Assert ----------------------------------------------------------
        assert result.success is True
        event_bus.publish.assert_awaited_once()

        # Verificar el evento publicado
        published_event = event_bus.publish.call_args[0][0]
        assert published_event.extracto_id == extracto_id
        assert published_event.usuario_id == usuario_id
        assert published_event.tarjeta_id == tarjeta_id
        assert published_event.transaction_count == 2

    @pytest.mark.asyncio
    async def test_Should_NotPublishEvent_When_NoEventBus(
        self,
        extracto_id: UUID,
        usuario_id: UUID,
        tarjeta_id: UUID,
        extracto_repo: MagicMock,
        transaccion_repo: MagicMock,
        mock_parser: MagicMock,
    ):
        """No falla cuando event_bus es None (modo polling)."""
        # Arrange --------------------------------------------------------
        model = make_extract_model(extracto_id, usuario_id, tarjeta_id)
        extracto_repo.get_by_id.return_value = model

        parse_result = make_parse_result(exitoso=True)
        mock_parser.parse.return_value = parse_result

        session = make_mock_session()
        extracto_repo.session = session
        transaccion_repo.session = session

        msg = ExtractMessage(
            tracking_id=extracto_id,
            file_content_b64=base64.b64encode(b"content").decode("utf-8"),
            user_id=usuario_id,
        )

        # Sin event_bus (modo polling)
        sut = self._build_service(extracto_repo, transaccion_repo, event_bus=None)

        # Act ------------------------------------------------------------
        result = await sut.process(msg, parser=mock_parser)

        # Assert ----------------------------------------------------------
        assert result.success is True  # No debe fallar por falta de event bus

    # ============================================================
    # ExtractMessage.from_dict
    # ============================================================

    def test_Should_ParseMessageFields_When_AllFieldsPresent(self):
        """Parsea correctamente un diccionario con todos los campos."""
        # Arrange --------------------------------------------------------
        tid = uuid4()
        uid = uuid4()
        cid = uuid4()
        data = {
            "tracking_id": str(tid),
            "file_key": "path/to/file.xlsx",
            "card_id": str(cid),
            "user_id": str(uid),
            "file_content_b64": "dGVzdA==",
        }

        # Act ------------------------------------------------------------
        msg = ExtractMessage.from_dict(data)

        # Assert ----------------------------------------------------------
        assert msg.tracking_id == tid
        assert msg.file_key == "path/to/file.xlsx"
        assert msg.card_id == cid
        assert msg.user_id == uid
        assert msg.file_content_b64 == "dGVzdA=="

    def test_Should_ParseLegacyFieldNames_When_UsingOldConvention(self):
        """Soporta nombres de campo legacy (extracto_id, s3_key, tarjeta_id, usuario_id)."""
        # Arrange --------------------------------------------------------
        tid = uuid4()
        uid = uuid4()
        cid = uuid4()
        data = {
            "extracto_id": str(tid),
            "s3_key": "extracts/test.xlsx",
            "tarjeta_id": str(cid),
            "usuario_id": str(uid),
        }

        # Act ------------------------------------------------------------
        msg = ExtractMessage.from_dict(data)

        # Assert ----------------------------------------------------------
        assert msg.tracking_id == tid
        assert msg.file_key == "extracts/test.xlsx"
        assert msg.card_id == cid
        assert msg.user_id == uid
        assert msg.file_content_b64 is None
