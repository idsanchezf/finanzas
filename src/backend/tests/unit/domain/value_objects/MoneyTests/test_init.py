"""Tests para el constructor __init__ de Money.

Verifica creacion, redondeo a 2 decimales, inmutabilidad,
y metodos de fabrica (zero, cop, usd).

Convencion TDD:
- Carpeta: MoneyTests/
- Archivo: test_init.py (metodo __init__)
- Clases: TestInit (para el __init__)
- Metodos: Should_{Resultado}_When_{Condicion}
- Patron AAA
"""

from decimal import Decimal

import pytest

from src.domain.value_objects.money import Money


class TestInit:
    """Tests para la creacion e inicializacion de Money (metodo __init__)."""

    sut = Money

    # ------------------------------------------------------------------
    def test_Should_CreateMoney_When_ValidAmountAndCurrency(self):
        """Camino feliz: crea Money con monto y moneda validos."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        money = Money(Decimal("100.50"), "COP")

        # Assert ----------------------------------------------------------
        assert money.amount == Decimal("100.50")
        assert money.currency == "COP"

    # ------------------------------------------------------------------
    def test_Should_RoundToTwoDecimals_When_MoreDecimalsProvided(self):
        """Redondea a 2 decimales para precision financiera."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        money = Money(Decimal("100.456"), "COP")

        # Assert ----------------------------------------------------------
        assert money.amount == Decimal("100.46")

    # ------------------------------------------------------------------
    def test_Should_RoundToTwoDecimals_When_IntegerProvided(self):
        """Entero se redondea a 2 decimales."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        money = Money(Decimal("100"), "COP")

        # Assert ----------------------------------------------------------
        assert money.amount == Decimal("100.00")

    # ------------------------------------------------------------------
    def test_Should_BeImmutable_When_AttemptToModify(self):
        """El Value Object debe ser inmutable (frozen dataclass)."""
        # Arrange --------------------------------------------------------
        money = Money.cop(500)

        # Act & Assert ----------------------------------------------------
        with pytest.raises(Exception):
            money.amount = Decimal("600")  # type: ignore[misc]

    # ------------------------------------------------------------------
    def test_Should_CreateMoney_When_CurrencyIsCOP(self):
        """Moneda COP por defecto."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        money = Money(Decimal("50"))

        # Assert ----------------------------------------------------------
        assert money.currency == "COP"

    # ------------------------------------------------------------------
    def test_Should_CreateZero_When_ZeroFactoryMethod(self):
        """Metodo de fabrica .zero() crea Money(0, currency)."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        zero_cop = Money.zero("COP")
        zero_usd = Money.zero("USD")

        # Assert ----------------------------------------------------------
        assert zero_cop.amount == Decimal("0")
        assert zero_cop.currency == "COP"
        assert zero_usd.amount == Decimal("0")
        assert zero_usd.currency == "USD"

    # ------------------------------------------------------------------
    def test_Should_CreateCOP_When_CopFactoryMethod(self):
        """Metodo de fabrica .cop() crea Money en COP."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        money = Money.cop(1500)

        # Assert ----------------------------------------------------------
        assert money.amount == Decimal("1500.00")
        assert money.currency == "COP"

    # ------------------------------------------------------------------
    def test_Should_CreateUSD_When_UsdFactoryMethod(self):
        """Metodo de fabrica .usd() crea Money en USD."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        money = Money.usd(99.99)

        # Assert ----------------------------------------------------------
        assert money.amount == Decimal("99.99")
        assert money.currency == "USD"

    # ------------------------------------------------------------------
    def test_Should_AcceptFloat_When_FactoryMethodConverts(self):
        """Acepta float y lo convierte a Decimal internamente."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        money = Money.cop(1500.75)

        # Assert ----------------------------------------------------------
        assert money.amount == Decimal("1500.75")

    # ------------------------------------------------------------------
    def test_Should_AcceptInt_When_FactoryMethodConverts(self):
        """Acepta int y lo convierte a Decimal internamente."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        money = Money.cop(2500000)

        # Assert ----------------------------------------------------------
        assert money.amount == Decimal("2500000.00")


class TestRepr:
    """Tests para __repr__ de Money."""

    def test_Should_FormatWithThousands_When_RepresentationCalled(self):
        """Representacion formateada con separador de miles."""
        # Arrange --------------------------------------------------------
        money = Money(Decimal("1500000.00"), "COP")

        # Act ------------------------------------------------------------
        result = repr(money)

        # Assert ----------------------------------------------------------
        assert "COP" in result
        assert "1,500,000.00" in result


class TestProperties:
    """Tests para las propiedades is_zero, is_negative, is_positive."""

    def test_Should_ReturnTrue_When_IsZeroOnZeroAmount(self):
        # Arrange --------------------------------------------------------
        money = Money.zero()

        # Act ------------------------------------------------------------
        result = money.is_zero

        # Assert ----------------------------------------------------------
        assert result is True

    def test_Should_ReturnFalse_When_IsZeroOnPositiveAmount(self):
        # Arrange --------------------------------------------------------
        money = Money.cop(100)

        # Act ------------------------------------------------------------
        result = money.is_zero

        # Assert ----------------------------------------------------------
        assert result is False

    def test_Should_ReturnTrue_When_IsPositiveOnPositiveAmount(self):
        # Arrange --------------------------------------------------------
        money = Money.cop(100)

        # Act ------------------------------------------------------------
        result = money.is_positive

        # Assert ----------------------------------------------------------
        assert result is True

    def test_Should_ReturnFalse_When_IsPositiveOnZero(self):
        # Arrange --------------------------------------------------------
        money = Money.zero()

        # Act ------------------------------------------------------------
        result = money.is_positive

        # Assert ----------------------------------------------------------
        assert result is False

    def test_Should_ReturnTrue_When_IsNegativeOnNegativeAmount(self):
        # Arrange --------------------------------------------------------
        money = Money.cop(-100)

        # Act ------------------------------------------------------------
        result = money.is_negative

        # Assert ----------------------------------------------------------
        assert result is True

    def test_Should_ReturnFalse_When_IsNegativeOnPositiveAmount(self):
        # Arrange --------------------------------------------------------
        money = Money.cop(100)

        # Act ------------------------------------------------------------
        result = money.is_negative

        # Assert ----------------------------------------------------------
        assert result is False
