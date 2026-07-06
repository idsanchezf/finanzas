"""Tests para operaciones aritmeticas de Money.

Verifica suma, resta, multiplicacion, division, negacion,
valor absoluto y comparaciones (==, <, >, <=, >=).

Convencion TDD:
- Carpeta: MoneyTests/
- Archivo: test_arithmetic.py (operadores aritmeticos)
- Clases: TestAdd, TestSub, TestMul, TestTruediv, TestNeg, TestAbs,
          TestEq, TestLt, TestGe, TestPercentage
"""

from decimal import Decimal

import pytest

from src.domain.value_objects.money import Money


class TestAdd:
    """Tests para __add__ (suma de Money + Money)."""

    def test_Should_AddAmounts_When_SameCurrency(self):
        # Arrange --------------------------------------------------------
        a = Money.cop(100)
        b = Money.cop(50)

        # Act ------------------------------------------------------------
        result = a + b

        # Assert ----------------------------------------------------------
        assert result.amount == Decimal("150.00")
        assert result.currency == "COP"

    def test_Should_AddDecimalAmounts_When_PrecisionMatters(self):
        # Arrange --------------------------------------------------------
        a = Money(Decimal("0.10"), "COP")
        b = Money(Decimal("0.20"), "COP")

        # Act ------------------------------------------------------------
        result = a + b

        # Assert ----------------------------------------------------------
        assert result.amount == Decimal("0.30")

    def test_Should_ReturnError_When_DifferentCurrencies(self):
        # Arrange --------------------------------------------------------
        a = Money.cop(100)
        b = Money.usd(50)

        # Act & Assert ----------------------------------------------------
        with pytest.raises(ValueError, match="monedas diferentes"):
            _ = a + b

    def test_Should_AddNegative_When_SubtractingEffectively(self):
        # Arrange --------------------------------------------------------
        a = Money.cop(100)
        b = Money.cop(-50)

        # Act ------------------------------------------------------------
        result = a + b

        # Assert ----------------------------------------------------------
        assert result.amount == Decimal("50.00")


class TestSub:
    """Tests para __sub__ (resta de Money - Money)."""

    def test_Should_SubtractAmounts_When_SameCurrency(self):
        # Arrange --------------------------------------------------------
        a = Money.cop(200)
        b = Money.cop(75)

        # Act ------------------------------------------------------------
        result = a - b

        # Assert ----------------------------------------------------------
        assert result.amount == Decimal("125.00")
        assert result.currency == "COP"

    def test_Should_ReturnNegative_When_SubtrahendGreater(self):
        # Arrange --------------------------------------------------------
        a = Money.cop(50)
        b = Money.cop(100)

        # Act ------------------------------------------------------------
        result = a - b

        # Assert ----------------------------------------------------------
        assert result.amount == Decimal("-50.00")

    def test_Should_ReturnError_When_DifferentCurrencies(self):
        # Arrange --------------------------------------------------------
        a = Money.cop(100)
        b = Money.usd(50)

        # Act & Assert ----------------------------------------------------
        with pytest.raises(ValueError, match="monedas diferentes"):
            _ = a - b


class TestMul:
    """Tests para __mul__ (Money * factor)."""

    def test_Should_MultiplyByInt_When_PositiveFactor(self):
        # Arrange --------------------------------------------------------
        money = Money.cop(150)

        # Act ------------------------------------------------------------
        result = money * 3

        # Assert ----------------------------------------------------------
        assert result.amount == Decimal("450.00")

    def test_Should_MultiplyByDecimal_When_PreciseFactor(self):
        # Arrange --------------------------------------------------------
        money = Money.cop(100)

        # Act ------------------------------------------------------------
        result = money * Decimal("1.5")

        # Assert ----------------------------------------------------------
        assert result.amount == Decimal("150.00")

    def test_Should_MultiplyByFloat_When_FractionalFactor(self):
        # Arrange --------------------------------------------------------
        money = Money.cop(200)

        # Act ------------------------------------------------------------
        result = money * 0.5

        # Assert ----------------------------------------------------------
        assert result.amount == Decimal("100.00")

    def test_Should_ReturnZero_When_MultiplyByZero(self):
        # Arrange --------------------------------------------------------
        money = Money.cop(999)

        # Act ------------------------------------------------------------
        result = money * 0

        # Assert ----------------------------------------------------------
        assert result.amount == Decimal("0.00")

    def test_Should_ReturnNegative_When_MultiplyByNegative(self):
        # Arrange --------------------------------------------------------
        money = Money.cop(100)

        # Act ------------------------------------------------------------
        result = money * -1

        # Assert ----------------------------------------------------------
        assert result.amount == Decimal("-100.00")


class TestTruediv:
    """Tests para __truediv__ (Money / divisor)."""

    def test_Should_DivideByInt_When_PositiveDivisor(self):
        # Arrange --------------------------------------------------------
        money = Money.cop(300)

        # Act ------------------------------------------------------------
        result = money / 3

        # Assert ----------------------------------------------------------
        assert result.amount == Decimal("100.00")

    def test_Should_DivideByDecimal_When_NonIntegerResult(self):
        # Arrange --------------------------------------------------------
        money = Money.cop(100)

        # Act ------------------------------------------------------------
        result = money / 3

        # Assert ----------------------------------------------------------
        assert result.amount == Decimal("33.33")

    def test_Should_RaiseZeroDivisionError_When_DivisorIsZero(self):
        # Arrange --------------------------------------------------------
        money = Money.cop(100)

        # Act & Assert ----------------------------------------------------
        with pytest.raises(ZeroDivisionError):
            _ = money / 0


