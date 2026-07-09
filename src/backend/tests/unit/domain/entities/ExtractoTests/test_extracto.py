"""Tests para la entidad Extracto — Aggregate Root de extracto bancario.

Verifica creacion, validaciones, calculos financieros, Money VO,
transiciones de estado y asociacion de transacciones.

Convencion TDD:
- Carpeta: ExtractoTests/
- Archivo: test_extracto.py
"""

from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from src.domain.entities.extracto import EstadoExtracto, Extracto
from src.domain.entities.transaccion import Transaccion
from src.domain.value_objects.money import Money

# ============================================================
# TestInit — Creacion y valores por defecto
# ============================================================


class TestInit:
    """Tests para el constructor __init__ y valores por defecto."""

    def test_Should_CreateExtracto_When_ValidData(self):
        """Camino feliz: crea extracto con datos completos."""
        # Arrange --------------------------------------------------------
        tarjeta_id = uuid4()
        usuario_id = uuid4()
        periodo_inicio = date(2026, 5, 15)
        periodo_fin = date(2026, 6, 14)
        fecha_corte = date(2026, 6, 14)
        fecha_limite_pago = date(2026, 7, 1)

        # Act ------------------------------------------------------------
        ext = Extracto(
            tarjeta_id=tarjeta_id,
            usuario_id=usuario_id,
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
            fecha_corte=fecha_corte,
            fecha_limite_pago=fecha_limite_pago,
            pago_total=Money.cop(2500000),
            pago_minimo=Money.cop(250000),
            cupo_total=Money.cop(5000000),
            cupo_disponible=Money.cop(2500000),
        )

        # Assert ----------------------------------------------------------
        assert ext.tarjeta_id == tarjeta_id
        assert ext.usuario_id == usuario_id
        assert ext.periodo_inicio == periodo_inicio
        assert ext.periodo_fin == periodo_fin
        assert ext.fecha_corte == fecha_corte
        assert ext.fecha_limite_pago == fecha_limite_pago
        assert ext.pago_total == Money.cop(2500000)
        assert ext.pago_minimo == Money.cop(250000)
        assert ext.cupo_total == Money.cop(5000000)
        assert ext.cupo_disponible == Money.cop(2500000)

    def test_Should_HavePendingDefaultStatus_When_Created(self):
        """Estado inicial por defecto es PENDING (pendiente)."""
        # Arrange --------------------------------------------------------
        periodo_inicio = date(2026, 5, 15)
        periodo_fin = date(2026, 6, 14)

        # Act ------------------------------------------------------------
        ext = Extracto(
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
        )

        # Assert ----------------------------------------------------------
        assert ext.estado == EstadoExtracto.PENDING

    def test_Should_HaveDefaultId_When_NotProvided(self):
        """Genera UUID automatico si no se proporciona."""
        # Arrange --------------------------------------------------------
        periodo_inicio = date(2026, 5, 15)
        periodo_fin = date(2026, 6, 14)

        # Act ------------------------------------------------------------
        ext = Extracto(
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
        )

        # Assert ----------------------------------------------------------
        assert ext.id is not None
        assert isinstance(ext.id, uuid4().__class__)

    def test_Should_HaveDefaultCreatedAt_When_NotProvided(self):
        """Genera timestamp de creacion automatico."""
        # Arrange --------------------------------------------------------
        periodo_inicio = date(2026, 5, 15)
        periodo_fin = date(2026, 6, 14)

        # Act ------------------------------------------------------------
        ext = Extracto(
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
        )

        # Assert ----------------------------------------------------------
        assert ext.created_at is not None

    def test_Should_SetDefaultMoneyZero_When_NotProvided(self):
        """Montos por defecto son Money.zero en COP."""
        # Arrange --------------------------------------------------------
        periodo_inicio = date(2026, 5, 15)
        periodo_fin = date(2026, 6, 14)

        # Act ------------------------------------------------------------
        ext = Extracto(
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
        )

        # Assert ----------------------------------------------------------
        assert ext.pago_total == Money.zero("COP")
        assert ext.pago_minimo == Money.zero("COP")
        assert ext.cupo_total == Money.zero("COP")
        assert ext.cupo_disponible == Money.zero("COP")


# ============================================================
# TestValidacionFechas — Validacion de periodo
# ============================================================


