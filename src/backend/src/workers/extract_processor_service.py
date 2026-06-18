"""Servicio de procesamiento de extractos bancarios.

Orquesta el flujo asincrono de procesamiento de un extracto:
1. Carga el extracto desde BD y actualiza su estado
2. Descarga el archivo Excel desde R2 (o usa contenido inline)
3. Parsea con ExtractoExcelParser
4. Persiste transacciones y actualiza metadatos
5. Publica eventos de dominio (ExtractoProcesado → transactions.new)
6. Maneja errores marcando el extracto como ERROR + DLQ
"""

from __future__ import annotations

import base64
import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from src.domain.entities.extracto import EstadoExtracto
from src.domain.entities.transaccion import Transaccion
from src.domain.events import ExtractoProcesado
from src.domain.value_objects.money import Money
from src.infrastructure.excel.parser import ExtractoExcelParser, ExtractoParseado

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Tipos
# ------------------------------------------------------------------

@dataclass
class ExtractMessage:
    """Mensaje recibido de la cola extract.uploaded / extractos.procesar.

    Soporta dos modos de entrega del archivo:
    - file_key: key en R2/S3 para descargar
    - file_content_b64: contenido base64 inline (fallback/testing)
    """

    tracking_id: UUID
    file_key: str | None = None
    card_id: UUID | None = None
    user_id: UUID | None = None
    file_content_b64: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExtractMessage":
        """Construye desde el dict recibido en el mensaje de RabbitMQ.

        Soporta multiples convenciones de nombres:
        - tracking_id / extracto_id
        - file_key / s3_key
        - card_id / tarjeta_id
        - user_id / usuario_id
        """
        tracking_id = data.get("tracking_id") or data.get("extracto_id")
        file_key = data.get("file_key") or data.get("s3_key")
        card_id = data.get("card_id") or data.get("tarjeta_id")
        user_id = data.get("user_id") or data.get("usuario_id")
        file_content_b64 = data.get("file_content_b64") or data.get("file_content")

        return cls(
            tracking_id=UUID(str(tracking_id)) if tracking_id else None,
            file_key=str(file_key) if file_key else None,
            card_id=UUID(str(card_id)) if card_id else None,
            user_id=UUID(str(user_id)) if user_id else None,
            file_content_b64=str(file_content_b64) if file_content_b64 else None,
        )


@dataclass
class ProcessResult:
    """Resultado del procesamiento de un extracto."""

    extracto_id: UUID
    estado: str
    transaction_count: int
    parse_errors: list[str]
    progress_pct: int
    success: bool


# ------------------------------------------------------------------
# Servicio
# ------------------------------------------------------------------

