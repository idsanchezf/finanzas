"""Tests para handle_cargar_extracto — Pre-flight check de duplicados (feat-003).

Cubre:
- BN-DUP-01: Unicidad de extracto por tarjeta + periodo
- BN-DUP-02: Periodo requerido para validacion de duplicidad
- Safety net: IntegrityError capturado en save()

Convencion TDD:
- Carpeta: CargarExtractoHandlerTests/
- Archivo: test_handle.py (todos los escenarios del metodo handle_cargar_extracto)
- Nombramiento: test_should_{resultado}_when_{condicion}
- Patron: AAA con # Arrange -----, # Act -----, # Assert -----
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from src.application.commands.cargar_extracto import CargarExtractoCommand
from src.application.handlers.command_handlers import CommandHandler
from src.domain.entities.extracto import EstadoExtracto, Extracto
from src.domain.events import (
    ExtractoProcesado,
)
from src.domain.exceptions import ExtractoDuplicadoError
from src.domain.repositories import (
    IExtractoRepository,
    ITransaccionRepository,
)

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def usuario_id() -> UUID:
    return uuid4()


@pytest.fixture
def tarjeta_id() -> UUID:
    return uuid4()


@pytest.fixture
def extracto_id_existente() -> UUID:
    return uuid4()


@pytest.fixture
def periodo_inicio() -> date:
    return date(2026, 5, 1)


@pytest.fixture
def periodo_fin() -> date:
    return date(2026, 5, 31)


@pytest.fixture
def cmd(usuario_id: UUID, tarjeta_id: UUID) -> CargarExtractoCommand:
    return CargarExtractoCommand(
        usuario_id=usuario_id,
        tarjeta_id=tarjeta_id,
        filename="extracto_mayo_2026.xlsx",
        file_content=b"mock excel content",
    )


@pytest.fixture
def mock_extracto_repo() -> MagicMock:
    """Mock de IExtractoRepository con soporte para get_by_tarjeta_and_periodo."""
    repo = MagicMock(spec=IExtractoRepository)
    repo.save = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_usuario = AsyncMock()
    repo.get_by_tarjeta_and_periodo = AsyncMock(return_value=None)
    repo.get_by_tarjeta_and_file_hash = AsyncMock(return_value=None)
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def mock_transaccion_repo() -> MagicMock:
    """Mock de ITransaccionRepository."""
    repo = MagicMock(spec=ITransaccionRepository)
    repo.bulk_save = AsyncMock(return_value=[])
    repo.save = AsyncMock()
    repo.get_by_id = AsyncMock()
    return repo


@pytest.fixture
def mock_event_bus() -> MagicMock:
    """Mock del event bus."""
    bus = MagicMock()
    bus.publish = AsyncMock()
    return bus


@pytest.fixture
def handler(
    mock_extracto_repo: MagicMock,
    mock_transaccion_repo: MagicMock,
    mock_event_bus: MagicMock,
) -> CommandHandler:
    """SUT: CommandHandler con dependencias mockeadas."""
    return CommandHandler(
        extracto_repo=mock_extracto_repo,
        transaccion_repo=mock_transaccion_repo,
        categoria_repo=MagicMock(),
        presupuesto_repo=MagicMock(),
        tarjeta_repo=MagicMock(),
        usuario_repo=MagicMock(),
        event_bus=mock_event_bus,
    )


# ============================================================
# Mock helpers
# ============================================================


def _create_mock_parse_result(periodo_inicio=None, periodo_fin=None, exitoso=True):
    """Crea un mock de resultado de parseo como el que retorna ExtractoExcelParser."""
    result = MagicMock()
    result.exitoso = exitoso
    result.metadatos = {}
    if periodo_inicio is not None:
        result.metadatos["periodo_inicio"] = periodo_inicio
    if periodo_fin is not None:
        result.metadatos["periodo_fin"] = periodo_fin
    result.transacciones = [
        {
            "fecha": date(2026, 5, 15),
            "comercio_original": "SUPERMERCADO EL EXITO",
            "valor": Decimal("150000"),
            "numero_cuotas": "1/1",
        }
    ]
    result.errores = []
    return result


def _mock_parser(periodo_inicio=None, periodo_fin=None, exitoso=True):
    """Retorna un MagicMock configurado para ExtractoExcelParser."""
    mock_parser_instance = MagicMock()
    mock_parser_instance.parse.return_value = _create_mock_parse_result(
        periodo_inicio=periodo_inicio, periodo_fin=periodo_fin, exitoso=exitoso
    )
    return mock_parser_instance


def _create_existing_extracto(extracto_id: UUID, tarjeta_id: UUID, p_inicio: date, p_fin: date):
    """Crea un mock de extracto existente retornado por get_by_tarjeta_and_periodo."""
    existing = MagicMock()
    existing.id = extracto_id
    existing.tarjeta_id = tarjeta_id
    existing.periodo_inicio = p_inicio
    existing.periodo_fin = p_fin
    existing.estado = "COMPLETED"
    existing.progress_pct = 100
    return existing


# ============================================================
# TestDuplicateDetection — BN-DUP-01: Deteccion de duplicados
# ============================================================


class TestDuplicateDetection:
    """Tests para la deteccion de extractos duplicados (pre-flight check)."""

    @pytest.mark.asyncio
    async def test_should_raise_duplicate_exception_when_extract_exists(
        self,
        handler: CommandHandler,
        cmd: CargarExtractoCommand,
        mock_extracto_repo: MagicMock,
        mock_transaccion_repo: MagicMock,
        mock_event_bus: MagicMock,
        extracto_id_existente: UUID,
        tarjeta_id: UUID,
        periodo_inicio: date,
        periodo_fin: date,
    ):
        """BN-DUP-01: Si get_by_tarjeta_and_periodo retorna extracto -> lanza ExtractoDuplicadoError."""
        # Arrange --------------------------------------------------------
        existing = _create_existing_extracto(
            extracto_id_existente, tarjeta_id, periodo_inicio, periodo_fin
        )
        mock_extracto_repo.get_by_tarjeta_and_periodo.return_value = existing
        # save() retorna el modelo guardado (usado por el handler para el primer save)
        mock_extracto_repo.save.return_value = MagicMock(
            id=uuid4(), estado="PARSING", progress_pct=10, tarjeta_id=tarjeta_id
        )
        mock_transaccion_repo.bulk_save.return_value = []
        mock_parse = _mock_parser(periodo_inicio=periodo_inicio, periodo_fin=periodo_fin)

        # Act & Assert ----------------------------------------------------
        with patch(
            "src.infrastructure.excel.parser.ExtractoExcelParser",
            return_value=mock_parse,
        ):
            with pytest.raises(ExtractoDuplicadoError) as exc_info:
                await handler.handle_cargar_extracto(cmd)

        # Assert ----------------------------------------------------------
        ex = exc_info.value
        assert ex.error_code == "EXTRACTO_DUPLICADO"
        assert ex.extracto_id == extracto_id_existente
        assert ex.tarjeta_id == tarjeta_id
        assert ex.periodo_inicio == periodo_inicio
        assert ex.periodo_fin == periodo_fin

    @pytest.mark.asyncio
    async def test_should_emit_duplicate_detected_event_when_duplicate(
        self,
        handler: CommandHandler,
        cmd: CargarExtractoCommand,
        mock_extracto_repo: MagicMock,
        mock_transaccion_repo: MagicMock,
        mock_event_bus: MagicMock,
        extracto_id_existente: UUID,
        tarjeta_id: UUID,
        periodo_inicio: date,
        periodo_fin: date,
    ):
        """BN-DUP-01: Se emite evento ExtractoDuplicadoDetectado antes de lanzar la excepcion."""
        # Arrange --------------------------------------------------------
        existing = _create_existing_extracto(
            extracto_id_existente, tarjeta_id, periodo_inicio, periodo_fin
        )
        mock_extracto_repo.get_by_tarjeta_and_periodo.return_value = existing
        mock_extracto_repo.save.return_value = MagicMock(
            id=uuid4(), estado="PARSING", progress_pct=10, tarjeta_id=tarjeta_id
        )
        mock_transaccion_repo.bulk_save.return_value = []
        mock_parse = _mock_parser(periodo_inicio=periodo_inicio, periodo_fin=periodo_fin)

        # Act ------------------------------------------------------------
        with patch(
            "src.infrastructure.excel.parser.ExtractoExcelParser",
            return_value=mock_parse,
        ):
            with pytest.raises(ExtractoDuplicadoError):
                await handler.handle_cargar_extracto(cmd)

        # Assert ----------------------------------------------------------
        # Verificar que se publico el evento ExtractoDuplicadoDetectado
        mock_event_bus.publish.assert_called()
        call_args = mock_event_bus.publish.call_args[0][0]
        from src.domain.events import ExtractoDuplicadoDetectado

        assert isinstance(call_args, ExtractoDuplicadoDetectado)
        assert call_args.extracto_id_existente == extracto_id_existente
        assert call_args.tarjeta_id == tarjeta_id


class TestNoDuplicateFlow:
    """Tests para el flujo normal cuando NO hay duplicado."""

    @pytest.mark.asyncio
    async def test_should_proceed_normally_when_no_duplicate(
        self,
        handler: CommandHandler,
        cmd: CargarExtractoCommand,
        mock_extracto_repo: MagicMock,
        mock_transaccion_repo: MagicMock,
        mock_event_bus: MagicMock,
        tarjeta_id: UUID,
        periodo_inicio: date,
        periodo_fin: date,
    ):
        """BN-DUP-01 (rama NO existe): el flujo continua normalmente."""
        # Arrange --------------------------------------------------------
        mock_extracto_repo.get_by_tarjeta_and_periodo.return_value = None
        saved_extracto_mock = MagicMock(
            id=uuid4(),
            estado="COMPLETED",
            progress_pct=100,
            tarjeta_id=tarjeta_id,
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
        )
        mock_extracto_repo.save.return_value = saved_extracto_mock
        mock_transaccion_repo.bulk_save.return_value = []
        mock_parse = _mock_parser(periodo_inicio=periodo_inicio, periodo_fin=periodo_fin)

        # Act ------------------------------------------------------------
        with patch(
            "src.infrastructure.excel.parser.ExtractoExcelParser",
            return_value=mock_parse,
        ):
            result = await handler.handle_cargar_extracto(cmd)

        # Assert ----------------------------------------------------------
        # Verificar que get_by_tarjeta_and_periodo fue llamado
        mock_extracto_repo.get_by_tarjeta_and_periodo.assert_called_once_with(
            tarjeta_id=tarjeta_id,
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
        )
        # Verificar que el flujo continuo (save fue llamado al menos 1 vez — Fix #1: save post-parseo)
        assert mock_extracto_repo.save.call_count >= 1
        # Verificar que se emitio evento de exito
        mock_event_bus.publish.assert_called()
        # Verificar resultado
        assert "extract_id" in result
        assert result["estado"] == "COMPLETED"


class TestAllowWhenPeriodoNotDetectable:
    """Tests para Fix #2: Permitir extractos sin periodo detectable -> proteccion solo por hash.

    BN-DUP-02 modificado: Si periodo_inicio o periodo_fin es None post-parseo,
    se permite la carga pero solo se protege contra duplicados via file_hash
    (no via periodo). No se lanza ValidacionFallidaError.
    """

    @pytest.mark.asyncio
    async def test_should_allow_when_both_periodos_are_none(
        self,
        handler: CommandHandler,
        cmd: CargarExtractoCommand,
        mock_extracto_repo: MagicMock,
        mock_transaccion_repo: MagicMock,
        tarjeta_id: UUID,
    ):
        """Fix #2: Si ambos periodos son None post-parseo -> permite carga, protege por hash."""
        # Arrange --------------------------------------------------------
        mock_extracto_repo.get_by_tarjeta_and_periodo.return_value = None
        mock_extracto_repo.get_by_tarjeta_and_file_hash.return_value = None
        mock_extracto_repo.save.return_value = None
        mock_transaccion_repo.bulk_save.return_value = []
        mock_parse = _mock_parser(periodo_inicio=None, periodo_fin=None)

        # Act ------------------------------------------------------------
        with patch(
            "src.infrastructure.excel.parser.ExtractoExcelParser",
            return_value=mock_parse,
        ):
            result = await handler.handle_cargar_extracto(cmd)

        # Assert ----------------------------------------------------------
        # No debe lanzar excepcion
        assert result is not None
        # get_by_tarjeta_and_periodo NO debe llamarse (periodo no detectable)
        mock_extracto_repo.get_by_tarjeta_and_periodo.assert_not_called()
        # get_by_tarjeta_and_file_hash SI debe llamarse (proteccion por hash)
        mock_extracto_repo.get_by_tarjeta_and_file_hash.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_allow_when_periodo_inicio_is_none(
        self,
        handler: CommandHandler,
        cmd: CargarExtractoCommand,
        mock_extracto_repo: MagicMock,
        mock_transaccion_repo: MagicMock,
        tarjeta_id: UUID,
        periodo_fin: date,
    ):
        """Fix #2: Si solo periodo_inicio es None post-parseo -> permite carga."""
        # Arrange --------------------------------------------------------
        mock_extracto_repo.get_by_tarjeta_and_periodo.return_value = None
        mock_extracto_repo.get_by_tarjeta_and_file_hash.return_value = None
        mock_extracto_repo.save.return_value = None
        mock_transaccion_repo.bulk_save.return_value = []
        mock_parse = _mock_parser(periodo_inicio=None, periodo_fin=periodo_fin)

        # Act ------------------------------------------------------------
        with patch(
            "src.infrastructure.excel.parser.ExtractoExcelParser",
            return_value=mock_parse,
        ):
            result = await handler.handle_cargar_extracto(cmd)

        # Assert ----------------------------------------------------------
        assert result is not None
        mock_extracto_repo.get_by_tarjeta_and_periodo.assert_not_called()

    @pytest.mark.asyncio
    async def test_should_allow_when_periodo_fin_is_none(
        self,
        handler: CommandHandler,
        cmd: CargarExtractoCommand,
        mock_extracto_repo: MagicMock,
        mock_transaccion_repo: MagicMock,
        tarjeta_id: UUID,
        periodo_inicio: date,
    ):
        """Fix #2: Si solo periodo_fin es None post-parseo -> permite carga."""
        # Arrange --------------------------------------------------------
        mock_extracto_repo.get_by_tarjeta_and_periodo.return_value = None
        mock_extracto_repo.get_by_tarjeta_and_file_hash.return_value = None
        mock_extracto_repo.save.return_value = None
        mock_transaccion_repo.bulk_save.return_value = []
        mock_parse = _mock_parser(periodo_inicio=periodo_inicio, periodo_fin=None)

        # Act ------------------------------------------------------------
        with patch(
            "src.infrastructure.excel.parser.ExtractoExcelParser",
            return_value=mock_parse,
        ):
            result = await handler.handle_cargar_extracto(cmd)

        # Assert ----------------------------------------------------------
        assert result is not None
        mock_extracto_repo.get_by_tarjeta_and_periodo.assert_not_called()


