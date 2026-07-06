"""Worker — Procesador de Extractos Bancarios.

Modos de operacion:
1. RabbitMQ mode (default): consume de la cola extractos.procesar.
2. Polling mode (fallback): si RabbitMQ no esta disponible, consulta la BD
   periodicamente por extractos en estado PENDING y los procesa.

Ejecucion standalone:
    cd src/backend && python -m src.workers.extract_processor

Variables de entorno:
    RABBITMQ_URL: URL de conexion RabbitMQ (default: amqp://guest:guest@localhost:5672/)
    DATABASE_URL: URL de conexion PostgreSQL (default: postgresql+asyncpg://...)
    POLLING_MODE: "true" para forzar modo polling (default: auto-detectar)
    POLLING_INTERVAL: segundos entre ciclos de polling (default: 5)
    R2_ACCESS_KEY, R2_SECRET_KEY, R2_ENDPOINT: credenciales Cloudflare R2
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

# Asegurar que src/ esta en el path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.infrastructure.database import async_session_factory
from src.infrastructure.messaging.consumers import ExtractProcessorConsumer
from src.infrastructure.messaging.rabbitmq import RabbitMQEventBus
from src.infrastructure.storage.r2_storage import R2Storage, get_storage
from src.workers.extract_processor_service import (
    ExtractMessage,
    ExtractProcessorService,
)

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


# ============================================================
# RabbitMQ Mode
# ============================================================


async def run_rabbitmq_mode(
    rabbitmq_url: str,
    storage: R2Storage,
    event_bus: RabbitMQEventBus,
) -> None:
    """Ejecuta el worker en modo RabbitMQ consumer."""
    logger.info("Iniciando ExtractProcessor en modo RabbitMQ...")
    logger.info(f"RabbitMQ URL: {rabbitmq_url}")
    logger.info("Cola: extractos.procesar")

    consumer = ExtractProcessorConsumer(
        url=rabbitmq_url,
        session_factory=async_session_factory,
        storage=storage,
        event_bus=event_bus,
    )

    try:
        await consumer.start()
    except KeyboardInterrupt:
        logger.info("Worker detenido por el usuario (Ctrl+C)")
    except Exception:
        logger.error("Error fatal en modo RabbitMQ", exc_info=True)
        raise
    finally:
        await consumer.stop()


# ============================================================
# Polling Mode (fallback sin RabbitMQ)
# ============================================================


async def run_polling_mode(
    poll_interval: int,
    storage: R2Storage,
) -> None:
    """Ejecuta el worker en modo polling (consulta BD por extractos PENDING).

    Util cuando RabbitMQ no esta disponible (desarrollo local, testing).
    """
    from sqlalchemy import select

    from src.infrastructure.persistence.models import ExtractoModel
    from src.infrastructure.persistence.repositories.extracto_repo import ExtractoRepository
    from src.infrastructure.persistence.repositories.transaccion_repo import TransaccionRepository

    logger.info(f"Iniciando ExtractProcessor en modo POLLING (intervalo={poll_interval}s)...")

    while True:
        try:
            async with async_session_factory() as session:
                # Buscar extractos en estado PENDING
                stmt = (
                    select(ExtractoModel)
                    .where(ExtractoModel.estado == "PENDING")
                    .order_by(ExtractoModel.created_at.asc())
                    .limit(5)
                )
                result = await session.execute(stmt)
                pending_extracts = list(result.scalars().all())

                if pending_extracts:
                    logger.info(
                        f"Polling: {len(pending_extracts)} extracto(s) pendiente(s) encontrado(s)"
                    )

                    for extracto_model in pending_extracts:
                        try:
                            extracto_repo = ExtractoRepository(session)
                            transaccion_repo = TransaccionRepository(session)

                            service = ExtractProcessorService(
                                extracto_repo=extracto_repo,
                                transaccion_repo=transaccion_repo,
                                storage=storage,
                                event_bus=None,  # Sin event bus en modo polling
                            )

                            msg = ExtractMessage(
                                tracking_id=extracto_model.id,
                                file_key=extracto_model.archivo_s3_key,
                                card_id=extracto_model.tarjeta_id,
                                user_id=extracto_model.usuario_id,
                            )

                            result = await service.process(msg)

                            if result.success:
                                await session.commit()
                                logger.info(
                                    f"Polling: extracto {extracto_model.id} procesado OK "
                                    f"({result.transaction_count} transacciones)"
                                )
                            else:
                                await session.commit()
                                logger.error(
                                    f"Polling: extracto {extracto_model.id} procesado con errores: "
                                    f"{result.parse_errors}"
                                )

                        except Exception:
                            await session.rollback()
                            logger.error(
                                f"Error procesando extracto {extracto_model.id} en polling",
                                exc_info=True,
                            )
                else:
                    logger.debug("Polling: sin extractos pendientes")

        except Exception:
            logger.error("Error en ciclo de polling", exc_info=True)

        await asyncio.sleep(poll_interval)


# ============================================================
# Deteccion de disponibilidad de RabbitMQ
# ============================================================


async def check_rabbitmq_available(url: str) -> bool:
    """Verifica si RabbitMQ esta disponible intentando una conexion."""
    import aio_pika

    try:
        connection = await aio_pika.connect_robust(url, timeout=3)
        await connection.close()
        return True
    except Exception:
        logger.warning(f"RabbitMQ no disponible en {url}. Usando modo polling como fallback.")
        return False


# ============================================================
# Entry point
# ============================================================


async def main() -> None:
    """Entry point del worker de procesamiento de extractos.

    Detecta automaticamente el modo de operacion:
    - Si POLLING_MODE=true → polling
    - Si RabbitMQ responde → RabbitMQ consumer
    - Si RabbitMQ no responde → polling (fallback)
    """
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    polling_mode = os.getenv("POLLING_MODE", "").lower() == "true"
    poll_interval = int(os.getenv("POLLING_INTERVAL", "5"))

    # Inicializar storage
    storage = get_storage()

    # Determinar modo
    if polling_mode:
        logger.info("POLLING_MODE=true forzado. Iniciando en modo polling.")
        await run_polling_mode(poll_interval, storage)
        return

    rabbitmq_available = await check_rabbitmq_available(rabbitmq_url)

    if rabbitmq_available:
        # Inicializar event bus
        event_bus = RabbitMQEventBus(rabbitmq_url)
        try:
            await event_bus.connect()
        except Exception as e:
            logger.error(f"Error conectando event bus: {e}. Usando polling.")
            await run_polling_mode(poll_interval, storage)
            return

        await run_rabbitmq_mode(rabbitmq_url, storage, event_bus)
    else:
        await run_polling_mode(poll_interval, storage)


if __name__ == "__main__":
    asyncio.run(main())
