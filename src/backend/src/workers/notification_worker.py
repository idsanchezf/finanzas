"""Worker — Servicio de Notificaciones.

Consume la cola notificaciones.enviar en RabbitMQ.
Envia notificaciones push (Web Push) y email a los usuarios.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.infrastructure.messaging.consumers import NotificationConsumer

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def main() -> None:
    """Entry point del worker de notificaciones."""
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

    logger.info("Iniciando Notification worker...")
    logger.info(f"RabbitMQ URL: {rabbitmq_url}")

    consumer = NotificationConsumer(rabbitmq_url)

    try:
        await consumer.start()
    except KeyboardInterrupt:
        logger.info("Worker detenido por el usuario")
    except Exception as e:
        logger.error("Error fatal en el worker", exc_info=True)
    finally:
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(main())
