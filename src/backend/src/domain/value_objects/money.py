"""Value Object Money — Monto monetario con precision financiera.

Inmutable. Usa Decimal para calculos financieros exactos.
Soporta conversion entre monedas.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from functools import total_ordering


@total_ordering
@dataclass(frozen=True)
class Money:
    """Monto monetario con moneda. Inmutable."""

    amount: Decimal
    currency: str = "COP"

    def __post_init__(self) -> None:
        """Redondea a 2 decimales para precision financiera."""
        object.__setattr__(self, "amount", self.amount.quantize(Decimal("0.01")))

    def __add__(self, other: Money) -> Money:
        self._validate_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._validate_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor: Decimal | int | float) -> Money:
        factor_dec = Decimal(str(factor))
        return Money(self.amount * factor_dec, self.currency)

    def __truediv__(self, divisor: Decimal | int | float) -> Money:
        divisor_dec = Decimal(str(divisor))
        if divisor_dec == 0:
            raise ZeroDivisionError("No se puede dividir por cero")
        return Money(self.amount / divisor_dec, self.currency)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount == other.amount and self.currency == other.currency

    def __lt__(self, other: Money) -> bool:
        self._validate_currency(other)
        return self.amount < other.amount

    def __neg__(self) -> Money:
        return Money(-self.amount, self.currency)

    def __abs__(self) -> Money:
        return Money(abs(self.amount), self.currency)

    def __repr__(self) -> str:
        return f"{self.currency} {self.amount:,.2f}"

    def _validate_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise ValueError(
                f"No se pueden operar montos con monedas diferentes: "
                f"{self.currency} vs {other.currency}"
            )

    def convert(self, target_currency: str, rate: Decimal) -> Money:
        """Convierte a otra moneda usando tasa de cambio.

        Args:
            target_currency: Codigo ISO de la moneda destino.
            rate: Tasa de cambio (cuanto vale 1 unidad de target_currency en self.currency).

        Returns:
            Money en la moneda destino.
        """
        if rate <= 0:
            raise ValueError("La tasa de cambio debe ser positiva")
        return Money(self.amount * rate, target_currency)

    def percentage(self, pct: Decimal) -> Money:
        """Calcula el porcentaje del monto."""
        return Money(self.amount * (pct / 100), self.currency)

    @property
    def is_zero(self) -> bool:
        return self.amount == 0

    @property
    def is_negative(self) -> bool:
        return self.amount < 0

    @property
    def is_positive(self) -> bool:
        return self.amount > 0

    @classmethod
    def zero(cls, currency: str = "COP") -> Money:
        return cls(Decimal("0"), currency)

    @classmethod
    def cop(cls, amount: Decimal | int | float) -> Money:
        return cls(Decimal(str(amount)), "COP")

    @classmethod
    def usd(cls, amount: Decimal | int | float) -> Money:
        return cls(Decimal(str(amount)), "USD")