class TestValidacionFechas:
    """Tests para validacion de fechas del periodo."""

    def test_Should_RaiseValueError_When_PeriodoInicioAfterPeriodoFin(self):
        """periodo_inicio > periodo_fin lanza ValueError."""
        # Arrange --------------------------------------------------------
        inicio = date(2026, 6, 15)
        fin = date(2026, 5, 15)

        # Act & Assert ----------------------------------------------------
        with pytest.raises(ValueError, match="periodo_inicio.*anterior.*periodo_fin"):
            Extracto(periodo_inicio=inicio, periodo_fin=fin)

    def test_Should_Accept_When_PeriodoInicioBeforePeriodoFin(self):
        """periodo_inicio < periodo_fin es valido."""
        # Arrange --------------------------------------------------------
        inicio = date(2026, 5, 1)
        fin = date(2026, 5, 31)

        # Act ------------------------------------------------------------
        ext = Extracto(periodo_inicio=inicio, periodo_fin=fin)

        # Assert ----------------------------------------------------------
        assert ext.periodo_inicio == inicio
        assert ext.periodo_fin == fin

    def test_Should_Accept_When_PeriodoInicioEqualsPeriodoFin(self):
        """periodo_inicio == periodo_fin es valido (periodo de 1 dia)."""
        # Arrange --------------------------------------------------------
        mismo_dia = date(2026, 5, 15)

        # Act ------------------------------------------------------------
        ext = Extracto(periodo_inicio=mismo_dia, periodo_fin=mismo_dia)

        # Assert ----------------------------------------------------------
        assert ext.periodo_inicio == mismo_dia
        assert ext.periodo_fin == mismo_dia


# ============================================================
# TestDiasParaPago — Calculo de dias hasta fecha de pago
# ============================================================


class TestDiasParaPago:
    """Tests para el calculo de dias hasta la fecha limite de pago."""

    def test_Should_CalculateDiasParaPago_When_FechaLimitePagoSet(self):
        """Retorna dias restantes hasta la fecha limite de pago (desde hoy)."""
        # Arrange --------------------------------------------------------
        hoy = date.today()
        dias_futuro = 15
        fecha_pago = hoy + timedelta(days=dias_futuro)
        ext = Extracto(
            periodo_inicio=date(2026, 5, 1),
            periodo_fin=date(2026, 5, 31),
            fecha_limite_pago=fecha_pago,
        )

        # Act ------------------------------------------------------------
        result = ext.dias_para_pago

        # Assert ----------------------------------------------------------
        assert result == dias_futuro

    def test_Should_ReturnZero_When_PastDueDate(self):
        """Retorna 0 si la fecha de pago ya paso."""
        # Arrange --------------------------------------------------------
        fecha_pasada = date.today() - timedelta(days=5)
        ext = Extracto(
            periodo_inicio=date(2026, 5, 1),
            periodo_fin=date(2026, 5, 31),
            fecha_limite_pago=fecha_pasada,
        )

        # Act ------------------------------------------------------------
        result = ext.dias_para_pago

        # Assert ----------------------------------------------------------
        assert result == 0

    def test_Should_ReturnZero_When_NoFechaLimitePago(self):
        """Retorna 0 si no hay fecha limite de pago (None)."""
        # Arrange --------------------------------------------------------
        ext = Extracto(
            periodo_inicio=date(2026, 5, 1),
            periodo_fin=date(2026, 5, 31),
            fecha_limite_pago=None,
        )

        # Act ------------------------------------------------------------
        result = ext.dias_para_pago

        # Assert ----------------------------------------------------------
        assert result == 0

    def test_Should_CalculateDiasEntreCorteYPago_When_AmbasFechasDadas(self):
        """Dias entre fecha_corte y fecha_limite_pago (due_date - cutoff_date)."""
        # Arrange --------------------------------------------------------
        fecha_corte = date(2026, 6, 14)
        fecha_limite_pago = date(2026, 7, 1)
        ext = Extracto(
            periodo_inicio=date(2026, 5, 15),
            periodo_fin=date(2026, 6, 14),
            fecha_corte=fecha_corte,
            fecha_limite_pago=fecha_limite_pago,
        )

        # Act ------------------------------------------------------------
        result = ext.dias_entre_corte_y_pago

        # Assert ----------------------------------------------------------
        # 17 dias entre 14-jun y 1-jul
        assert result == 17

    def test_Should_ReturnNone_When_NoCutoffDate_ForDiasEntreCorteYPago(self):
        """Retorna None si falta fecha_corte o fecha_limite_pago."""
        # Arrange --------------------------------------------------------
        ext = Extracto(
            periodo_inicio=date(2026, 5, 1),
            periodo_fin=date(2026, 5, 31),
            fecha_corte=None,
            fecha_limite_pago=date(2026, 6, 10),
        )

        # Act ------------------------------------------------------------
        result = ext.dias_entre_corte_y_pago

        # Assert ----------------------------------------------------------
        assert result is None


