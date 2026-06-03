"""Consumidores RabbitMQ — Workers que procesan eventos de dominio.

Cada worker consume de una cola especifica y ejecuta la logica correspondiente:
- extract_processor: Procesa archivos Excel
- classification_worker: Clasifica transacciones
- notification_worker: Envia notificaciones
"""

from __future__ import annotations

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any

import aio_pika

from src.infrastructure.messaging.rabbitmq import EXCHANGE_NAME

logger = logging.getLogger(__name__)


class BaseConsumer(ABC):
    """Consumidor base de RabbitMQ con manejo de ACK/NACK y DLQ.

    Los consumidores concretos heredan de esta clase y sobrescriben process_message.
    """

    def __init__(self, url: str, queue_name: str, prefetch_count: int = 10) -> None:
        self.url = url
        self.queue_name = queue_name
        self.prefetch_count = prefetch_count
        self._connection: aio_pika.RobustConnection | None = None

    async def start(self) -> None:
        """Inicia el consumidor: conecta, declara la cola y empieza a consumir."""
        self._connection = await aio_pika.connect_robust(self.url)
        channel = await self._connection.channel()
        await channel.set_qos(prefetch_count=self.prefetch_count)

        # Declarar exchange (debe existir, creado por el publisher)
        exchange = await channel.declare_exchange(
            EXCHANGE_NAME,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

        # Declarar cola
        queue = await channel.declare_queue(
            self.queue_name,
            durable=True,
        )

        # Binding
        await queue.bind(exchange, routing_key=self.queue_name)

        logger.info(f"Consumidor iniciado en cola '{self.queue_name}'")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                await self._handle_message(message)

    async def _handle_message(self, message: aio_pika.IncomingMessage) -> None:
        """Procesa un mensaje con manejo de errores y ACK/NACK."""
        async with message.process():
            try:
                body = json.loads(message.body.decode("utf-8"))
                event_name = message.headers.get("event_name", "Unknown")

                logger.debug(
                    f"Mensaje recibido en {self.queue_name}",
                    event_name=event_name,
                    message_id=message.message_id,
                )

                await self.process_message(body, message.headers)

            except Exception as e:
                logger.error(
                    f"Error procesando mensaje en {self.queue_name}",
                    exc_info=True,
                    message_id=message.message_id,
                )
                # Rechazar — va a DLQ despues de varios reintentos
                raise

    @abstractmethod
    async def process_message(self, body: dict[str, Any], headers: dict[str, Any]) -> None:
        """Procesa el contenido del mensaje.

        Implementado por cada worker concreto.

        Args:
            body: Contenido del mensaje decodificado de JSON.
            headers: Headers del mensaje (incluye event_name).
        """
        ...

    async def stop(self) -> None:
        """Detiene el consumidor cerrando la conexion."""
        if self._connection:
            await self._connection.close()
            logger.info(f"Consumidor {self.queue_name} detenido")


class ExtractProcessorConsumer(BaseConsumer):
    """Consumidor de la cola extractos.procesar.

    Procesa archivos Excel cargados por el usuario.
    """

    def __init__(self, url: str) -> None:
        super().__init__(url, queue_name="extractos.procesar", prefetch_count=5)

    async def process_message(self, body: dict[str, Any], headers: dict[str, Any]) -> None:
        """Procesa un evento ExtractoCargado."""
        extracto_id = body.get("extracto_id")
        usuario_id = body.get("usuario_id")
        s3_key = body.get("s3_key")

        logger.info(
            "Procesando extracto",
            extracto_id=extracto_id,
            usuario_id=usuario_id,
            s3_key=s3_key,
        )

        # TODO: Implementar logica de parseo en src/workers/extract_processor.py
        # 1. Descargar archivo Excel desde R2/S3
        # 2. Parsear usando openpyxl/pandas
        # 3. Extraer transacciones y metadatos
        # 4. Persistir en BD
        # 5. Publicar evento ExtractoProcesado

        await asyncio.sleep(0.1)  # Placeholder


class ClassificationConsumer(BaseConsumer):
    """Consumidor de la cola extractos.clasificar.

    Clasifica transacciones usando el motor hibrido (reglas + ML).
    """

    def __init__(self, url: str) -> None:
        super().__init__(url, queue_name="extractos.clasificar", prefetch_count=10)

    async def process_message(self, body: dict[str, Any], headers: dict[str, Any]) -> None:
        """Procesa un evento ExtractoProcesado."""
        extracto_id = body.get("extracto_id")
        transaction_count = body.get("transaction_count", 0)

        logger.info(
            "Clasificando transacciones",
            extracto_id=extracto_id,
            count=transaction_count,
        )

        # TODO: Implementar logica de clasificacion en src/workers/classification_worker.py
        await asyncio.sleep(0.1)  # Placeholder


class NotificationConsumer(BaseConsumer):
    """Consumidor de la cola notificaciones.enviar.

    Envia notificaciones push y email a los usuarios.
    """

    def __init__(self, url: str) -> None:
        super().__init__(url, queue_name="notificaciones.enviar", prefetch_count=10)

    async def process_message(self, body: dict[str, Any], headers: dict[str, Any]) -> None:
        """Procesa eventos de notificacion."""
        usuario_id = body.get("usuario_id")
        tipo = body.get("tipo_recordatorio") or body.get("tipo")

        logger.info(
            "Enviando notificacion",
            usuario_id=usuario_id,
            tipo=tipo,
        )

        # TODO: Implementar logica de notificaciones en src/workers/notification_worker.py
        await asyncio.sleep(0.1)  # Placeholder
