"""Entidad Usuario — Aggregate Root.

Representa un usuario de la plataforma Finance Report.
Autenticado via OAuth2 (Google/Microsoft). Soporta 2FA TOTP.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class AuthProvider(str, Enum):
    GOOGLE = "google"
    MICROSOFT = "microsoft"


@dataclass
class Usuario:
    """Usuario de la plataforma Finance Report."""

    id: UUID = field(default_factory=uuid4)
    email: str = ""
    nombre: str = ""
    avatar_url: str | None = None
    auth_provider: AuthProvider = AuthProvider.GOOGLE
    auth_provider_id: str = ""
    tfa_enabled: bool = False
    tfa_secret: str | None = None
    preferencias: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def enable_2fa(self, secret: str) -> None:
        """Habilita autenticacion de dos factores TOTP."""
        self.tfa_secret = secret
        self.tfa_enabled = True
        self.updated_at = datetime.utcnow()

    def disable_2fa(self) -> None:
        """Deshabilita autenticacion de dos factores."""
        self.tfa_secret = None
        self.tfa_enabled = False
        self.updated_at = datetime.utcnow()

    def update_preferences(self, preferencias: dict[str, Any]) -> None:
        """Actualiza las preferencias del usuario."""
        self.preferencias = {**self.preferencias, **preferencias}
        self.updated_at = datetime.utcnow()

    @property
    def moneda_default(self) -> str:
        """Moneda por defecto del usuario (COP por defecto)."""
        return self.preferencias.get("moneda", "COP")

    @property
    def idioma(self) -> str:
        """Idioma preferido (es por defecto)."""
        return self.preferencias.get("idioma", "es")
