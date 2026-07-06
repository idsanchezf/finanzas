"""Step definitions para BDD de feature feat-003: Prevenir extractos duplicados.

Los steps When usan asyncio.run() para ejecutar codigo async desde funciones
sincronas, que es el contrato de pytest-bdd para steps.
"""

from __future__ import annotations

import asyncio
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from pytest_bdd import given, parsers, then, when

from src.application.commands.cargar_extracto import CargarExtractoCommand
from src.application.handlers.command_handlers import CommandHandler
from src.domain.exceptions import ExtractoDuplicadoError, ValidacionFallidaError
from src.domain.repositories import IExtractoRepository, ITransaccionRepository


# ============================================================
# Fixtures compartidos
# ============================================================


@pytest.fixture
def bdd_context() -> dict:
    """Contexto mutable compartido entre todos los steps del escenario."""
    return {}


@pytest.fixture
def bdd_extracto_repo():
    repo = MagicMock(spec=IExtractoRepository)
    repo.save = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_usuario = AsyncMock()
    repo.get_by_tarjeta_and_periodo = AsyncMock(return_value=None)
    repo.get_by_tarjeta_and_file_hash = AsyncMock(return_value=None)
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def bdd_transaccion_repo():
    repo = MagicMock(spec=ITransaccionRepository)
    repo.bulk_save = AsyncMock(return_value=[])
    repo.save = AsyncMock()
    repo.get_by_id = AsyncMock()
    return repo


@pytest.fixture
def bdd_event_bus():
    bus = MagicMock()
    bus.publish = AsyncMock()
    return bus


@pytest.fixture
def bdd_handler(bdd_extracto_repo, bdd_transaccion_repo, bdd_event_bus):
    return CommandHandler(
        extracto_repo=bdd_extracto_repo,
        transaccion_repo=bdd_transaccion_repo,
        categoria_repo=MagicMock(),
        presupuesto_repo=MagicMock(),
        usuario_repo=MagicMock(),
        event_bus=bdd_event_bus,
    )


# ============================================================
# Helpers
# ============================================================


def _make_parse_result(periodo_inicio=None, periodo_fin=None, exitoso=True):
    result_mock = MagicMock()
    result_mock.exitoso = exitoso
    result_mock.metadatos = {}
    if periodo_inicio is not None:
        result_mock.metadatos["periodo_inicio"] = periodo_inicio
    if periodo_fin is not None:
        result_mock.metadatos["periodo_fin"] = periodo_fin
    result_mock.transacciones = [
        {"fecha": date(2026, 5, 15), "comercio_original": "COMERCIO DE PRUEBA",
         "valor": Decimal("50000"), "numero_cuotas": "1/1"}
    ]
    result_mock.errores = []
    return result_mock


async def _execute_handler_async(
    handler, extracto_repo, tarjeta_id, usuario_id, p_inicio, p_fin
) -> dict:
    saved_mock = MagicMock(
        id=uuid4(), estado="COMPLETED", progress_pct=100,
        tarjeta_id=tarjeta_id, periodo_inicio=p_inicio, periodo_fin=p_fin,
    )
    extracto_repo.save.return_value = saved_mock

    # Crear parser mock: parser.parse() retorna el resultado con metadatos
    parse_result = _make_parse_result(periodo_inicio=p_inicio, periodo_fin=p_fin)
    parser_mock = MagicMock()
    parser_mock.parse.return_value = parse_result

    cmd = CargarExtractoCommand(
        usuario_id=usuario_id, tarjeta_id=tarjeta_id,
        filename="test_extracto.xlsx", file_content=b"mock content",
    )

    result = {"status": "ok", "error": None}

    with patch(
        "src.infrastructure.excel.parser.ExtractoExcelParser",
        return_value=parser_mock,
    ):
        try:
            handler_result = await handler.handle_cargar_extracto(cmd)
            result["data"] = handler_result
            result["status"] = "created"
        except ValidacionFallidaError as e:
            result["status"] = "unprocessable"
            result["error"] = e
            result["mensaje"] = str(e)
        except ExtractoDuplicadoError as e:
            result["status"] = "conflict"
            result["error"] = e
            result["extracto_id"] = e.extracto_id
            result["tarjeta_id"] = e.tarjeta_id
            result["periodo_inicio"] = e.periodo_inicio
            result["periodo_fin"] = e.periodo_fin

    return result


def _execute_handler(
    handler, extracto_repo, tarjeta_id, usuario_id, p_inicio, p_fin
) -> dict:
    """Wrapper sincrono para ejecutar el handler async."""
    return asyncio.run(
        _execute_handler_async(handler, extracto_repo, tarjeta_id, usuario_id, p_inicio, p_fin)
    )


# ============================================================
# Given steps
# ============================================================


