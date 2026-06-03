"""Command Handlers — Procesan comandos de escritura.

Cada metodo maneja un tipo de comando, orquestando repositorios,
servicios de dominio y publicando eventos al bus de mensajes.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from src.application.commands import (
    CargarExtractoCommand,
    ClasificarTransaccionCommand,
    ClasificarTransaccionesMasivasCommand,
    CorregirCategoriaCommand,
    CrearCategoriaCommand,
    CrearMetaAhorroCommand,
    CrearPresupuestoCommand,
)
from src.domain.entities.categoria import Categoria
from src.domain.entities.extracto import Extracto
from src.domain.entities.meta_ahorro import MetaAhorro
from src.domain.entities.presupuesto import Presupuesto
from src.domain.repositories import (
    ICategoriaRepository,
    IExtractoRepository,
    IPresupuestoRepository,
    ITransaccionRepository,
    IUsuarioRepository,
)

logger = logging.getLogger(__name__)


class CommandHandler:
    """Procesador de comandos de escritura (CQRS).

    Recibe las dependencias via inyeccion de dependencias (FastAPI Depends).
    Cada metodo procesa un comando especifico y retorna el resultado.
    """

    def __init__(
        self,
        extracto_repo: IExtractoRepository,
        transaccion_repo: ITransaccionRepository,
        categoria_repo: ICategoriaRepository,
        presupuesto_repo: IPresupuestoRepository,
        usuario_repo: IUsuarioRepository,
        event_bus: Any | None = None,
    ) -> None:
        self.extracto_repo = extracto_repo
        self.transaccion_repo = transaccion_repo
        self.categoria_repo = categoria_repo
        self.presupuesto_repo = presupuesto_repo
        self.usuario_repo = usuario_repo
        self.event_bus = event_bus

    async def handle_cargar_extracto(
        self, cmd: CargarExtractoCommand
    ) -> dict[str, Any]:
        """Procesa la carga de un extracto bancario.

        Registra el extracto en estado PENDING y publica el evento ExtractoCargado
        para que el worker de procesamiento lo procese asincronicamente.
        """
        extracto = Extracto(
            tarjeta_id=cmd.tarjeta_id,
            usuario_id=cmd.usuario_id,
            archivo_s3_key=f"extracts/{cmd.usuario_id}/{cmd.filename}",
        )
        events = extracto.iniciar_procesamiento()

        # Persistir extracto en estado PENDING
        await self.extracto_repo.save(extracto)

        # Publicar eventos al bus de mensajes
        if self.event_bus:
            for event in events:
                await self.event_bus.publish(event)

        logger.info(
            "Extracto registrado",
            extracto_id=str(extracto.id),
            usuario_id=str(cmd.usuario_id),
            filename=cmd.filename,
        )

        return {
            "extracto_id": str(extracto.id),
            "estado": extracto.estado.value,
            "progress_pct": extracto.progress_pct,
        }

    async def handle_clasificar_transaccion(
        self, cmd: ClasificarTransaccionCommand
    ) -> dict[str, Any]:
        """Clasifica una transaccion individual con el motor hibrido."""
        transaccion = await self.transaccion_repo.get_by_id(cmd.transaccion_id)
        if not transaccion:
            raise ValueError(f"Transaccion {cmd.transaccion_id} no encontrada")

        # Obtener categorias y clasificar
        categorias = await self.categoria_repo.get_all(cmd.usuario_id)
        # La clasificacion real se delega al motor de clasificacion (infraestructura)
        # Aqui solo se actualiza el estado

        return {
            "transaccion_id": str(transaccion.id),
            "categoria_id": str(transaccion.categoria_id) if transaccion.categoria_id else None,
        }

    async def handle_clasificacion_masiva(
        self, cmd: ClasificarTransaccionesMasivasCommand
    ) -> dict[str, Any]:
        """Asigna la misma categoria a multiples transacciones."""
        updated = await self.transaccion_repo.bulk_update_category(
            cmd.transaccion_ids, cmd.categoria_id
        )

        # Publicar eventos de aprendizaje
        if self.event_bus:
            for tid in cmd.transaccion_ids:
                from src.domain.events import CategoriaCorregida
                event = CategoriaCorregida(
                    transaction_id=tid,
                    categoria_nueva=cmd.categoria_id,
                )
                await self.event_bus.publish(event)

        logger.info(
            "Clasificacion masiva completada",
            count=updated,
            usuario_id=str(cmd.usuario_id),
        )

        return {"updated_count": updated}

    async def handle_corregir_categoria(
        self, cmd: CorregirCategoriaCommand
    ) -> dict[str, Any]:
        """Corrige la categoria de una transaccion (aprendizaje supervisado)."""
        transaccion = await self.transaccion_repo.get_by_id(cmd.transaccion_id)
        if not transaccion:
            raise ValueError(f"Transaccion {cmd.transaccion_id} no encontrada")

        events = transaccion.corregir_categoria(cmd.categoria_id)
        await self.transaccion_repo.save(transaccion)

        # Publicar evento para reentrenar modelo ML
        if self.event_bus:
            for event in events:
                await self.event_bus.publish(event)

        return {
            "transaccion_id": str(transaccion.id),
            "categoria_id": str(transaccion.categoria_id),
            "confidence": float(transaccion.confidence) if transaccion.confidence else 100.0,
        }

    async def handle_crear_categoria(
        self, cmd: CrearCategoriaCommand
    ) -> dict[str, Any]:
        """Crea una categoria o subcategoria personalizada."""
        categoria = Categoria(
            nombre=cmd.nombre,
            icono=cmd.icono,
            color=cmd.color,
            parent_id=cmd.parent_id,
            usuario_id=cmd.usuario_id,
            es_predefinida=False,
        )
        saved = await self.categoria_repo.save(categoria)
        return {"id": str(saved.id), "nombre": saved.nombre}

    async def handle_crear_presupuesto(
        self, cmd: CrearPresupuestoCommand
    ) -> dict[str, Any]:
        """Crea un presupuesto mensual por categoria."""
        if cmd.limite_mensual <= 0:
            raise ValueError("El limite mensual debe ser mayor a 0")

        presupuesto = Presupuesto(
            usuario_id=cmd.usuario_id,
            categoria_id=cmd.categoria_id,
            limite_mensual=cmd.limite_mensual,
            alerta_80pct=cmd.alerta_80pct,
            alerta_100pct=cmd.alerta_100pct,
        )
        saved = await self.presupuesto_repo.save(presupuesto)
        return {"id": str(saved.id), "limite_mensual": str(saved.limite_mensual)}

    async def handle_crear_meta(
        self, cmd: CrearMetaAhorroCommand
    ) -> dict[str, Any]:
        """Crea una meta de ahorro."""
        if cmd.monto_objetivo <= 0:
            raise ValueError("El monto objetivo debe ser mayor a 0")

        meta = MetaAhorro(
            usuario_id=cmd.usuario_id,
            nombre=cmd.nombre,
            monto_objetivo=cmd.monto_objetivo,
            fecha_deseada=cmd.fecha_deseada,
        )
        # Nota: El repositorio de meta ahorro se implementaria en infraestructura
        return {"id": str(meta.id), "nombre": meta.nombre, "monto_objetivo": str(meta.monto_objetivo)}