# ============================================================
# TestCupoUtilizacion — Calculo de utilizacion de cupo
# ============================================================


class TestCupoUtilizacion:
    """Tests para el calculo de porcentaje de cupo utilizado."""

    def test_Should_CalculateCupoUtilizationPercentage_When_BothValuesSet(self):
        """Calcula (pago_total / cupo_total) * 100 con Money VO."""
        # Arrange --------------------------------------------------------
        ext = Extracto(
            periodo_inicio=date(2026, 5, 1),
            periodo_fin=date(2026, 5, 31),
            pago_total=Money.cop(2500000),
            cupo_total=Money.cop(5000000),
        )

        # Act ------------------------------------------------------------
        result = ext.porcentaje_cupo_utilizado

        # Assert ----------------------------------------------------------
        assert result == Decimal("50.00")

    def test_Should_ReturnZero_When_CupoTotalIsZero(self):
        """Retorna 0% si el cupo total es cero (evita division por cero)."""
        # Arrange --------------------------------------------------------
        ext = Extracto(
            periodo_inicio=date(2026, 5, 1),
            periodo_fin=date(2026, 5, 31),
            pago_total=Money.cop(2500000),
            cupo_total=Money.zero("COP"),
        )

        # Act ------------------------------------------------------------
        result = ext.porcentaje_cupo_utilizado

        # Assert ----------------------------------------------------------
        assert result == Decimal("0")

    def test_Should_ReturnZero_When_PagoTotalIsZero(self):
        """Retorna 0% si el pago total es cero."""
        # Arrange --------------------------------------------------------
        ext = Extracto(
            periodo_inicio=date(2026, 5, 1),
            periodo_fin=date(2026, 5, 31),
            pago_total=Money.zero("COP"),
            cupo_total=Money.cop(10000000),
        )

        # Act ------------------------------------------------------------
        result = ext.porcentaje_cupo_utilizado

        # Assert ----------------------------------------------------------
        assert result == Decimal("0")

    def test_Should_CalculateWithDecimalPrecision_When_FractionalAmounts(self):
        """Calcula con precision Decimal en montos fraccionarios."""
        # Arrange --------------------------------------------------------
        ext = Extracto(
            periodo_inicio=date(2026, 5, 1),
            periodo_fin=date(2026, 5, 31),
            pago_total=Money.cop(2567),
            cupo_total=Money.cop(10003),
        )

        # Act ------------------------------------------------------------
        result = ext.porcentaje_cupo_utilizado

        # Assert ----------------------------------------------------------
        # 2567 / 10003 * 100 ≈ 25.66...
        assert result > Decimal("25")
        assert result < Decimal("26")


# ============================================================
# TestAsociacionTransacciones — Asociacion de transacciones
# ============================================================


