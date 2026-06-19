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
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.infrastructure.messaging.rabbitmq import EXCHANGE_NAME
from src.infrastructure.persistence.repositories.extracto_repo import ExtractoRepository
from src.infrastructure.persistence.repositories.transaccion_repo import TransaccionRepository
from src.infrastructure.persistence.unit_of_work import UnitOfWork
from src.workers.extract_processor_service import (
    ExtractMessage,
    ExtractProcessorService,
)

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
                    "Mensaje recibido en %s: event=%s msg_id=%s",
                    self.queue_name, event_name, message.message_id,
                )

                await self.process_message(body, message.headers)

            except Exception:
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
    """Consumidor de la cola extractos.procesar (extract.uploaded).

    Procesa archivos Excel cargados por el usuario.

    Flujo completo:
    1. Recibe mensaje con tracking_id, file_key, card_id, user_id
    2. Descarga el archivo desde R2/S3 (o usa file_content inline)
    3. Parsea con ExtractoExcelParser
    4. Persiste transacciones y actualiza metadatos del extracto
    5. Publica evento ExtractoProcesado → transactions.new
    6. En caso de error: marca extracto como ERROR
    """

    def __init__(
        self,
        url: str,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        storage: Any = None,
        event_bus: Any = None,
    ) -> None:
        super().__init__(url, queue_name="extractos.procesar", prefetch_count=5)
        self.session_factory = session_factory
        self.storage = storage
        self.event_bus = event_bus

    async def process_message(self, body: dict[str, Any], headers: dict[str, Any]) -> None:
        """Procesa un evento de extracto cargado.

        El mensaje puede venir con los campos:
        - tracking_id / extracto_id: ID del extracto en BD
        - file_key / s3_key: Key en R2 para descargar el Excel
        - card_id / tarjeta_id: ID de la tarjeta
        - user_id / usuario_id: ID del usuario
        - file_content_b64: Contenido base64 del archivo (inline, sin R2)
        """
        msg = ExtractMessage.from_dict(body)

        logger.info(
            "Procesando extracto via RabbitMQ",
            extracto_id=str(msg.tracking_id),
            usuario_id=str(msg.user_id) if msg.user_id else None,
            file_key=msg.file_key,
            has_inline_content=bool(msg.file_content_b64),
        )

        # Si no hay session_factory, modo sin BD (testing/debug)
        if self.session_factory is None:
            logger.warning(
                "Session factory no configurada — procesamiento sin persistencia",
                extracto_id=str(msg.tracking_id),
            )
            return

        # Procesar con UnitOfWork (transaccion atomica)
        async with UnitOfWork(self.session_factory) as uow:
            extracto_repo = ExtractoRepository(uow.session)
            transaccion_repo = TransaccionRepository(uow.session)

            service = ExtractProcessorService(
                extracto_repo=extracto_repo,
                transaccion_repo=transaccion_repo,
                storage=self.storage,
                event_bus=self.event_bus,
            )

            result = await service.process(msg)

            if result.success:
                await uow.commit()
                logger.info(
                    "Extracto procesado exitosamente",
                    extracto_id=str(result.extracto_id),
                    transacciones=result.transaction_count,
                )
            else:
                # El servicio ya marco el extracto como ERROR.
                # Hacemos commit igual para persistir el estado ERROR.
                await uow.commit()
                logger.error(
                    "Extracto procesado con errores",
                    extracto_id=str(result.extracto_id),
                    errores=result.parse_errors,
                )


class ClassificationConsumer(BaseConsumer):
    """Consumidor de la cola extractos.clasificar.

    Clasifica transacciones usando el motor hibrido (reglas + ML).
    Delega la logica de clasificacion a ClassificationService.
    """

    def __init__(self, url: str, service: Any | None = None) -> None:
        super().__init__(url, queue_name="extractos.clasificar", prefetch_count=10)
        self._service = service

    async def process_message(self, body: dict[str, Any], headers: dict[str, Any]) -> None:
        """Procesa un evento ExtractoProcesado o TransaccionClasificada.

        Espera mensajes con formato:
        {
            "extract_id": "...",
            "transaction_ids": [...],
            "user_id": "..."
        }
        """
        extract_id = body.get("extract_id")
        transaction_ids = body.get("transaction_ids", [])
        user_id = body.get("user_id")

        # Validar payload
        if not extract_id or not user_id:
            logger.error(
                "Mensaje invalido: faltan extract_id o user_id. body=%s",
                str(body),
            )
            return

        # Convertir string IDs a UUID
        from uuid import UUID

        try:
            extract_uuid = UUID(extract_id) if isinstance(extract_id, str) else extract_id
            user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
            txn_ids = [
                UUID(tid) if isinstance(tid, str) else tid
                for tid in transaction_ids
            ]
        except (ValueError, TypeError) as e:
            logger.error(
                "IDs invalidos en el mensaje: error=%s extract_id=%s user_id=%s",
                str(e), str(extract_id), str(user_id),
            )
            return

        transaction_count = len(txn_ids)

        logger.info(
            "Clasificando transacciones: extract_id=%s count=%d user_id=%s",
            str(extract_uuid), transaction_count, str(user_uuid),
        )

        if self._service is None:
            # Lazy import e inicializacion si no se inyecto
            import os

            from src.infrastructure.persistence.unit_of_work import create_session_factory
            from src.workers.classification_service import ClassificationService

            database_url = os.getenv(
                "DATABASE_URL",
                "postgresql+asyncpg://postgres:postgres@localhost:5432/finance_report",
            )
            session_factory = await create_session_factory(database_url)
            self._service = ClassificationService(session_factory=session_factory)

        results = await self._service.process_extract(
            extract_id=extract_uuid,
            transaction_ids=txn_ids,
            user_id=user_uuid,
        )

        # Log de resultados
        classified = sum(1 for r in results if r["category_id"] is not None)
        low_confidence = sum(
            1 for r in results
            if r["category_id"] is not None and r["confidence"] < 70
        )

        logger.info(
            "Clasificacion completada via RabbitMQ: extract_id=%s total=%d classified=%d low_confidence=%d",
            str(extract_uuid), transaction_count, classified, low_confidence,
        )


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
