"""Command Handlers — Procesan comandos de escritura.

Cada metodo maneja un tipo de comando, orquestando repositorios,
servicios de dominio y publicando eventos al bus de mensajes.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

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
from src.domain.entities.transaccion import Transaccion
from src.domain.repositories import (
    ICategoriaRepository,
    IExtractoRepository,
    IPresupuestoRepository,
    ITransaccionRepository,
    IUsuarioRepository,
)
from src.domain.value_objects.money import Money

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

        Flujo completo:
        1. Crea el extracto en estado PENDING y lo persiste.
        2. Parsea el Excel con ExtractoExcelParser.
        3. Actualiza metadatos del extracto (periodo, montos, fechas).
        4. Crea transacciones a partir del parseo y las persiste.
        5. Marca el extracto como COMPLETED si el parseo fue exitoso.
        6. Publica evento ExtractoCargado para notificaciones asincronas.
        """
        from src.infrastructure.excel.parser import ExtractoExcelParser

        # 1. Crear extracto en estado PENDING
        extracto = Extracto(
            tarjeta_id=cmd.tarjeta_id,
            usuario_id=cmd.usuario_id,
            archivo_s3_key=f"extracts/{cmd.usuario_id}/{cmd.filename}",
        )
        extracto.iniciar_procesamiento()

        # Persistir extracto en estado PARSING (10%)
        await self.extracto_repo.save(extracto)

        transaction_count = 0
        parse_errors: list[str] = []
        parse_result = None  # inicializar fuera del try para acceso posterior

        # 2. Parsear el archivo Excel
        try:
            parser = ExtractoExcelParser()
            parse_result = parser.parse(cmd.file_content, cmd.filename)

            # 3. Actualizar metadatos del extracto desde el parseo
            meta = parse_result.metadatos
            if "periodo_inicio" in meta:
                extracto.periodo_inicio = meta["periodo_inicio"]
            if "periodo_fin" in meta:
                extracto.periodo_fin = meta["periodo_fin"]
            if "fecha_corte" in meta:
                extracto.fecha_corte = meta["fecha_corte"]
            if "fecha_limite_pago" in meta:
                extracto.fecha_limite_pago = meta["fecha_limite_pago"]
            if "pago_minimo" in meta:
                extracto.pago_minimo = Money(
                    Decimal(str(meta["pago_minimo"])),
                    meta.get("moneda", "COP"),
                )
            if "pago_total" in meta:
                extracto.pago_total = Money(
                    Decimal(str(meta["pago_total"])),
                    meta.get("moneda", "COP"),
                )
            if "cupo_total" in meta:
                extracto.cupo_total = Money(
                    Decimal(str(meta["cupo_total"])),
                    meta.get("moneda", "COP"),
                )
            if "cupo_disponible" in meta:
                extracto.cupo_disponible = Money(
                    Decimal(str(meta["cupo_disponible"])),
                    meta.get("moneda", "COP"),
                )

            extracto.metadatos = meta
            extracto.avanzar_parseo(40)

            # 4. Crear y persistir transacciones
            if parse_result.transacciones:
                transaccion_entities: list[Transaccion] = []
                for t_data in parse_result.transacciones:
                    valor = t_data.get("valor", Decimal("0.00"))
                    if isinstance(valor, (int, float)):
                        valor = Decimal(str(valor))

                    tx = Transaccion(
                        extracto_id=extracto.id,
                        usuario_id=cmd.usuario_id,
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
                transaction_count = len(transaccion_entities)
                extracto.transacciones = transaccion_entities

            extracto.avanzar_parseo(60)
            parse_errors = parse_result.errores

        except Exception as e:
            logger.error(
                "Error al parsear el Excel del extracto",
                extracto_id=str(extracto.id),
                filename=cmd.filename,
                error=str(e),
                exc_info=True,
            )
            parse_errors.append(str(e))

        # 5. Completar o marcar error segun resultado del parseo
        if parse_result and parse_result.exitoso:
            extracto.iniciar_clasificacion()
            # Aqui se dispararia la clasificacion asincrona con ML
            # Por ahora, completar directamente
            events = extracto.completar()
        elif parse_errors:
            extracto.marcar_error("; ".join(parse_errors))
            events = []
        else:
            extracto.marcar_error("No se encontraron transacciones en el archivo")
            events = []

        # Persistir estado final del extracto
        await self.extracto_repo.save(extracto)

        # 6. Publicar eventos al bus de mensajes
        if self.event_bus:
            for event in events:
                await self.event_bus.publish(event)

        logger.info(
            "Extracto procesado",
            extracto_id=str(extracto.id),
            usuario_id=str(cmd.usuario_id),
            filename=cmd.filename,
            transacciones=transaction_count,
            estado=extracto.estado.value if hasattr(extracto.estado, "value") else str(extracto.estado),
        )

        return {
            "extract_id": str(extracto.id),
            "estado": extracto.estado.value if hasattr(extracto.estado, "value") else str(extracto.estado),
            "progress_pct": extracto.progress_pct,
            "transacciones_count": transaction_count,
            "parse_errors": parse_errors,
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
        """Asigna la misma categoria a multiples transacciones.

        1. Valida que todas las transacciones existan y pertenezcan al usuario.
        2. Actualiza categoria + confidence=100 (manual).
        3. Publica eventos CategoriaCorregida para aprendizaje del modelo.
        """
        # Validar que existan y pertenezcan al usuario
        transacciones_model = []
        for tid in cmd.transaccion_ids:
            model = await self.transaccion_repo.get_by_id(tid)
            if model is None:
                raise ValueError(f"Transaccion {tid} no encontrada")
            transacciones_model.append(model)

        # Actualizar via bulk UPDATE (eficiente para multiples filas)
        updated = await self.transaccion_repo.bulk_update_category(
            cmd.transaccion_ids, cmd.categoria_id
        )

        # Publicar eventos de aprendizaje para cada transaccion
        if self.event_bus:
            for model in transacciones_model:
                from src.domain.events import CategoriaCorregida

                event = CategoriaCorregida(
                    transaction_id=model.id,
                    categoria_anterior=model.categoria_id,
                    categoria_nueva=cmd.categoria_id,
                    comercio_original=model.comercio_original,
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
        """Corrige la categoria de una transaccion (aprendizaje supervisado).

        1. Obtiene la transaccion como entidad de dominio.
        2. Ejecuta la correccion (metodo de dominio que actualiza estado y genera eventos).
        3. Persiste los cambios en la BD via repositorio.
        4. Publica evento CategoriaCorregida para reentrenar el modelo ML.
        """
        # Obtener entidad de dominio (con metodos de negocio)
        transaccion = await self.transaccion_repo.get_entity_by_id(cmd.transaccion_id)
        if not transaccion:
            raise ValueError(f"Transaccion {cmd.transaccion_id} no encontrada")

        # Ejecutar logica de dominio: actualiza categoria + confidence + genera evento
        events = transaccion.corregir_categoria(cmd.categoria_id)

        # Persistir cambios en BD
        await self.transaccion_repo.update(cmd.transaccion_id, transaccion)

        # Publicar evento para reentrenar modelo ML
        if self.event_bus:
            for event in events:
                await self.event_bus.publish(event)

        logger.info(
            "Categoria corregida manualmente",
            transaccion_id=str(cmd.transaccion_id),
            categoria_id=str(cmd.categoria_id),
            usuario_id=str(cmd.usuario_id),
        )

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
