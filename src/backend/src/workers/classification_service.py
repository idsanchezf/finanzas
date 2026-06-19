"""ClassificationService — Orquestacion de clasificacion de transacciones.

Logica pura de aplicacion (sin dependencias de infraestructura como RabbitMQ).
Es la capa de aplicacion que coordina el clasificador de reglas deterministicas
con los repositorios de BD para clasificar transacciones de un extracto.

Responsabilidades:
1. Obtener categorias disponibles (predefinidas + personalizadas)
2. Para cada transaccion: ejecutar ClasificadorReglas.clasificar()
3. Persistir categoria_id + confidence en BD
4. Si confidence < 70%, marcar para revision (flag de baja confianza)
5. Actualizar estado del extracto (CLASSIFYING → COMPLETED)
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.domain.entities.categoria import Categoria
from src.infrastructure.excel.clasificador_reglas import ClasificadorReglas
from src.infrastructure.persistence.repositories.categoria_repo import CategoriaRepository
from src.infrastructure.persistence.repositories.extracto_repo import ExtractoRepository
from src.infrastructure.persistence.repositories.transaccion_repo import TransaccionRepository

logger = logging.getLogger(__name__)


class ClassificationService:
    """Servicio de aplicacion para clasificar transacciones de un extracto.

    Orquesta el pipeline de clasificacion:
    1. Carga categorias y el extracto
    2. Para cada transaccion, ejecuta el clasificador de reglas
    3. Persiste los resultados y actualiza el progreso del extracto
    """

    # Umbral de confianza para marcar como "baja" — requiere revision del usuario
    LOW_CONFIDENCE_THRESHOLD = Decimal("70.00")

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        clasificador: ClasificadorReglas | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._clasificador = clasificador or ClasificadorReglas()

        # Repositorios se crean con la sesion activa
        self._transaccion_repo: TransaccionRepository | None = None
        self._categoria_repo: CategoriaRepository | None = None
        self._extracto_repo: ExtractoRepository | None = None

    # ============================================================
    # Metodo principal: procesar un extracto completo
    # ============================================================

    async def process_extract(
        self,
        extract_id: UUID,
        transaction_ids: list[UUID],
        user_id: UUID,
    ) -> list[dict[str, Any]]:
        """Clasifica todas las transacciones de un extracto.

        Args:
            extract_id: ID del extracto a procesar.
            transaction_ids: Lista de IDs de transacciones a clasificar.
            user_id: ID del usuario propietario.

        Returns:
            Lista de resultados: [{"transaction_id", "category_id", "confidence", "source"}]
        """
        results: list[dict[str, Any]] = []

        async with self._session_factory() as session:
            self._transaccion_repo = TransaccionRepository(session)
            self._categoria_repo = CategoriaRepository(session)
            self._extracto_repo = ExtractoRepository(session)

            # 1. Cargar categorias (predefinidas + personalizadas del usuario)
            categoria_models = await self._categoria_repo.get_all(usuario_id=user_id)
            categorias_dominio = [
                Categoria(
                    id=m.id,
                    nombre=m.nombre,
                    icono=m.icono,
                    color=m.color,
                    parent_id=m.parent_id,
                    es_predefinida=m.es_predefinida,
                    usuario_id=m.usuario_id,
                    palabras_clave=m.palabras_clave or [],
                )
                for m in categoria_models
            ]

            logger.info(
                "Categorias cargadas para clasificacion: count=%d extract_id=%s",
                len(categorias_dominio),
                str(extract_id),
            )

            # 2. Cargar el extracto y marcarlo como CLASSIFYING
            extracto_model = await self._extracto_repo.get_by_id(extract_id)
            if extracto_model is None:
                logger.error("Extracto no encontrado: %s", str(extract_id))
                return results

            extracto_model.estado = "CLASSIFYING"
            extracto_model.progress_pct = 70
            await self._extracto_repo.save(extracto_model)

            # 3. Clasificar cada transaccion
            total = len(transaction_ids)
            classified_count = 0

            for idx, txn_id in enumerate(transaction_ids):
                txn_model = await self._transaccion_repo.get_by_id(txn_id)
                if txn_model is None:
                    logger.warning(
                        "Transaccion no encontrada, omitiendo: %s",
                        str(txn_id),
                    )
                    continue

                # Ejecutar clasificador de reglas
                categoria_id, confidence, source = self._clasificar_comercio(
                    comercio=txn_model.comercio_original,
                    categorias=categorias_dominio,
                )

                # Actualizar modelo con el resultado
                txn_model.categoria_id = categoria_id
                txn_model.confidence = Decimal(str(round(confidence, 2)))

                await self._transaccion_repo.save(txn_model)

                if categoria_id is not None:
                    classified_count += 1

                results.append({
                    "transaction_id": txn_id,
                    "category_id": categoria_id,
                    "confidence": Decimal(str(round(confidence, 2))),
                    "source": source,
                })

                # 4. Actualizar progreso periodicamente
                if (idx + 1) % 10 == 0 or (idx + 1) == total:
                    progress = 70 + int(30 * (idx + 1) / total)
                    extracto_model.progress_pct = min(100, progress)
                    await self._extracto_repo.save(extracto_model)

            # 5. Marcar extracto como completado
            extracto_model.estado = "COMPLETED"
            extracto_model.progress_pct = 100
            await self._extracto_repo.save(extracto_model)

            await session.commit()

            logger.info(
                "Clasificacion completada: extract_id=%s total=%d classified=%d unclassified=%d",
                str(extract_id), total, classified_count, total - classified_count,
            )

        return results

    # ============================================================
    # Clasificacion individual
    # ============================================================

    async def classify_single(
        self,
        transaction_id: UUID,
        user_id: UUID,
    ) -> dict[str, Any] | None:
        """Clasifica una sola transaccion.

        Args:
            transaction_id: ID de la transaccion a clasificar.
            user_id: ID del usuario propietario.

        Returns:
            Resultado: {"transaction_id", "category_id", "confidence", "source"}
            o None si la transaccion no existe.
        """
        async with self._session_factory() as session:
            self._transaccion_repo = TransaccionRepository(session)
            self._categoria_repo = CategoriaRepository(session)

            txn_model = await self._transaccion_repo.get_by_id(transaction_id)
            if txn_model is None:
                logger.warning(
                    "Transaccion no encontrada: %s",
                    str(transaction_id),
                )
                return None

            categoria_models = await self._categoria_repo.get_all(usuario_id=user_id)
            categorias_dominio = [
                Categoria(
                    id=m.id,
                    nombre=m.nombre,
                    icono=m.icono,
                    color=m.color,
                    parent_id=m.parent_id,
                    es_predefinida=m.es_predefinida,
                    usuario_id=m.usuario_id,
                    palabras_clave=m.palabras_clave or [],
                )
                for m in categoria_models
            ]

            categoria_id, confidence, source = self._clasificar_comercio(
                comercio=txn_model.comercio_original,
                categorias=categorias_dominio,
            )

            txn_model.categoria_id = categoria_id
            txn_model.confidence = Decimal(str(round(confidence, 2)))

            await self._transaccion_repo.save(txn_model)
            await session.commit()

            return {
                "transaction_id": transaction_id,
                "category_id": categoria_id,
                "confidence": Decimal(str(round(confidence, 2))),
                "source": source,
            }

    # ============================================================
    # Helpers
    # ============================================================

    def _clasificar_comercio(
        self,
        comercio: str,
        categorias: list[Categoria],
    ) -> tuple[UUID | None, float, str]:
        """Ejecuta el pipeline de clasificacion hibrida.

        Args:
            comercio: Nombre original del comercio.
            categorias: Lista de entidades Categoria con palabras_clave.

        Returns:
            Tupla (categoria_id, confidence, source).
        """
        cat_id, confidence, source = self._clasificador.clasificar(
            comercio=comercio,
            categorias=categorias,
            historial=[],  # ML no implementado en MVP
        )
        return cat_id, confidence, source

    # ============================================================
    # Helpers derivados
    # ============================================================

    def is_low_confidence(self, confidence: Decimal | float) -> bool:
        """True si la confianza es baja y requiere revision del usuario."""
        conf = Decimal(str(confidence)) if not isinstance(confidence, Decimal) else confidence
        return conf < self.LOW_CONFIDENCE_THRESHOLD
