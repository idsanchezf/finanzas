"""Cliente RabbitMQ — Publicacion de eventos de dominio.

Usa aio_pika para conexion async con RabbitMQ.
Publica eventos en el exchange 'finance.events' con routing key por tipo de evento.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from typing import Any

import aio_pika

logger = logging.getLogger(__name__)

# Exchange y colas definidos en la arquitectura
EXCHANGE_NAME = "finance.events"
DLQ_EXCHANGE_NAME = "finance.dlq"

QUEUES = {
    "extractos.procesar": "ExtractoCargado",
    "extractos.clasificar": "ExtractoProcesado",
    "notificaciones.enviar": "RecordatorioPendiente",
    "clasificacion.aprender": "CategoriaCorregida",
}


class RabbitMQEventBus:
    """Bus de eventos basado en RabbitMQ.

    Publica eventos de dominio al exchange 'finance.events'.
    Los workers consumen de colas especificas segun el tipo de evento.
    """

    def __init__(self, url: str = "amqp://guest:guest@localhost:5672/") -> None:
        self.url = url
        self._connection: aio_pika.RobustConnection | None = None
        self._channel: aio_pika.RobustChannel | None = None
        self._exchange: aio_pika.RobustExchange | None = None

    async def connect(self) -> None:
        """Establece conexion con RabbitMQ y declara el exchange."""
        self._connection = await aio_pika.connect_robust(self.url)
        self._channel = await self._connection.channel()

        # Declarar exchange principal (topic)
        self._exchange = await self._channel.declare_exchange(
            EXCHANGE_NAME,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

        # Declarar Dead Letter Exchange
        dlq_exchange = await self._channel.declare_exchange(
            DLQ_EXCHANGE_NAME,
            aio_pika.ExchangeType.DIRECT,
            durable=True,
        )

        # Declarar DLQ
        await self._channel.declare_queue(
            "dead_letter",
            durable=True,
            arguments={
                "x-message-ttl": 7 * 24 * 60 * 60 * 1000,  # 7 dias TTL
            },
        )

        # Declarar colas principales con DLQ configurado
        for queue_name in QUEUES:
            await self._channel.declare_queue(
                queue_name,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": DLQ_EXCHANGE_NAME,
                    "x-dead-letter-routing-key": "dead_letter",
                },
            )
            # Binding: cola recibe eventos con routing key que coincide con su nombre
            await self._exchange.bind(queue_name, routing_key=queue_name.replace(".", "."))

        logger.info("RabbitMQ conectado y exchange/config declarado")

    async def disconnect(self) -> None:
        """Cierra la conexion con RabbitMQ."""
        if self._connection:
            await self._connection.close()
            logger.info("RabbitMQ desconectado")

    async def publish(self, event: Any, routing_key: str | None = None) -> None:
        """Publica un evento de dominio en el exchange.

        Args:
            event: Evento de dominio (dataclass).
            routing_key: Opcional. Si no se provee, se deriva del nombre del evento.
        """
        if not self._exchange:
            await self.connect()

        if routing_key is None:
            # Derivar routing key del tipo de evento
            event_name = event.__class__.__name__
            routing_key = self._get_routing_key(event_name)

        # Serializar evento a JSON
        body = json.dumps(self._serialize_event(event), default=str).encode("utf-8")

        message = aio_pika.Message(
            body=body,
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            message_id=str(event.event_id),
            headers={
                "event_name": event.__class__.__name__,
                "occurred_at": event.occurred_at.isoformat() if hasattr(event, "occurred_at") else "",
            },
        )

        await self._exchange.publish(message, routing_key=routing_key)
        logger.debug(
            "Evento publicado",
            event_name=event.__class__.__name__,
            routing_key=routing_key,
        )

    def _get_routing_key(self, event_name: str) -> str:
        """Mapea nombre de evento a routing key de cola."""
        mapping = {
            "ExtractoCargado": "extractos.procesar",
            "ExtractoProcesado": "extractos.clasificar",
            "TransaccionClasificada": "extractos.clasificar",
            "CategoriaCorregida": "clasificacion.aprender",
            "PresupuestoAlcanzado": "notificaciones.enviar",
            "HabitoDetectado": "notificaciones.enviar",
            "RecordatorioPendiente": "notificaciones.enviar",
        }
        return mapping.get(event_name, "extractos.procesar")

    def _serialize_event(self, event: Any) -> dict[str, Any]:
        """Convierte un evento de dominio a dict serializable."""
        if hasattr(event, "__dataclass_fields__"):
            return asdict(event)
        return vars(event)


# Instancia singleton para uso en la aplicacion
_event_bus: RabbitMQEventBus | None = None


async def get_event_bus() -> RabbitMQEventBus:
    """Retorna la instancia singleton del bus de eventos."""
    global _event_bus
    if _event_bus is None:
        import os
        url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
        _event_bus = RabbitMQEventBus(url)
        await _event_bus.connect()
    return _event_bus