class TestAsociacionTransacciones:
    """Tests para asociar transacciones al extracto."""

    def test_Should_AcceptTransaccionesList_When_Provided(self):
        """El extracto puede contener una lista de transacciones."""
        # Arrange --------------------------------------------------------
        tx1 = Transaccion(
            comercio_original="DLO*DIDI FOOD",
            valor=Decimal("25000.00"),
        )
        tx2 = Transaccion(
            comercio_original="UBER TRIP",
            valor=Decimal("15000.00"),
        )
        ext = Extracto(
            periodo_inicio=date(2026, 5, 1),
            periodo_fin=date(2026, 5, 31),
            transacciones=[tx1, tx2],
        )

        # Act ------------------------------------------------------------
        result = ext.transacciones

        # Assert ----------------------------------------------------------
        assert len(result) == 2
        assert result[0] is tx1
        assert result[1] is tx2

    def test_Should_HaveEmptyTransacciones_ByDefault(self):
        """Lista de transacciones vacia por defecto."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        ext = Extracto(
            periodo_inicio=date(2026, 5, 1),
            periodo_fin=date(2026, 5, 31),
        )

        # Assert ----------------------------------------------------------
        assert ext.transacciones == []


# ============================================================
# TestMoneyVO — Uso de Money Value Object
# ============================================================


class TestMoneyVO:
    """Tests para verificar que los montos usan el Value Object Money."""

    def test_Should_UseMoneyVO_ForPagoTotal(self):
        """pago_total es instancia de Money."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        ext = Extracto(
            periodo_inicio=date(2026, 5, 1),
            periodo_fin=date(2026, 5, 31),
            pago_total=Money.cop(1000000),
        )

        # Assert ----------------------------------------------------------
        assert isinstance(ext.pago_total, Money)
        assert ext.pago_total.amount == Decimal("1000000.00")
        assert ext.pago_total.currency == "COP"

    def test_Should_UseMoneyVO_ForPagoMinimo(self):
        """pago_minimo es instancia de Money."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        ext = Extracto(
            periodo_inicio=date(2026, 5, 1),
            periodo_fin=date(2026, 5, 31),
            pago_minimo=Money.cop(250000),
        )

        # Assert ----------------------------------------------------------
        assert isinstance(ext.pago_minimo, Money)
        assert ext.pago_minimo.amount == Decimal("250000.00")
        assert ext.pago_minimo.currency == "COP"

    def test_Should_UseMoneyVO_ForCupoTotal(self):
        """cupo_total es instancia de Money."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        ext = Extracto(
            periodo_inicio=date(2026, 5, 1),
            periodo_fin=date(2026, 5, 31),
            cupo_total=Money.cop(5000000),
        )

        # Assert ----------------------------------------------------------
        assert isinstance(ext.cupo_total, Money)
        assert ext.cupo_total.amount == Decimal("5000000.00")

    def test_Should_UseMoneyVO_ForCupoDisponible(self):
        """cupo_disponible es instancia de Money."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        ext = Extracto(
            periodo_inicio=date(2026, 5, 1),
            periodo_fin=date(2026, 5, 31),
            cupo_disponible=Money.cop(3000000),
        )

        # Assert ----------------------------------------------------------
        assert isinstance(ext.cupo_disponible, Money)
        assert ext.cupo_disponible.amount == Decimal("3000000.00")

    def test_Should_SupportMoneyOperations_When_MoneyValues(self):
        """Soporta operaciones aritmeticas del VO Money."""
        # Arrange --------------------------------------------------------
        ext = Extracto(
            periodo_inicio=date(2026, 5, 1),
            periodo_fin=date(2026, 5, 31),
            pago_total=Money.cop(1000000),
            cupo_total=Money.cop(5000000),
        )

        # Act ------------------------------------------------------------
        cupo_restante = ext.cupo_total - ext.pago_total

        # Assert ----------------------------------------------------------
        assert cupo_restante == Money.cop(4000000)


# ============================================================
# TestTransicionesEstado — Transiciones de estado
# ============================================================


class TestTransicionesEstado:
    """Tests para las transiciones validas de estado del extracto."""

    def test_Should_TransitionToParsing_When_IniciarProcesamiento(self):
        """PENDING -> PARSING al iniciar procesamiento."""
        # Arrange --------------------------------------------------------
        ext = Extracto(
            periodo_inicio=date(2026, 5, 1),
            periodo_fin=date(2026, 5, 31),
            archivo_s3_key="extractos/test.xlsx",
        )

        # Act ------------------------------------------------------------
        events = ext.iniciar_procesamiento()

        # Assert ----------------------------------------------------------
        assert ext.estado == EstadoExtracto.PARSING
        assert ext.progress_pct == 10
        assert len(events) == 1

    def test_Should_UpdateProgress_When_AvanzarParseo(self):
        """Actualiza progreso durante parseo (10-60%)."""
        # Arrange --------------------------------------------------------
        ext = Extracto(
            periodo_inicio=date(2026, 5, 1),
            periodo_fin=date(2026, 5, 31),
        )
        ext.iniciar_procesamiento()

        # Act ------------------------------------------------------------
        ext.avanzar_parseo(45)

        # Assert ----------------------------------------------------------
        assert ext.estado == EstadoExtracto.PARSING
        assert ext.progress_pct == 45

    def test_Should_CapProgressAt60_When_AvanzarParseoExceeds(self):
        """No puede exceder 60% en fase de parseo."""
        # Arrange --------------------------------------------------------
        ext = Extracto(
            periodo_inicio=date(2026, 5, 1),
            periodo_fin=date(2026, 5, 31),
        )
        ext.iniciar_procesamiento()

        # Act ------------------------------------------------------------
        ext.avanzar_parseo(90)

        # Assert ----------------------------------------------------------
        assert ext.progress_pct == 60

    def test_Should_FloorProgressAt10_When_AvanzarParseoBelow(self):
        """No puede bajar de 10% en fase de parseo."""
        # Arrange --------------------------------------------------------
        ext = Extracto(
            periodo_inicio=date(2026, 5, 1),
            periodo_fin=date(2026, 5, 31),
        )
        ext.iniciar_procesamiento()

        # Act ------------------------------------------------------------
        ext.avanzar_parseo(3)

        # Assert ----------------------------------------------------------
        assert ext.progress_pct == 10

    def test_Should_TransitionToClassifying_When_IniciarClasificacion(self):
        """Transicion a fase de clasificacion."""
        # Arrange --------------------------------------------------------
        ext = Extracto(
            periodo_inicio=date(2026, 5, 1),
            periodo_fin=date(2026, 5, 31),
        )

        # Act ------------------------------------------------------------
        ext.iniciar_clasificacion()

        # Assert ----------------------------------------------------------
        assert ext.estado == EstadoExtracto.CLASSIFYING
        assert ext.progress_pct == 70

    def test_Should_TransitionToCompleted_When_Completar(self):
        """Transicion a COMPLETED al terminar procesamiento."""
        # Arrange --------------------------------------------------------
        tx = Transaccion(
            comercio_original="TEST",
            valor=Decimal("10000.00"),
        )
        ext = Extracto(
            periodo_inicio=date(2026, 5, 1),
            periodo_fin=date(2026, 5, 31),
            transacciones=[tx],
        )

        # Act ------------------------------------------------------------
        events = ext.completar()

        # Assert ----------------------------------------------------------
        assert ext.estado == EstadoExtracto.COMPLETED
        assert ext.progress_pct == 100
        assert len(events) == 1

    def test_Should_TransitionToError_When_MarcarError(self):
        """Transicion a ERROR con mensaje descriptivo."""
        # Arrange --------------------------------------------------------
        ext = Extracto(
            periodo_inicio=date(2026, 5, 1),
            periodo_fin=date(2026, 5, 31),
        )

        # Act ------------------------------------------------------------
        ext.marcar_error("Archivo corrupto: formato no reconocido")

        # Assert ----------------------------------------------------------
        assert ext.estado == EstadoExtracto.ERROR
        assert ext.error_message == "Archivo corrupto: formato no reconocido"

    def test_Should_CompleteFlow_When_PendingToParsingToClassifyingToCompleted(self):
        """Flujo completo: PENDING -> PARSING -> CLASSIFYING -> COMPLETED."""
        # Arrange --------------------------------------------------------
        tx = Transaccion(
            comercio_original="DLO*DIDI FOOD",
            valor=Decimal("25000.00"),
        )
        ext = Extracto(
            periodo_inicio=date(2026, 5, 1),
            periodo_fin=date(2026, 5, 31),
            archivo_s3_key="extractos/mayo2026.xlsx",
            transacciones=[tx],
        )

        # Act ------------------------------------------------------------
        # 1. Iniciar procesamiento
        ext.iniciar_procesamiento()
        assert ext.estado == EstadoExtracto.PARSING
        assert ext.progress_pct == 10

        # 2. Avanzar parseo
        ext.avanzar_parseo(40)
        assert ext.progress_pct == 40

        # 3. Avanzar parseo a maximo
        ext.avanzar_parseo(60)
        assert ext.progress_pct == 60

        # 4. Iniciar clasificacion
        ext.iniciar_clasificacion()
        assert ext.estado == EstadoExtracto.CLASSIFYING
        assert ext.progress_pct == 70

        # 5. Completar
        events = ext.completar()
        assert ext.estado == EstadoExtracto.COMPLETED
        assert ext.progress_pct == 100

        # Assert ----------------------------------------------------------
        assert len(events) == 1
        assert ext.error_message is None


# ============================================================
# TestProperties — Propiedades adicionales
# ============================================================


class TestProperties:
    """Tests para propiedades derivadas."""

    def test_Should_CalculateDuracionPeriodo_When_DatesSet(self):
        """Duracion en dias del periodo de facturacion."""
        # Arrange --------------------------------------------------------
        ext = Extracto(
            periodo_inicio=date(2026, 5, 15),
            periodo_fin=date(2026, 6, 14),
        )

        # Act ------------------------------------------------------------
        result = ext.duracion_periodo

        # Assert ----------------------------------------------------------
        assert result == 30  # 30 dias entre 15-may y 14-jun