class TestIntegrityErrorSafetyNet:
    """Tests para T007: Captura de IntegrityError en save()."""

    @pytest.mark.asyncio
    async def test_should_convert_integrity_error_to_domain_exception(
        self,
        handler: CommandHandler,
        cmd: CargarExtractoCommand,
        mock_extracto_repo: MagicMock,
        mock_transaccion_repo: MagicMock,
        mock_event_bus: MagicMock,
        tarjeta_id: UUID,
        periodo_inicio: date,
        periodo_fin: date,
    ):
        """T007: IntegrityError en save() -> ExtractoDuplicadoError() sin args."""
        # Arrange --------------------------------------------------------
        # get_by_tarjeta_and_periodo retorna None (pre-flight pasa limpio)
        mock_extracto_repo.get_by_tarjeta_and_periodo.return_value = None
        # get_by_tarjeta_and_file_hash tambien retorna None
        mock_extracto_repo.get_by_tarjeta_and_file_hash.return_value = None

        # Fix #1: save se llama solo UNA vez (post-parseo)
        # Simular IntegrityError como race condition
        mock_extracto_repo.save.side_effect = IntegrityError(
            "duplicate key value violates unique constraint", params=None, orig=None
        )
        mock_transaccion_repo.bulk_save.return_value = []
        mock_parse = _mock_parser(periodo_inicio=periodo_inicio, periodo_fin=periodo_fin)

        # Act & Assert ----------------------------------------------------
        with patch(
            "src.infrastructure.excel.parser.ExtractoExcelParser",
            return_value=mock_parse,
        ):
            with pytest.raises(ExtractoDuplicadoError) as exc_info:
                await handler.handle_cargar_extracto(cmd)

        # Assert ----------------------------------------------------------
        ex = exc_info.value
        assert ex.error_code == "EXTRACTO_DUPLICADO"
        # En race condition, extracto_id debe ser None
        assert ex.extracto_id is None
        assert ex.tarjeta_id is None
        assert "concurrencia" in str(ex).lower() or "simultanea" in str(ex).lower()


