"""Worker — Servicio de Clasificacion de Transacciones.

Consume mensajes de la cola `transactions.new` en RabbitMQ.
Ejecuta el pipeline de clasificacion hibrida (reglas + ML) sobre las
transacciones de un extracto procesado.

Modos de ejecucion:
- **RabbitMQ** (default): consume de la cola `extractos.clasificar`
- **Polling fallback**: si RabbitMQ no esta disponible, revisa la BD cada 5s
  por extractos en estado PARSING/CLASSIFYING con transacciones sin clasificar.

Uso standalone:
    cd src/backend && python -m src.workers.classification_worker
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.infrastructure.messaging.consumers import ClassificationConsumer
from src.workers.classification_service import ClassificationService

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


# ============================================================
# Constantes
# ============================================================

POLLING_INTERVAL_SECONDS = 5
RABBITMQ_DEFAULT_URL = "amqp://guest:guest@localhost:5672/"


# ============================================================
# Modo RabbitMQ
# ============================================================

class RabbitMQClassificationWorker:
    """Worker que consume via RabbitMQ y clasifica transacciones."""

    def __init__(
        self,
        rabbitmq_url: str,
        classification_service: ClassificationService,
    ) -> None:
        self._url = rabbitmq_url
        self._service = classification_service
        self._consumer: ClassificationConsumer | None = None

    async def start(self) -> None:
        """Inicia el worker conectando a RabbitMQ."""
        self._consumer = ClassificationConsumer(
            url=self._url,
            service=self._service,
        )
        await self._consumer.start()

    async def stop(self) -> None:
        """Detiene el worker cerrando la conexion."""
        if self._consumer:
            await self._consumer.stop()


# ============================================================
# Modo Polling (fallback sin RabbitMQ)
# ============================================================

class PollingClassificationWorker:
    """Worker que revisa la BD cada 5s en busca de transacciones sin clasificar.

    Util cuando RabbitMQ no esta disponible (desarrollo local, entornos limitados).
    """

    def __init__(
        self,
        service: ClassificationService,
        interval_seconds: float = POLLING_INTERVAL_SECONDS,
    ) -> None:
        self._service = service
        self._interval = interval_seconds
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Inicia el bucle de polling."""
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(
            "Polling worker iniciado",
            interval_seconds=self._interval,
        )

    async def stop(self) -> None:
        """Detiene el bucle de polling."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Polling worker detenido")

    async def _poll_loop(self) -> None:
        """Bucle principal de polling."""
        from sqlalchemy import select

        from src.infrastructure.persistence.models import ExtractoModel, TransaccionModel

        while self._running:
            try:
                async with self._service._session_factory() as session:
                    # Buscar extractos en PARSING o CLASSIFYING
                    stmt = select(ExtractoModel).where(
                        ExtractoModel.estado.in_(["PARSING", "CLASSIFYING"])
                    )
                    result = await session.execute(stmt)
                    extractos_pendientes = result.scalars().all()

                    for extracto in extractos_pendientes:
                        # Buscar transacciones sin clasificar en este extracto
                        txn_stmt = select(TransaccionModel).where(
                            TransaccionModel.extracto_id == extracto.id,
                            TransaccionModel.categoria_id.is_(None),
                        )
                        txn_result = await session.execute(txn_stmt)
                        transacciones = txn_result.scalars().all()

                        if transacciones:
                            transaction_ids = [t.id for t in transacciones]
                            logger.info(
                                "Polling: clasificando transacciones",
                                extract_id=str(extracto.id),
                                count=len(transaction_ids),
                            )
                            await self._service.process_extract(
                                extract_id=extracto.id,
                                transaction_ids=transaction_ids,
                                user_id=extracto.usuario_id,
                            )

            except Exception as e:
                logger.error(
                    "Error en polling loop",
                    exc_info=True,
                    error=str(e),
                )

            await asyncio.sleep(self._interval)


# ============================================================
# Entry point
# ============================================================

async def create_service() -> ClassificationService:
    """Crea el ClassificationService con la sesion de BD configurada."""
    from src.infrastructure.persistence.unit_of_work import create_session_factory

    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/finance_report",
    )
    session_factory = await create_session_factory(database_url)
    return ClassificationService(session_factory=session_factory)


async def main() -> None:
    """Entry point del worker de clasificacion."""
    # Determinar modo
    use_rabbitmq = os.getenv("RABBITMQ_ENABLED", "true").lower() in ("true", "1", "yes")
    rabbitmq_url = os.getenv("RABBITMQ_URL", RABBITMQ_DEFAULT_URL)

    logger.info("Iniciando Classification worker...")
    logger.info(f"Modo: {'RabbitMQ' if use_rabbitmq else 'Polling (fallback)'}")

    # Crear el servicio de clasificacion
    service = await create_service()

    # Iniciar worker segun modo
    if use_rabbitmq:
        worker = RabbitMQClassificationWorker(
            rabbitmq_url=rabbitmq_url,
            classification_service=service,
        )
        logger.info(f"RabbitMQ URL: {rabbitmq_url}")
    else:
        polling_interval = float(os.getenv("POLLING_INTERVAL", str(POLLING_INTERVAL_SECONDS)))
        worker = PollingClassificationWorker(
            service=service,
            interval_seconds=polling_interval,
        )

    # Manejar senales de shutdown gracefully
    shutdown_event = asyncio.Event()

    def _signal_handler(signum, frame):
        logger.info(f"Senal {signum} recibida, iniciando shutdown...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    try:
        await worker.start()
        # Esperar shutdown
        await shutdown_event.wait()
    except KeyboardInterrupt:
        logger.info("Worker detenido por el usuario")
    except Exception:
        logger.error("Error fatal en el worker", exc_info=True)
    finally:
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
