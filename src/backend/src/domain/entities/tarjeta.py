"""Entidad Tarjeta — Aggregate hijo de Usuario.

Representa una tarjeta de credito o debito asociada al usuario.
Solo se almacenan los ultimos 4 digitos por seguridad.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class TipoTarjeta(str, Enum):
    CREDITO = "credito"
    DEBITO = "debito"


@dataclass
class Tarjeta:
    """Tarjeta de credito o debito del usuario."""

    id: UUID = field(default_factory=uuid4)
    usuario_id: UUID = field(default_factory=uuid4)
    banco: str = ""
    ultimos_4_digitos: str = ""  # Solo los ultimos 4 digitos — NUNCA el numero completo
    tipo: TipoTarjeta = TipoTarjeta.CREDITO
    alias: str | None = None
    activa: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Valida que solo se almacenen 4 digitos del numero de tarjeta."""
        if self.ultimos_4_digitos and len(self.ultimos_4_digitos) > 4:
            raise ValueError("Solo se permite almacenar los ultimos 4 digitos de la tarjeta")
        if self.ultimos_4_digitos and not self.ultimos_4_digitos.isdigit():
            raise ValueError("Los ultimos 4 digitos deben ser numericos")

    def desactivar(self) -> None:
        """Desactiva la tarjeta (no se elimina para preservar historial)."""
        self.activa = False

    def activar(self) -> None:
        """Reactiva la tarjeta."""
        self.activa = True

    @property
    def nombre_visible(self) -> str:
        """Nombre visible de la tarjeta para el usuario."""
        return self.alias or f"{self.banco} *{self.ultimos_4_digitos}"