class ExtractProcessorService:
    """Servicio de procesamiento de extractos.

    Encapsula la logica de negocio del worker: descarga, parseo,
    persistencia y publicacion de eventos.

    Las dependencias (repos, storage, event_bus) se inyectan para
    permitir testing unitario con mocks.
    """

    def __init__(
        self,
        extracto_repo: Any = None,
        transaccion_repo: Any = None,
        storage: Any = None,
        event_bus: Any = None,
    ) -> None:
        self.extracto_repo = extracto_repo
        self.transaccion_repo = transaccion_repo
        self.storage = storage
        self.event_bus = event_bus

    async def process(
        self,
        msg: ExtractMessage,
        parser: ExtractoExcelParser | None = None,
    ) -> ProcessResult:
        """Procesa un extracto desde el mensaje hasta la publicacion de eventos.

        Args:
            msg: Mensaje con tracking_id, file_key, etc.
            parser: Instancia de ExtractoExcelParser (inyectable para testing).

        Returns:
            ProcessResult con el resultado del procesamiento.
        """
        extracto_id = msg.tracking_id
        parser = parser or ExtractoExcelParser()

        logger.info(
            "Iniciando procesamiento de extracto extracto_id=%s file_key=%s user_id=%s",
            extracto_id,
            msg.file_key,
            str(msg.user_id) if msg.user_id else None,
        )

        # 1. Cargar extracto desde BD
        extracto = await self.extracto_repo.get_by_id(extracto_id)
        if extracto is None:
            raise ValueError(f"Extracto {extracto_id} no encontrado en BD")

        # Actualizar estado → PARSING
        if hasattr(extracto, "estado"):
            if hasattr(extracto.estado, "value"):
                extracto.estado = EstadoExtracto.PARSING
            else:
                extracto.estado = "PARSING"
        if hasattr(extracto, "progress_pct"):
            extracto.progress_pct = 10

        await self.extracto_repo.save(extracto)
        await self._flush()

        # 2. Obtener el contenido del archivo Excel
        try:
            file_content, filename = await self._obtener_contenido(msg, extracto)
        except Exception as e:
            logger.error(
                "Error al descargar/obtener el archivo Excel extracto_id=%s error=%s",
                extracto_id,
                str(e),
                exc_info=True,
            )
            await self._marcar_error(extracto, f"Error al obtener archivo: {str(e)}")
            return ProcessResult(
                extracto_id=extracto_id,
                estado="ERROR",
                transaction_count=0,
                parse_errors=[f"Error al obtener archivo: {str(e)}"],
                progress_pct=0,
                success=False,
            )

        # 3. Parsear el Excel
        parse_result = parser.parse(file_content, filename)

        # 4. Actualizar metadatos del extracto desde el parseo
        meta = parse_result.metadatos
        self._actualizar_metadatos(extracto, meta)

        if hasattr(extracto, "progress_pct"):
            extracto.progress_pct = 40
        await self.extracto_repo.save(extracto)
        await self._flush()

        # 5. Crear y persistir transacciones
        transaction_count = 0
        transaccion_ids: list[UUID] = []

        if parse_result.transacciones:
            transaccion_entities: list[Transaccion] = []
            usuario_id = msg.user_id or (
                extracto.usuario_id if hasattr(extracto, "usuario_id") else None
            )

            for t_data in parse_result.transacciones:
                valor = t_data.get("valor", Decimal("0.00"))
                if isinstance(valor, (int, float)):
                    valor = Decimal(str(valor))

                tx = Transaccion(
                    extracto_id=extracto_id,
                    usuario_id=usuario_id or extracto_id,  # fallback
                    numero_autorizacion=t_data.get("numero_autorizacion"),
                    fecha=t_data.get("fecha"),
                    comercio_original=t_data.get("comercio_original", ""),
                    valor=valor,
                    numero_cuotas=t_data.get("numero_cuotas"),
                    cuotas_totales=t_data.get("cuotas_totales"),
                    cuota_actual=t_data.get("cuota_actual"),
                    moneda_original=t_data.get("moneda_original"),
                    valor_moneda_original=(
                        Decimal(str(t_data["valor_moneda_original"]))
                        if t_data.get("valor_moneda_original") is not None
                        else None
                    ),
                    es_cuota=t_data.get("es_cuota", False),
                )
                transaccion_entities.append(tx)

            await self.transaccion_repo.bulk_save(transaccion_entities)
            await self._flush()
            transaction_count = len(transaccion_entities)
            transaccion_ids = [tx.id for tx in transaccion_entities]

        # 6. Actualizar estado del extracto
        #    Flujo: PARSING → CLASSIFYING (este worker parsea y deja listo para clasificar)
        #    El ClassificationWorker se encarga de CLASSIFYING → COMPLETED
        if parse_result.exitoso:
            if hasattr(extracto, "estado"):
                if hasattr(extracto.estado, "value"):
                    extracto.estado = EstadoExtracto.CLASSIFYING
                else:
                    extracto.estado = "CLASSIFYING"
            if hasattr(extracto, "progress_pct"):
                extracto.progress_pct = 70
            success = True
        elif parse_result.errores:
            error_msg = "; ".join(parse_result.errores)
            await self._marcar_error(extracto, error_msg)
            success = False
        else:
            await self._marcar_error(extracto, "No se encontraron transacciones en el archivo")
            success = False

        await self.extracto_repo.save(extracto)
        await self._flush()

        # 7. Publicar eventos
        if success and self.event_bus:
            try:
                # Publicar ExtractoProcesado → enruta a extractos.clasificar
                # Este es el evento transactions.new del diseno arquitectonico
                usuario_id_actual = msg.user_id or (
                    extracto.usuario_id if hasattr(extracto, "usuario_id") else None
                )
                tarjeta_id_actual = msg.card_id or (
                    extracto.tarjeta_id if hasattr(extracto, "tarjeta_id") else None
                )

                event = ExtractoProcesado(
                    extracto_id=extracto_id,
                    usuario_id=usuario_id_actual or extracto_id,
                    tarjeta_id=tarjeta_id_actual or extracto_id,
                    transaction_count=transaction_count,
                )
                await self.event_bus.publish(event)
                logger.info(
                    "Evento ExtractoProcesado publicado (transactions.new) extracto_id=%s transaction_count=%d",
                    extracto_id,
                    transaction_count,
                )
            except Exception as e:
                logger.error(
                    "Error al publicar evento ExtractoProcesado extracto_id=%s error=%s",
                    extracto_id,
                    str(e),
                    exc_info=True,
                )
                # No fallamos el procesamiento por error en publicacion de evento
                # El extracto ya esta procesado y persistido

        logger.info(
            "Procesamiento de extracto finalizado extracto_id=%s estado=%s transacciones=%d errores=%d",
            extracto_id,
            "CLASSIFYING" if success else "ERROR",
            transaction_count,
            len(parse_result.errores),
        )

        return ProcessResult(
            extracto_id=extracto_id,
            estado="CLASSIFYING" if success else "ERROR",
            transaction_count=transaction_count,
            parse_errors=parse_result.errores,
            progress_pct=70 if success else 0,
            success=success,
        )

    # ============================================================
    # Helpers privados
    # ============================================================

    async def _obtener_contenido(
        self, msg: ExtractMessage, extracto: Any
    ) -> tuple[bytes, str]:
        """Obtiene el contenido binario del archivo Excel.

        Prioridad:
        1. file_content_b64 inline en el mensaje
        2. Descarga desde R2/S3 via file_key
        3. Usa archivo_s3_key del extracto como fallback

        Returns:
            Tuple de (bytes_del_archivo, nombre_del_archivo).
        """
        # Opcion 1: contenido inline base64
        if msg.file_content_b64:
            logger.debug("Usando file_content inline (base64)")
            return base64.b64decode(msg.file_content_b64), "extracto_inline.xlsx"

        # Opcion 2: file_key del mensaje
        file_key = msg.file_key
        if not file_key and hasattr(extracto, "archivo_s3_key"):
            file_key = extracto.archivo_s3_key

        if not file_key:
            raise ValueError(
                "No se encontro file_key en el mensaje ni archivo_s3_key en el extracto"
            )

        if self.storage is None:
            raise RuntimeError(
                "Se requiere R2Storage para descargar el archivo, pero no fue inyectado. "
                "Use file_content_b64 en el mensaje o configure R2."
            )

        # Descargar de R2 (sync, ejecutar en thread para no bloquear)
        bucket = "finance-extracts"
        logger.info(f"Descargando archivo de R2: {bucket}/{file_key}")

        content = await self._download_async(bucket, file_key)
        filename = file_key.split("/")[-1] if "/" in file_key else file_key
        return content, filename

    async def _download_async(self, bucket: str, key: str) -> bytes:
        """Descarga archivo de R2 de forma async (boto3 es sync)."""
        import asyncio

        return await asyncio.to_thread(self.storage.download_file, bucket, key)

    def _actualizar_metadatos(self, extracto: Any, meta: dict[str, Any]) -> None:
        """Actualiza los metadatos del extracto desde el resultado del parseo."""
        if "periodo_inicio" in meta:
            extracto.periodo_inicio = meta["periodo_inicio"]
        if "periodo_fin" in meta:
            extracto.periodo_fin = meta["periodo_fin"]
        if "fecha_corte" in meta:
            extracto.fecha_corte = meta["fecha_corte"]
        if "fecha_limite_pago" in meta:
            extracto.fecha_limite_pago = meta["fecha_limite_pago"]
        if "pago_minimo" in meta:
            try:
                extracto.pago_minimo = Money(
                    Decimal(str(meta["pago_minimo"])),
                    meta.get("moneda", "COP"),
                )
            except Exception:
                logger.warning("No se pudo parsear pago_minimo value=%s", meta.get("pago_minimo"))
        if "pago_total" in meta:
            try:
                extracto.pago_total = Money(
                    Decimal(str(meta["pago_total"])),
                    meta.get("moneda", "COP"),
                )
            except Exception:
                logger.warning("No se pudo parsear pago_total value=%s", meta.get("pago_total"))
        if "cupo_total" in meta:
            try:
                extracto.cupo_total = Money(
                    Decimal(str(meta["cupo_total"])),
                    meta.get("moneda", "COP"),
                )
            except Exception:
                logger.warning("No se pudo parsear cupo_total value=%s", meta.get("cupo_total"))
        if "cupo_disponible" in meta:
            try:
                extracto.cupo_disponible = Money(
                    Decimal(str(meta["cupo_disponible"])),
                    meta.get("moneda", "COP"),
                )
            except Exception:
                logger.warning("No se pudo parsear cupo_disponible value=%s", meta.get("cupo_disponible"))

        if hasattr(extracto, "metadatos"):
            extracto.metadatos = meta

    async def _marcar_error(self, extracto: Any, mensaje: str) -> None:
        """Marca el extracto en estado ERROR y persiste."""
        if hasattr(extracto, "estado"):
            if hasattr(extracto.estado, "value"):
                extracto.estado = EstadoExtracto.ERROR
            else:
                extracto.estado = "ERROR"
        if hasattr(extracto, "error_message"):
            extracto.error_message = mensaje
        if hasattr(extracto, "progress_pct"):
            extracto.progress_pct = 0

        await self.extracto_repo.save(extracto)
        await self._flush()

        logger.error(
            "Extracto marcado como ERROR extracto_id=%s error=%s",
            str(getattr(extracto, "id", "unknown")),
            mensaje,
        )

    async def _flush(self) -> None:
        """Flush de cambios pendientes si el repositorio lo soporta."""
        if hasattr(self.extracto_repo, "session") and hasattr(
            self.extracto_repo.session, "flush"
        ):
            await self.extracto_repo.session.flush()
