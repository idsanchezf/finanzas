"""Tests para la inicializacion y flags automaticos de Transaccion.

Verifica __post_init__: derivacion de es_abono, es_cuota,
y propiedades basicas.

Convencion TDD:
- Carpeta: TransaccionTests/
- Archivo: test_init.py
"""

from datetime import date
from decimal import Decimal
from uuid import uuid4

from src.domain.entities.transaccion import Transaccion


class TestInit:
    """Tests para el constructor __init__ y __post_init__."""

    def test_Should_CreateTransaction_When_ValidData(self):
        """Camino feliz: crea transaccion con datos completos."""
        # Arrange --------------------------------------------------------
        extracto_id = uuid4()
        usuario_id = uuid4()

        # Act ------------------------------------------------------------
        tx = Transaccion(
            extracto_id=extracto_id,
            usuario_id=usuario_id,
            comercio_original="DLO*DIDI FOOD CO PAYIN",
            valor=Decimal("25000.00"),
            fecha=date(2026, 5, 15),
        )

        # Assert ----------------------------------------------------------
        assert tx.comercio_original == "DLO*DIDI FOOD CO PAYIN"
        assert tx.valor == Decimal("25000.00")
        assert tx.fecha == date(2026, 5, 15)
        assert tx.extracto_id == extracto_id
        assert tx.usuario_id == usuario_id

    def test_Should_SetEsAbonoTrue_When_ValorIsNegative(self):
        """Flag es_abono=True cuando valor < 0."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        tx = Transaccion(valor=Decimal("-1200000.00"))

        # Assert ----------------------------------------------------------
        assert tx.es_abono is True

    def test_Should_SetEsAbonoFalse_When_ValorIsPositive(self):
        """Flag es_abono=False cuando valor > 0."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        tx = Transaccion(valor=Decimal("50000.00"))

        # Assert ----------------------------------------------------------
        assert tx.es_abono is False

    def test_Should_SetEsAbonoFalse_When_ValorIsZero(self):
        """Flag es_abono=False cuando valor = 0 (no es negativo)."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        tx = Transaccion(valor=Decimal("0.00"))

        # Assert ----------------------------------------------------------
        assert tx.es_abono is False

    def test_Should_SetEsCuotaTrue_When_CuotasTotalesGreaterThanOne(self):
        """Flag es_cuota=True cuando cuotas_totales > 1."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        tx = Transaccion(
            valor=Decimal("360000.00"),
            cuotas_totales=12,
            cuota_actual=1,
            numero_cuotas="1/12",
        )

        # Assert ----------------------------------------------------------
        assert tx.es_cuota is True

    def test_Should_SetEsCuotaFalse_When_CuotasTotalesIsOne(self):
        """Flag es_cuota=False cuando cuotas_totales = 1."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        tx = Transaccion(
            valor=Decimal("50000.00"),
            cuotas_totales=1,
            numero_cuotas="1/1",
        )

        # Assert ----------------------------------------------------------
        assert tx.es_cuota is False

    def test_Should_SetEsCuotaFalse_When_NoCuotas(self):
        """Flag es_cuota=False cuando no hay cuotas_totales (None)."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        tx = Transaccion()

        # Assert ----------------------------------------------------------
        assert tx.es_cuota is False

    def test_Should_HaveDefaultId_When_NotProvided(self):
        """Genera UUID automatico si no se proporciona."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        tx = Transaccion()

        # Assert ----------------------------------------------------------
        assert tx.id is not None
        assert isinstance(tx.id, uuid4().__class__)

    def test_Should_HaveDefaultCreatedAt_When_NotProvided(self):
        """Genera timestamp de creacion automatico."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        tx = Transaccion()

        # Assert ----------------------------------------------------------
        assert tx.created_at is not None

    def test_Should_SetMonedaOriginalAndValor_When_Provided(self):
        """Soporta moneda original (USD) y su valor."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        tx = Transaccion(
            comercio_original="AMAZON.COM",
            valor=Decimal("150000.00"),
            moneda_original="USD",
            valor_moneda_original=Decimal("37.50"),
        )

        # Assert ----------------------------------------------------------
        assert tx.moneda_original == "USD"
        assert tx.valor_moneda_original == Decimal("37.50")

    def test_Should_SetParentTransactionId_When_SubFila(self):
        """Sub-fila VR MONEDA ORIG referencia a transaccion padre."""
        # Arrange --------------------------------------------------------
        parent_id = uuid4()

        # Act ------------------------------------------------------------
        tx = Transaccion(
            comercio_original="VR MONEDA ORIG USD",
            valor=Decimal("150.00"),
            parent_transaccion_id=parent_id,
        )

        # Assert ----------------------------------------------------------
        assert tx.parent_transaccion_id == parent_id