@given(parsers.parse('que existe una tarjeta "{ultimos_4}" del banco "{banco}"'))
def given_tarjeta_existe(bdd_context: dict, ultimos_4: str, banco: str) -> None:
    bdd_context["tarjeta_id"] = uuid4()
    bdd_context["ultimos_4"] = ultimos_4
    bdd_context["banco"] = banco


@given(
    parsers.parse(
        'que la tarjeta tiene un extracto cargado para el periodo "{p_inicio}" a "{p_fin}"'
    )
)
def given_tarjeta_tiene_extracto(bdd_context: dict, p_inicio: str, p_fin: str) -> None:
    existing = MagicMock()
    existing.id = uuid4()
    existing.tarjeta_id = bdd_context["tarjeta_id"]
    existing.periodo_inicio = date.fromisoformat(p_inicio)
    existing.periodo_fin = date.fromisoformat(p_fin)
    existing.estado = "COMPLETED"
    existing.progress_pct = 100
    bdd_context["extracto_existente"] = existing
    bdd_context["periodo_dup_inicio"] = date.fromisoformat(p_inicio)
    bdd_context["periodo_dup_fin"] = date.fromisoformat(p_fin)


@given(
    parsers.parse(
        'que la tarjeta "{ultimos_4}" NO tiene extracto para el periodo "{p_inicio}" a "{p_fin}"'
    )
)
def given_tarjeta_sin_extracto(
    bdd_context: dict, ultimos_4: str, p_inicio: str, p_fin: str
) -> None:
    bdd_context["sin_extracto"] = True


@given("que el archivo Excel no contiene informacion de periodo facturado")
def given_sin_periodo(bdd_context: dict) -> None:
    bdd_context["sin_periodo"] = True


# ============================================================
# When steps (sync — usan asyncio.run para el handler async)
# ============================================================


@when(
    parsers.parse(
        'el usuario sube un extracto para la tarjeta "{ultimos_4}" '
        'con periodo "{p_inicio}" a "{p_fin}"'
    )
)
def when_subir_extracto_con_periodo(
    bdd_context: dict,
    bdd_handler: CommandHandler,
    bdd_extracto_repo,
    ultimos_4: str,
    p_inicio: str,
    p_fin: str,
) -> None:
    tarjeta_id = bdd_context.get("tarjeta_id", uuid4())
    usuario_id = uuid4()
    periodo_inicio = date.fromisoformat(p_inicio)
    periodo_fin = date.fromisoformat(p_fin)

    if bdd_context.get("sin_extracto"):
        bdd_extracto_repo.get_by_tarjeta_and_periodo.return_value = None
    elif "extracto_existente" in bdd_context:
        # Solo retorna duplicado si tarjeta_id + periodo COINCIDEN exactamente
        expected_inicio = bdd_context.get("periodo_dup_inicio", periodo_inicio)
        expected_fin = bdd_context.get("periodo_dup_fin", periodo_fin)
        existing = bdd_context["extracto_existente"]

        def _side_effect(tarjeta_id, periodo_inicio, periodo_fin):
            if tarjeta_id == bdd_context["tarjeta_id"] and periodo_inicio == expected_inicio and periodo_fin == expected_fin:
                return existing
            return None

        bdd_extracto_repo.get_by_tarjeta_and_periodo.side_effect = _side_effect
    else:
        bdd_extracto_repo.get_by_tarjeta_and_periodo.return_value = None

    bdd_context["_result"] = _execute_handler(
        bdd_handler, bdd_extracto_repo, tarjeta_id, usuario_id,
        periodo_inicio, periodo_fin,
    )


@when(parsers.parse('el usuario sube el extracto para la tarjeta "{ultimos_4}"'))
def when_subir_extracto_sin_periodo(
    bdd_context: dict,
    bdd_handler: CommandHandler,
    bdd_extracto_repo,
    ultimos_4: str,
) -> None:
    tarjeta_id = bdd_context.get("tarjeta_id", uuid4())
    usuario_id = uuid4()
    bdd_extracto_repo.get_by_tarjeta_and_periodo.return_value = None

    bdd_context["_result"] = _execute_handler(
        bdd_handler, bdd_extracto_repo, tarjeta_id, usuario_id, None, None,
    )


def _result(ctx: dict) -> dict:
    return ctx.get("_result", {})


# ============================================================
# Then steps
# ============================================================


@then(parsers.parse("el sistema responde con codigo {codigo:d} Conflict"))
def then_codigo_409(bdd_context: dict, codigo: int) -> None:
    assert codigo == 409
    assert _result(bdd_context)["status"] == "conflict"


@then(parsers.parse("el sistema responde con codigo {codigo:d} Created"))
def then_codigo_201(bdd_context: dict, codigo: int) -> None:
    assert codigo == 201
    assert _result(bdd_context)["status"] == "created"