class TestNeg:
    """Tests para __neg__ (-Money)."""

    def test_Should_Negate_When_PositiveAmount(self):
        # Arrange --------------------------------------------------------
        money = Money.cop(100)

        # Act ------------------------------------------------------------
        result = -money

        # Assert ----------------------------------------------------------
        assert result.amount == Decimal("-100.00")
        assert result.currency == "COP"

    def test_Should_MakePositive_When_NegativeAmount(self):
        # Arrange --------------------------------------------------------
        money = Money.cop(-50)

        # Act ------------------------------------------------------------
        result = -money

        # Assert ----------------------------------------------------------
        assert result.amount == Decimal("50.00")


class TestAbs:
    """Tests para __abs__ (abs(Money))."""

    def test_Should_ReturnPositive_When_NegativeAmount(self):
        # Arrange --------------------------------------------------------
        money = Money.cop(-100)

        # Act ------------------------------------------------------------
        result = abs(money)

        # Assert ----------------------------------------------------------
        assert result.amount == Decimal("100.00")

    def test_Should_ReturnSame_When_PositiveAmount(self):
        # Arrange --------------------------------------------------------
        money = Money.cop(100)

        # Act ------------------------------------------------------------
        result = abs(money)

        # Assert ----------------------------------------------------------
        assert result.amount == Decimal("100.00")


class TestEq:
    """Tests para __eq__ (igualdad de Money)."""

    def test_Should_BeEqual_When_SameAmountAndCurrency(self):
        # Arrange --------------------------------------------------------
        a = Money.cop(100)
        b = Money.cop(100)

        # Act ------------------------------------------------------------
        result = a == b

        # Assert ----------------------------------------------------------
        assert result is True

    def test_Should_NotBeEqual_When_DifferentAmount(self):
        # Arrange --------------------------------------------------------
        a = Money.cop(100)
        b = Money.cop(200)

        # Act ------------------------------------------------------------
        result = a == b

        # Assert ----------------------------------------------------------
        assert result is False

    def test_Should_NotBeEqual_When_DifferentCurrency(self):
        # Arrange --------------------------------------------------------
        a = Money.cop(100)
        b = Money.usd(100)

        # Act ------------------------------------------------------------
        result = a == b

        # Assert ----------------------------------------------------------
        assert result is False

    def test_Should_NotBeEqual_When_ComparedToNonMoney(self):
        # Arrange --------------------------------------------------------
        money = Money.cop(100)

        # Act ------------------------------------------------------------
        result = money == "not money"

        # Assert ----------------------------------------------------------
        assert result is False


class TestLt:
    """Tests para __lt__ (Money < Money)."""

    def test_Should_BeLessThan_When_AmountSmaller(self):
        # Arrange --------------------------------------------------------
        a = Money.cop(100)
        b = Money.cop(200)

        # Act ------------------------------------------------------------
        result = a < b

        # Assert ----------------------------------------------------------
        assert result is True

    def test_Should_NotBeLessThan_When_AmountGreater(self):
        # Arrange --------------------------------------------------------
        a = Money.cop(300)
        b = Money.cop(200)

        # Act ------------------------------------------------------------
        result = a < b

        # Assert ----------------------------------------------------------
        assert result is False

    def test_Should_NotBeLessThan_When_AmountEqual(self):
        # Arrange --------------------------------------------------------
        a = Money.cop(200)
        b = Money.cop(200)

        # Act ------------------------------------------------------------
        result = a < b

        # Assert ----------------------------------------------------------
        assert result is False

    def test_Should_ReturnError_When_DifferentCurrencies(self):
        # Arrange --------------------------------------------------------
        a = Money.cop(100)
        b = Money.usd(200)

        # Act & Assert ----------------------------------------------------
        with pytest.raises(ValueError, match="monedas diferentes"):
            _ = a < b


class TestGe:
    """Tests para comparacion >= (via total_ordering)."""

    def test_Should_BeGreaterEqual_When_AmountGreater(self):
        # Arrange --------------------------------------------------------
        a = Money.cop(300)
        b = Money.cop(200)

        # Act ------------------------------------------------------------
        result = a >= b

        # Assert ----------------------------------------------------------
        assert result is True

    def test_Should_BeGreaterEqual_When_AmountEqual(self):
        # Arrange --------------------------------------------------------
        a = Money.cop(200)
        b = Money.cop(200)

        # Act ------------------------------------------------------------
        result = a >= b

        # Assert ----------------------------------------------------------
        assert result is True

    def test_Should_NotBeGreaterEqual_When_AmountSmaller(self):
        # Arrange --------------------------------------------------------
        a = Money.cop(100)
        b = Money.cop(200)

        # Act ------------------------------------------------------------
        result = a >= b

        # Assert ----------------------------------------------------------
        assert result is False


class TestPercentage:
    """Tests para percentage()."""

    def test_Should_Calculate10Percent_When_PositiveAmount(self):
        # Arrange --------------------------------------------------------
        money = Money.cop(1000)

        # Act ------------------------------------------------------------
        result = money.percentage(Decimal("10"))

        # Assert ----------------------------------------------------------
        assert result.amount == Decimal("100.00")

    def test_Should_Calculate50Percent_When_PositiveAmount(self):
        # Arrange --------------------------------------------------------
        money = Money.cop(500)

        # Act ------------------------------------------------------------
        result = money.percentage(Decimal("50"))

        # Assert ----------------------------------------------------------
        assert result.amount == Decimal("250.00")

    def test_Should_Calculate0Percent_When_ZeroAmount(self):
        # Arrange --------------------------------------------------------
        money = Money.cop(1000)

        # Act ------------------------------------------------------------
        result = money.percentage(Decimal("0"))

        # Assert ----------------------------------------------------------
        assert result.amount == Decimal("0.00")
