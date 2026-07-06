"""Value Object ConfianzaClasificacion — Nivel de certeza en la clasificacion."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class NivelConfianza(str, Enum):
    ALTA = "HIGH"  # >90%
    MEDIA = "MEDIUM"  # 70-90%
    BAJA = "LOW"  # <70%


@dataclass(frozen=True)
class ConfianzaClasificacion:
    """Nivel de confianza de una clasificacion automatica.

    ALTA:   >90% — Confiable, no requiere revision.
    MEDIA:  70-90% — Probablemente correcta.
    BAJA:   <70% — Requiere confirmacion del usuario.
    """

    score: Decimal  # 0-100
    fuente: str = "rules"  # "rules", "ml", "manual"

    def __post_init__(self) -> None:
        if self.score < 0 or self.score > 100:
            raise ValueError(f"Score fuera de rango: {self.score} (debe estar entre 0 y 100)")

    @property
    def nivel(self) -> NivelConfianza:
        """Nivel cualitativo de confianza."""
        if self.score >= 90:
            return NivelConfianza.ALTA
        elif self.score >= 70:
            return NivelConfianza.MEDIA
        else:
            return NivelConfianza.BAJA

    @property
    def requiere_revision(self) -> bool:
        """True si la clasificacion necesita revision del usuario."""
        return self.nivel == NivelConfianza.BAJA

    @property
    def porcentaje(self) -> str:
        return f"{self.score:.0f}%"

    @classmethod
    def alta(cls, fuente: str = "rules") -> ConfianzaClasificacion:
        """Confianza alta (95%)."""
        return cls(Decimal("95"), fuente)

    @classmethod
    def media(cls, fuente: str = "ml") -> ConfianzaClasificacion:
        """Confianza media (80%)."""
        return cls(Decimal("80"), fuente)

    @classmethod
    def baja(cls, fuente: str = "ml") -> ConfianzaClasificacion:
        """Confianza baja (50%)."""
        return cls(Decimal("50"), fuente)

    @classmethod
    def manual(cls) -> ConfianzaClasificacion:
        """Clasificacion manual del usuario (100%)."""
        return cls(Decimal("100"), "manual")
