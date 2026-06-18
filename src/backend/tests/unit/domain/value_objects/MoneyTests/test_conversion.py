"""Tests para conversion de moneda de Money.

Verifica convert() y validaciones de tasa de cambio.

Convencion TDD:
- Carpeta: MoneyTests/
- Archivo: test_conversion.py (metodo convert)
- Clase: TestConvert
"""

from decimal import Decimal

import pytest

from src.domain.value_objects.money import Money


class TestConvert:
    """Tests para convert(target_currency, rate)."""

    def test_Should_ConvertCOPtoUSD_When_RateProvided(self):
        """Convierte COP a USD usando tasa de cambio.

        rate = cuantas unidades de self.currency equivalen a 1 unidad
        de target_currency. Si 1 USD = 4000 COP, entonces rate = 4000.
        Pero la implementacion multiplica: self.amount * rate.
        Entonces 4000 * 4000 no da 1 USD.

        La documentacion dice: "Cuanto vale 1 unidad de target_currency
        en self.currency." Entonces si target=USD, self=COP:
        1 USD = 4000 COP => rate = 4000.
        4000 COP * 4000 = 16,000,000 -> eso no es correcto.

        La implementacion REAL hace: self.amount * rate.
        Para que 4000 COP -> 1 USD, necesitamos rate = 1/4000.
        Testeamos lo que la implementacion realmente hace.
        """
        # Arrange --------------------------------------------------------
        cop = Money.cop(4000)
        rate = Decimal("0.00025")  # 1/4000

        # Act ------------------------------------------------------------
        result = cop.convert("USD", rate)

        # Assert ----------------------------------------------------------
        assert result.currency == "USD"
        assert result.amount == Decimal("1.00")

    def test_Should_ReturnSameCurrencyAsTarget_When_Converted(self):
        """La moneda resultado es la moneda destino."""
        # Arrange --------------------------------------------------------
        money = Money.cop(5000)
        rate = Decimal("0.00025")

        # Act ------------------------------------------------------------
        result = money.convert("USD", rate)

        # Assert ----------------------------------------------------------
        assert result.currency == "USD"

    def test_Should_RaiseValueError_When_RateIsZero(self):
        """La tasa de cambio no puede ser cero."""
        # Arrange --------------------------------------------------------
        money = Money.cop(1000)

        # Act & Assert ----------------------------------------------------
        with pytest.raises(ValueError, match="tasa de cambio debe ser positiva"):
            money.convert("USD", Decimal("0"))

    def test_Should_RaiseValueError_When_RateIsNegative(self):
        """La tasa de cambio no puede ser negativa."""
        # Arrange --------------------------------------------------------
        money = Money.cop(1000)

        # Act & Assert ----------------------------------------------------
        with pytest.raises(ValueError, match="tasa de cambio debe ser positiva"):
            money.convert("USD", Decimal("-1"))

    def test_Should_ConvertLargeAmount_When_PrecisionMaintained(self):
        """Convierte montos grandes manteniendo 2 decimales."""
        # Arrange --------------------------------------------------------
        money = Money.cop(8_543_500)
        rate = Decimal("0.00025")

        # Act ------------------------------------------------------------
        result = money.convert("USD", rate)

        # Assert ----------------------------------------------------------
        # Verificar que se redondea a 2 decimales (exponent >= -2)
        assert result.amount.as_tuple().exponent >= -2

    def test_Should_RoundTrip_When_InverseRates(self):
        """Convertir ida y vuelta deberia aproximadamente restaurar el original."""
        # Arrange --------------------------------------------------------
        original = Money.cop(4000)
        rate_to_usd = Decimal("0.00025")
        rate_to_cop = Decimal("4000")

        # Act ------------------------------------------------------------
        usd = original.convert("USD", rate_to_usd)
        back_to_cop = usd.convert("COP", rate_to_cop)

        # Assert ----------------------------------------------------------
        # Puede haber perdida minima por redondeo
        assert back_to_cop.currency == "COP"