# ============================================================
# TestPeriodoValidation — Fix #2: Periodo no detectable -> 422
# ============================================================


class TestPeriodoValidation:
    """Tests para Fix #2: Periodo no detectable -> permite carga con proteccion por hash."""

    @pytest.mark.asyncio
    async def test_should_allow_and_use_hash_when_periodo_not_detectable(
        self,
        handler: CommandHandler,
        cmd: CargarExtractoCommand,
        mock_extracto_repo: MagicMock,
        mock_transaccion_repo: MagicMock,
        tarjeta_id: UUID,
    ):
        """Fix #2: Si el parser no extrae periodo -> permite carga, protege por hash."""
        # Arrange --------------------------------------------------------
        mock_extracto_repo.get_by_tarjeta_and_periodo.return_value = None
        mock_extracto_repo.get_by_tarjeta_and_file_hash.return_value = None
        mock_extracto_repo.save.return_value = None
        mock_transaccion_repo.bulk_save.return_value = []
        mock_parse = _mock_parser(periodo_inicio=None, periodo_fin=None)

        # Act ------------------------------------------------------------
        with patch(
            "src.infrastructure.excel.parser.ExtractoExcelParser",
            return_value=mock_parse,
        ):
            result = await handler.handle_cargar_extracto(cmd)

        # Assert ----------------------------------------------------------
        # No debe lanzar excepcion — el flujo completa normalmente
        assert result is not None
        # get_by_tarjeta_and_periodo NO debe llamarse (periodo no detectable)
        mock_extracto_repo.get_by_tarjeta_and_periodo.assert_not_called()
        # get_by_tarjeta_and_file_hash SI debe llamarse (proteccion por hash)
        mock_extracto_repo.get_by_tarjeta_and_file_hash.assert_called_once()
        # save SI se llama (el handler persiste el extracto)
        mock_extracto_repo.save.assert_called_once()


