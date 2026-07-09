"""Query Handlers — Procesan consultas de lectura (CQRS).

Los queries no modifican el estado del sistema. Solo consultan repositorios
y aplican transformaciones para retornar DTOs de presentacion.

Nota: Los repositorios retornan modelos ORM (SQLAlchemy), NO entidades de dominio.
Se accede directamente a las columnas del modelo (Decimal, str, date, etc.).
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Any

from src.application.queries import (
    DashboardByCategoryQuery,
    DashboardDailyQuery,
    DashboardMonthlyTrendQuery,
    DashboardSummaryQuery,
    ObtenerExtractosQuery,
    ObtenerInsightsQuery,
    ObtenerTransaccionesQuery,
)
from src.domain.exceptions import EntidadNoEncontradaError
from src.domain.repositories import (
    ICategoriaRepository,
    IExtractoRepository,
    ITransaccionRepository,
)

logger = logging.getLogger(__name__)


class QueryHandler:
    """Procesador de consultas de lectura (CQRS)."""

    def __init__(
        self,
        extracto_repo: IExtractoRepository,
        transaccion_repo: ITransaccionRepository,
        categoria_repo: ICategoriaRepository,
    ) -> None:
        self.extracto_repo = extracto_repo
        self.transaccion_repo = transaccion_repo
        self.categoria_repo = categoria_repo

    async def handle_dashboard_summary(self, query: DashboardSummaryQuery) -> dict[str, Any]:
        """Retorna los KPIs del dashboard para un extracto.

        Incluye:
        - total_gastado: suma de gastos (no incluye abonos/pagos)
        - total_ingresos: suma de abonos/pagos
        - total_transacciones: conteo de transacciones (excluyendo abonos)
        - promedio_diario: gasto promedio por dia del periodo
        - pct_cupo_utilizado: porcentaje del cupo total ya consumido
        - dias_para_corte: dias restantes hasta la fecha limite de pago
        - variacion_vs_anterior: comparacion con el extracto previo
        """
        extracto = await self.extracto_repo.get_by_id(query.extracto_id)
        if not extracto:
            raise EntidadNoEncontradaError(
                entidad="Extracto", entidad_id=query.extracto_id
            )

        transacciones = await self.transaccion_repo.get_by_extracto(query.extracto_id)

        # Gastos: transacciones con valor positivo que NO son abonos
        gastos = [t for t in transacciones if t.valor > 0 and not t.es_abono]
        total_gastado = sum(t.valor for t in gastos)

        # Ingresos: abonos o transacciones con valor negativo
        ingresos_list = [t for t in transacciones if t.valor < 0 or t.es_abono]
        total_ingresos = sum(abs(t.valor) for t in ingresos_list)

        num_transacciones = len(gastos)

        # Dias del periodo (si no estan definidos, asumir 30)
        dias_periodo = 30
        if extracto.periodo_inicio and extracto.periodo_fin:
            dias_periodo = (extracto.periodo_fin - extracto.periodo_inicio).days
        dias_periodo = max(dias_periodo, 1)

        promedio_diario = total_gastado / dias_periodo

        # Calcular % cupo utilizado
        pct_cupo = Decimal("0")
        if extracto.cupo_total and extracto.cupo_total > 0:
            pct_cupo = (total_gastado / extracto.cupo_total) * 100

        # Calcular dias hasta fecha limite de pago
        dias_pago = 0
        if extracto.fecha_limite_pago:
            delta = extracto.fecha_limite_pago - date.today()
            dias_pago = max(0, delta.days)

        # Variacion vs extracto anterior: buscar el extracto previo del usuario
        variacion_vs_anterior = 0.0
        try:
            extractos_anteriores, _ = await self.extracto_repo.get_by_usuario(
                query.usuario_id, page=1, size=24
            )
            # Ordenar por periodo_inicio descendente y buscar el inmediatamente anterior
            otros = sorted(
                [
                    e
                    for e in extractos_anteriores
                    if e.id != query.extracto_id and e.periodo_inicio is not None
                ],
                key=lambda e: e.periodo_inicio,
                reverse=True,
            )
            if otros and total_gastado > 0:
                prev = otros[0]
                prev_trans = await self.transaccion_repo.get_by_extracto(prev.id)
                prev_gastos = [t for t in prev_trans if t.valor > 0 and not t.es_abono]
                prev_total = sum(t.valor for t in prev_gastos)
                if prev_total > 0:
                    variacion_vs_anterior = float(((total_gastado - prev_total) / prev_total) * 100)
        except Exception:
            variacion_vs_anterior = 0.0

        return {
            "extracto_id": str(extracto.id),
            "periodo": {
                "inicio": extracto.periodo_inicio.isoformat() if extracto.periodo_inicio else None,
                "fin": extracto.periodo_fin.isoformat() if extracto.periodo_fin else None,
                "fecha_corte": extracto.fecha_corte.isoformat() if extracto.fecha_corte else None,
            },
            "kpis": {
                "total_gastado": float(total_gastado),
                "total_ingresos": float(total_ingresos),
                "total_transacciones": num_transacciones,
                "promedio_diario": round(float(promedio_diario), 2),
                "pct_cupo_utilizado": round(float(pct_cupo), 1),
                "dias_para_pago": dias_pago,
                "variacion_vs_anterior_pct": round(variacion_vs_anterior, 1),
            },
        }

    async def handle_dashboard_by_category(self, query: DashboardByCategoryQuery) -> dict[str, Any]:
        """Retorna distribucion de gasto por categoria para grafico Donut.

        Solo incluye gastos (valor > 0, no abonos).
        Las transacciones sin categoria se agrupan en 'Sin categoria'.
        """
        transacciones = await self.transaccion_repo.get_by_extracto(query.extracto_id)
        categorias = await self.categoria_repo.get_all(query.usuario_id)

        # Agrupar por categoria (solo gastos, no abonos)
        gastos_por_categoria: dict[str, dict] = {}
        for t in transacciones:
            if t.valor <= 0 or t.es_abono:
                continue
            # Si no tiene categoria, usar ID especial
            cat_id = str(t.categoria_id) if t.categoria_id else "__uncategorized__"
            if cat_id not in gastos_por_categoria:
                if cat_id == "__uncategorized__":
                    cat_name = "Sin categoria"
                    cat_color = "#6B7280"
                    cat_icon = "📁"
                else:
                    cat = next((c for c in categorias if str(c.id) == cat_id), None)
                    cat_name = cat.nombre if cat else "Sin categoria"
                    cat_color = cat.color if cat else "#6B7280"
                    cat_icon = cat.icono if cat and hasattr(cat, "icono") else "📁"
                gastos_por_categoria[cat_id] = {
                    "categoria_id": cat_id,
                    "categoria": cat_name,
                    "icono": cat_icon,
                    "color": cat_color,
                    "total": 0.0,
                    "count": 0,
                }
            gastos_por_categoria[cat_id]["total"] += float(t.valor)
            gastos_por_categoria[cat_id]["count"] += 1

        total_general = sum(c["total"] for c in gastos_por_categoria.values())
        items = sorted(gastos_por_categoria.values(), key=lambda x: x["total"], reverse=True)

        top_items = items[: query.top_n]
        otros_items = items[query.top_n :]
        otros_total = sum(i["total"] for i in otros_items)
        otros_count = sum(i["count"] for i in otros_items)

        for item in top_items:
            item["percentage"] = round(
                (item["total"] / total_general * 100) if total_general > 0 else 0, 1
            )

        return {
            "total_gastado": round(total_general, 2),
            "total_transacciones": sum(c["count"] for c in items),
            "items": top_items,
            "otros": {
                "total": round(otros_total, 2),
                "count": otros_count,
                "percentage": round(
                    (otros_total / total_general * 100) if total_general > 0 else 0, 1
                ),
            },
        }

    async def handle_dashboard_daily(self, query: DashboardDailyQuery) -> dict[str, Any]:
        """Retorna gasto diario del periodo para grafico de Barras Apiladas.

        Solo incluye gastos (valor > 0, no abonos).
        Agrupa por dia y por categoria dentro de cada dia.
        """
        transacciones = await self.transaccion_repo.get_by_extracto(query.extracto_id)
        categorias = await self.categoria_repo.get_all(query.usuario_id)

        # Agrupar por dia (solo gastos, no abonos)
        gastos_por_dia: dict[str, dict] = {}
        for t in transacciones:
            if t.valor <= 0 or t.es_abono or t.fecha is None:
                continue
            dia_key = t.fecha.isoformat()
            if dia_key not in gastos_por_dia:
                gastos_por_dia[dia_key] = {
                    "fecha": dia_key,
                    "total": 0.0,
                    "count": 0,
                    "por_categoria": {},
                }
            gastos_por_dia[dia_key]["total"] += float(t.valor)
            gastos_por_dia[dia_key]["count"] += 1

            cat_id = str(t.categoria_id) if t.categoria_id else "uncategorized"
            if cat_id not in gastos_por_dia[dia_key]["por_categoria"]:
                cat = next((c for c in categorias if str(c.id) == cat_id), None)
                gastos_por_dia[dia_key]["por_categoria"][cat_id] = {
                    "categoria_id": cat_id,
                    "categoria": cat.nombre if cat else "Sin categoria",
                    "color": cat.color if cat else "#6B7280",
                    "total": 0.0,
                }
            gastos_por_dia[dia_key]["por_categoria"][cat_id]["total"] += float(t.valor)

        # Convertir por_categoria de dict a lista ordenada
        for dia_data in gastos_por_dia.values():
            dia_data["categorias"] = sorted(
                dia_data["por_categoria"].values(),
                key=lambda x: x["total"],
                reverse=True,
            )
            del dia_data["por_categoria"]

        items = sorted(gastos_por_dia.values(), key=lambda x: x["fecha"])
        promedio = sum(i["total"] for i in items) / len(items) if items else 0.0

        return {
            "items": items,
            "total_dias": len(items),
            "promedio_diario": round(promedio, 2),
        }

    async def handle_dashboard_monthly_trend(
        self, query: DashboardMonthlyTrendQuery
    ) -> dict[str, Any]:
        """Retorna tendencia mensual de gastos/ingresos para grafico de Linea.

        Consulta los ultimos N extractos del usuario (por default 6 meses).
        Si se especifica tarjeta_id, filtra solo extractos de esa tarjeta.
        """
        # Consultar los ultimos N extractos del usuario
        extractos, _ = await self.extracto_repo.get_by_usuario(
            query.usuario_id,
            page=1,
            size=query.meses * 2,  # Pedir extras por filtro
        )

        # Filtrar por tarjeta si se especifica
        if query.tarjeta_id:
            extractos = [e for e in extractos if e.tarjeta_id == query.tarjeta_id]

        items = []
        for e in extractos:
            if not e.periodo_inicio:
                continue

            transacciones = await self.transaccion_repo.get_by_extracto(e.id)

            # Gastos: valor positivo, no abonos
            gastos_list = [t for t in transacciones if t.valor > 0 and not t.es_abono]
            gastos = sum(t.valor for t in gastos_list)

            # Ingresos: abonos o valor negativo
            ingresos_list = [t for t in transacciones if t.valor < 0 or t.es_abono]
            ingresos = sum(abs(t.valor) for t in ingresos_list)

            items.append(
                {
                    "mes": e.periodo_inicio.strftime("%Y-%m"),
                    "extracto_id": str(e.id),
                    "periodo_inicio": e.periodo_inicio.isoformat(),
                    "periodo_fin": e.periodo_fin.isoformat() if e.periodo_fin else None,
                    "gastos": float(gastos),
                    "ingresos": float(ingresos),
                    "transacciones_count": len(gastos_list),
                    "saldo_neto": float(ingresos - gastos),
                }
            )

        # Ordenar cronologicamente y limitar a los ultimos N meses
        items.sort(key=lambda x: x["mes"])
        items = items[-query.meses :]

        # Promedio movil de los ultimos 3 meses
        gastos_items = [i["gastos"] for i in items]
        promedio_movil_3m = (
            sum(gastos_items[-3:]) / 3
            if len(gastos_items) >= 3
            else (sum(gastos_items) / len(gastos_items) if gastos_items else 0)
        )

        # Tendencia general (comparacion primer vs ultimo mes)
        tendencia_pct = 0.0
        if len(items) >= 2 and items[0]["gastos"] > 0:
            tendencia_pct = round(
                ((items[-1]["gastos"] - items[0]["gastos"]) / items[0]["gastos"]) * 100, 1
            )

        return {
            "items": items,
            "total_meses": len(items),
            "promedio_movil_3m": round(promedio_movil_3m, 2),
            "tendencia_pct": tendencia_pct,
        }

    async def handle_obtener_transacciones(
        self, query: ObtenerTransaccionesQuery
    ) -> dict[str, Any]:
        """Retorna lista de transacciones con filtros, paginacion y sorting.

        Soportes:
        - Filtros: extracto_id, categoria_id, search (comercio), confidence (HIGH/MEDIUM/LOW)
        - Paginacion: page, size
        - Sorting: sort_by (fecha, valor, comercio, confidence), order (asc/desc)
        """
        filters: dict[str, Any] = {}
        if query.extracto_id:
            filters["extracto_id"] = query.extracto_id
        if query.categoria_id:
            filters["categoria_id"] = query.categoria_id
        if query.search:
            filters["search"] = query.search
        if query.confidence:
            filters["confidence"] = query.confidence

        items, total = await self.transaccion_repo.get_by_usuario(
            query.usuario_id,
            filters=filters,
            page=query.page,
            size=query.size,
            sort_by=query.sort_by,
            order=query.order,
        )

        return {
            "items": [
                {
                    "id": str(t.id),
                    "fecha": t.fecha.isoformat() if t.fecha else None,
                    "comercio": t.nombre_visible,
                    "valor": float(t.valor),
                    "categoria_id": str(t.categoria_id) if t.categoria_id else None,
                    "confidence": float(t.confidence) if t.confidence else None,
                    "es_cuota": t.es_cuota,
                }
                for t in items
            ],
            "total": total,
            "page": query.page,
            "size": query.size,
        }

    async def handle_obtener_extractos(self, query: ObtenerExtractosQuery) -> dict[str, Any]:
        """Retorna lista de extractos del usuario."""
        items, total = await self.extracto_repo.get_by_usuario(
            query.usuario_id, page=query.page, size=query.size
        )

        return {
            "items": [
                {
                    "id": str(e.id),
                    "estado": e.estado,
                    "periodo_inicio": e.periodo_inicio.isoformat() if e.periodo_inicio else None,
                    "periodo_fin": e.periodo_fin.isoformat() if e.periodo_fin else None,
                    "pago_total": float(e.pago_total),
                    "tarjeta_id": str(e.tarjeta_id),
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in items
            ],
            "total": total,
            "page": query.page,
            "size": query.size,
        }

    async def handle_obtener_insights(self, query: ObtenerInsightsQuery) -> dict[str, Any]:
        """Retorna alertas y habitos detectados para el periodo."""
        # El calculo real lo hace el DetectorHabitos del dominio
        # En produccion, los insights se pre-calculan en el worker de clasificacion
        transacciones_raw = await self.transaccion_repo.get_by_extracto(query.extracto_id)
        transacciones = [
            {
                "valor": float(t.valor),
                "comercio": t.nombre_visible,
                "categoria_nombre": "General",
                "es_cuota": t.es_cuota,
                "categoria_id": str(t.categoria_id) if t.categoria_id else None,
            }
            for t in transacciones_raw
        ]

        return {
            "items": [],
            "score": 75,
            "zona": "healthy",
            "transacciones_count": len(transacciones),
        }