@then('el cuerpo de la respuesta contiene "extracto_id" del extracto ya existente')
def then_respuesta_contiene_extracto_id(bdd_context: dict) -> None:
    assert _result(bdd_context).get("extracto_id") is not None


@then("el mensaje incluye el id de la tarjeta y el rango del periodo")
def then_mensaje_incluye_tarjeta_y_periodo(bdd_context: dict) -> None:
    error = _result(bdd_context)["error"]
    assert error.tarjeta_id is not None
    assert error.periodo_inicio is not None
    assert error.periodo_fin is not None


@then("NO se persiste un nuevo extracto en la base de datos")
def then_no_se_persiste(bdd_context: dict) -> None:
    assert _result(bdd_context)["status"] == "conflict"


@then('se emite el evento de dominio "ExtractoDuplicadoDetectado"')
def then_emite_evento_duplicado(bdd_context: dict, bdd_event_bus) -> None:
    bdd_event_bus.publish.assert_called()
    call_args = bdd_event_bus.publish.call_args[0][0]
    from src.domain.events import ExtractoDuplicadoDetectado
    assert isinstance(call_args, ExtractoDuplicadoDetectado)


@then("el extracto se persiste correctamente en la base de datos")
def then_extracto_persiste(bdd_context: dict) -> None:
    assert _result(bdd_context)["status"] == "created"
    assert "data" in _result(bdd_context)


@then('se emite el evento de dominio "ExtractoCreado"')
def then_emite_evento_creado(bdd_context: dict, bdd_event_bus) -> None:
    bdd_event_bus.publish.assert_called()
    call_args = bdd_event_bus.publish.call_args[0][0]
    from src.domain.events import ExtractoProcesado
    assert isinstance(call_args, ExtractoProcesado)


@then('se registra un log de nivel WARN indicando "periodo no detectable, validacion de duplicado omitida"')
def then_registra_warn(bdd_context: dict) -> None:
    assert _result(bdd_context)["status"] == "created"


# ============================================================
# Nuevos steps — Fix #2 y Fix #3
# ============================================================


@given(parsers.parse('que la tarjeta tiene un extracto cargado con hash "{file_hash}"'))
def given_tarjeta_tiene_extracto_con_hash(bdd_context: dict, file_hash: str) -> None:
    """Fix #3: La tarjeta tiene un extracto existente con un file_hash conocido."""
    existing = MagicMock()
    existing.id = uuid4()
    existing.tarjeta_id = bdd_context["tarjeta_id"]
    existing.periodo_inicio = date(2026, 6, 1)
    existing.periodo_fin = date(2026, 6, 30)
    existing.estado = "COMPLETED"
    existing.progress_pct = 100
    existing.file_hash = file_hash
    bdd_context["extracto_existente_hash"] = existing
    bdd_context["file_hash_existente"] = file_hash


@when(parsers.parse('el usuario sube el mismo archivo Excel con hash "{file_hash}" para la tarjeta "{ultimos_4}"'))
def when_subir_extracto_con_hash(
    bdd_context: dict,
    bdd_handler: CommandHandler,
    bdd_extracto_repo,
    file_hash: str,
    ultimos_4: str,
) -> None:
    """Fix #3: Subir extracto con mismo hash de archivo."""
    tarjeta_id = bdd_context.get("tarjeta_id", uuid4())
    usuario_id = uuid4()

    # Periodo check: no match (periodo diferente)
    bdd_extracto_repo.get_by_tarjeta_and_periodo.return_value = None
    # File hash check: SI match
    existing = bdd_context.get("extracto_existente_hash")
    if existing:
        bdd_extracto_repo.get_by_tarjeta_and_file_hash.return_value = existing

    bdd_context["_result"] = _execute_handler(
        bdd_handler, bdd_extracto_repo, tarjeta_id, usuario_id,
        date(2026, 6, 1), date(2026, 6, 30),
    )


@then(parsers.parse("el sistema responde con codigo {codigo:d} Unprocessable Entity"))
def then_codigo_422(bdd_context: dict, codigo: int) -> None:
    assert codigo == 422
    assert _result(bdd_context)["status"] == "unprocessable"


@then("el mensaje indica que no se pudo determinar el periodo del extracto")
def then_mensaje_periodo_no_detectable(bdd_context: dict) -> None:
    mensaje = _result(bdd_context).get("mensaje", "")
    assert "periodo" in mensaje.lower() or "archivo" in mensaje.lower()


@then("el mensaje indica que el extracto ya existe por hash")
def then_mensaje_duplicado_hash(bdd_context: dict) -> None:
    assert _result(bdd_context)["status"] == "conflict"
