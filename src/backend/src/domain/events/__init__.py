"""Eventos de dominio — Inmutables, representan hechos que ocurrieron.

Cada evento tiene un nombre unico, timestamp y payload inmutable.
Los workers y otros servicios consumen estos eventos via RabbitMQ.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4


@dataclass(frozen=True)
class DomainEvent:
    """Evento base del dominio."""

    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def event_name(self) -> str:
        return self.__class__.__name__


@dataclass(frozen=True)
class ExtractoCargado:
    """Se publica cuando un usuario sube un archivo Excel y se registra el extracto."""

    extracto_id: UUID
    usuario_id: UUID
    tarjeta_id: UUID
    s3_key: str = ""
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def event_name(self) -> str:
        return self.__class__.__name__


@dataclass(frozen=True)
class ExtractoProcesado:
    """Se publica cuando el Procesador de Extractos termina de parsear el Excel."""

    extracto_id: UUID
    usuario_id: UUID
    tarjeta_id: UUID
    transaction_count: int = 0
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def event_name(self) -> str:
        return self.__class__.__name__


@dataclass(frozen=True)
class TransaccionClasificada:
    """Se publica cuando una transaccion es clasificada (automatica o manualmente)."""

    transaction_id: UUID
    extracto_id: UUID
    categoria_id: UUID
    categoria_anterior: UUID | None = None
    confidence: Decimal = field(default_factory=lambda: Decimal("0"))
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def event_name(self) -> str:
        return self.__class__.__name__


@dataclass(frozen=True)
class CategoriaCorregida:
    """Se publica cuando el usuario corrige manualmente la categoria de una transaccion.

    Este evento dispara el aprendizaje del modelo ML.
    """

    transaction_id: UUID
    categoria_nueva: UUID
    categoria_anterior: UUID | None = None
    comercio_original: str = ""
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def event_name(self) -> str:
        return self.__class__.__name__


@dataclass(frozen=True)
class PresupuestoAlcanzado:
    """Se publica cuando el gasto de una categoria alcanza el 80% o 100% del presupuesto."""

    usuario_id: UUID
    presupuesto_id: UUID
    categoria_id: UUID
    porcentaje: Decimal = field(default_factory=lambda: Decimal("0"))
    umbral: str = "80"  # "80" o "100"
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def event_name(self) -> str:
        return self.__class__.__name__


@dataclass(frozen=True)
class HabitoDetectado:
    """Se publica cuando el sistema detecta un mal habito financiero."""

    usuario_id: UUID
    tipo_habito: str = ""
    titulo: str = ""
    mensaje: str = ""
    severidad: str = "medium"  # "low", "medium", "high", "critical"
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def event_name(self) -> str:
        return self.__class__.__name__


@dataclass(frozen=True)
class RecordatorioPendiente:
    """Se publica cuando hay un recordatorio programado para el usuario."""

    usuario_id: UUID
    tipo_recordatorio: str = ""  # "pago", "corte", "presupuesto"
    tarjeta_id: UUID | None = None
    fecha_limite: datetime | None = None
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def event_name(self) -> str:
        return self.__class__.__name__


@dataclass(frozen=True)
class ExtractoDuplicadoDetectado:
    """Se emite cuando se detecta un intento de cargar un extracto duplicado.

    Es un evento informativo: no modifica estado, solo habilita
    logging, metricas y notificaciones (feat-003).
    """

    extracto_id_existente: UUID
    tarjeta_id: UUID
    periodo_inicio: date | None = None
    periodo_fin: date | None = None
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def event_name(self) -> str:
        return self.__class__.__name__


__all__ = [
    "DomainEvent",
    "ExtractoCargado",
    "ExtractoProcesado",
    "TransaccionClasificada",
    "CategoriaCorregida",
    "PresupuestoAlcanzado",
    "HabitoDetectado",
    "RecordatorioPendiente",
    "ExtractoDuplicadoDetectado",
]
