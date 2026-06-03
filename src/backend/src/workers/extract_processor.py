"""Worker — Procesador de Extractos.

Consume la cola extractos.procesar en RabbitMQ.
Descarga el archivo Excel desde R2, lo parsea, extrae transacciones
y las persiste en la base de datos. Publica evento ExtractoProcesado al terminar.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

# Asegurar que src/ esta en el path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.infrastructure.messaging.consumers import ExtractProcessorConsumer

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def main() -> None:
    """Entry point del worker de procesamiento de extractos."""
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

    logger.info("Iniciando ExtractProcessor worker...")
    logger.info(f"RabbitMQ URL: {rabbitmq_url}")

    consumer = ExtractProcessorConsumer(rabbitmq_url)

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