# ============================================================
# TestFileHashDetection — Fix #3: Hash SHA-256 como deteccion
# ============================================================


class TestFileHashDetection:
    """Tests para Fix #3: Deteccion de duplicados por hash SHA-256 del archivo."""

    @pytest.mark.asyncio
    async def test_should_detect_duplicate_by_file_hash_early_preparseo(
        self,
        handler: CommandHandler,
        cmd: CargarExtractoCommand,
        mock_extracto_repo: MagicMock,
        mock_transaccion_repo: MagicMock,
        mock_event_bus: MagicMock,
        extracto_id_existente: UUID,
        tarjeta_id: UUID,
        periodo_inicio: date,
        periodo_fin: date,
    ):
        """Fix #3: Pre-flight temprano por hash detecta duplicado antes del parseo -> 409.

        El hash se chequea inmediatamente al recibir el archivo, sin parsear.
        get_by_tarjeta_and_periodo NO se llama porque la excepcion se lanza antes.
        """
        # Arrange --------------------------------------------------------
        existing = _create_existing_extracto(
            extracto_id_existente, tarjeta_id, periodo_inicio, periodo_fin
        )
        # El chequeo temprano por hash encuentra match
        mock_extracto_repo.get_by_tarjeta_and_file_hash.return_value = existing

        # Act & Assert ----------------------------------------------------
        with pytest.raises(ExtractoDuplicadoError) as exc_info:
            await handler.handle_cargar_extracto(cmd)

        # Assert ----------------------------------------------------------
        ex = exc_info.value
        assert ex.error_code == "EXTRACTO_DUPLICADO"
        # get_by_tarjeta_and_periodo NO se llama (parseo no ocurre)
        mock_extracto_repo.get_by_tarjeta_and_periodo.assert_not_called()
        # get_by_tarjeta_and_file_hash SI se llama (pre-flight temprano)
        mock_extracto_repo.get_by_tarjeta_and_file_hash.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_save_extracto_after_parseo_not_before(
        self,
        handler: CommandHandler,
        cmd: CargarExtractoCommand,
        mock_extracto_repo: MagicMock,
        mock_transaccion_repo: MagicMock,
        mock_event_bus: MagicMock,
        tarjeta_id: UUID,
        periodo_inicio: date,
        periodo_fin: date,
    ):
        """Fix #1: El save() ocurre DESPUES del parseo, no antes.

        Verifica que save se llama exactamente 1 vez (en el flujo feliz),
        lo que indica que el primer save pre-parseo fue eliminado.
        Antes del fix, save se llamaba 2 veces.
        """
        # Arrange --------------------------------------------------------
        mock_extracto_repo.get_by_tarjeta_and_periodo.return_value = None
        mock_extracto_repo.get_by_tarjeta_and_file_hash.return_value = None
        saved_extracto_mock = MagicMock(
            id=uuid4(),
            estado="COMPLETED",
            progress_pct=100,
            tarjeta_id=tarjeta_id,
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
        )
        mock_extracto_repo.save.return_value = saved_extracto_mock
        mock_transaccion_repo.bulk_save.return_value = []
        mock_parse = _mock_parser(periodo_inicio=periodo_inicio, periodo_fin=periodo_fin)

        # Act ------------------------------------------------------------
        with patch(
            "src.infrastructure.excel.parser.ExtractoExcelParser",
            return_value=mock_parse,
        ):
            result = await handler.handle_cargar_extracto(cmd)

        # Assert ----------------------------------------------------------
        # Fix #1: solo 1 save (post-parseo), no 2 (antes: pre + post)
        assert mock_extracto_repo.save.call_count == 1
        assert "extract_id" in result

    @pytest.mark.asyncio
    async def test_should_persist_file_hash_on_first_save(
        self,
        handler: CommandHandler,
        cmd: CargarExtractoCommand,
        mock_extracto_repo: MagicMock,
        mock_transaccion_repo: MagicMock,
        mock_event_bus: MagicMock,
        tarjeta_id: UUID,
        periodo_inicio: date,
        periodo_fin: date,
    ):
        """Fix #3: El file_hash se calcula y persiste en el save."""
        # Arrange --------------------------------------------------------
        mock_extracto_repo.get_by_tarjeta_and_periodo.return_value = None
        mock_extracto_repo.get_by_tarjeta_and_file_hash.return_value = None
        saved_extracto_mock = MagicMock(
            id=uuid4(),
            estado="COMPLETED",
            progress_pct=100,
            tarjeta_id=tarjeta_id,
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
            file_hash=None,  # sera asignado por el handler
        )
        mock_extracto_repo.save.return_value = saved_extracto_mock
        mock_transaccion_repo.bulk_save.return_value = []
        mock_parse = _mock_parser(periodo_inicio=periodo_inicio, periodo_fin=periodo_fin)

        # Act ------------------------------------------------------------
        with patch(
            "src.infrastructure.excel.parser.ExtractoExcelParser",
            return_value=mock_parse,
        ):
            result = await handler.handle_cargar_extracto(cmd)

        # Assert ----------------------------------------------------------
        # Verificar que save fue llamado
        mock_extracto_repo.save.assert_called()
        # Obtener el extracto pasado al save
        call_args = mock_extracto_repo.save.call_args
        if call_args and call_args.args:
            extracto_pasado = call_args.args[0]
        elif call_args and call_args.kwargs:
            extracto_pasado = call_args.kwargs.get("extracto", None)
        else:
            extracto_pasado = None
        # file_hash debe estar asignado en la entidad pasada a save
        if extracto_pasado is not None:
            file_hash = getattr(extracto_pasado, "file_hash", None)
            assert file_hash is not None, "file_hash debe estar asignado antes de save"
            assert len(file_hash) == 64, (
                f"file_hash debe ser SHA-256 (64 chars), es: {len(file_hash)}"
            )
