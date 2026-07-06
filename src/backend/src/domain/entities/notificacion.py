"""Entidad Notificacion — Mensajes dirigidos al usuario."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class TipoNotificacion(str, Enum):
    RECORDATORIO_PAGO = "recordatorio_pago"
    ALERTA_PRESUPUESTO = "alerta_presupuesto"
    RESUMEN_SEMANAL = "resumen_semanal"
    HABITO_DETECTADO = "habito_detectado"
    RECORDATORIO_CORTE = "recordatorio_corte"
    ALERTA_TRANSACCION_GRANDE = "alerta_transaccion_grande"
    RESUMEN_MENSUAL = "resumen_mensual"


class CanalNotificacion(str, Enum):
    PUSH = "push"
    EMAIL = "email"
    IN_APP = "in_app"


@dataclass
class Notificacion:
    """Notificacion dirigida al usuario (push, email o in-app)."""

    id: UUID = field(default_factory=uuid4)
    usuario_id: UUID = field(default_factory=uuid4)
    tipo: TipoNotificacion = TipoNotificacion.RESUMEN_SEMANAL
    titulo: str = ""
    mensaje: str = ""
    leida: bool = False
    canal: CanalNotificacion = CanalNotificacion.IN_APP
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def marcar_leida(self) -> None:
        """Marca la notificacion como leida."""
        self.leida = True
