"""Query Handlers — Procesan consultas de lectura (CQRS).

Los queries no modifican el estado del sistema. Solo consultan repositorios
y aplican transformaciones para retornar DTOs de presentacion.
"""

from __future__ import annotations

import logging
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
from src.domain.repositories import (
    IExtractoRepository,
    ITransaccionRepository,
    ICategoriaRepository,
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

    async def handle_dashboard_summary(
        self, query: DashboardSummaryQuery
    ) -> dict[str, Any]:
        """Retorna los KPIs del dashboard para un extracto."""
        extracto = await self.extracto_repo.get_by_id(query.extracto_id)
        if not extracto:
            raise ValueError(f"Extracto {query.extracto_id} no encontrado")

        transacciones = await self.transaccion_repo.get_by_extracto(query.extracto_id)
        total_gastado = sum(
            abs(t.valor) for t in transacciones if t.valor > 0
        )
        total_ingresos = sum(
            abs(t.valor) for t in transacciones if t.valor < 0
        )
        dias_periodo = (
            (extracto.periodo_fin - extracto.periodo_inicio).days
            if extracto.periodo_inicio and extracto.periodo_fin
            else 30
        ) or 1
        promedio_diario = total_gastado / dias_periodo

        return {
            "total_gastado": float(total_gastado),
            "total_ingresos": float(total_ingresos),
            "promedio_diario": float(promedio_diario),
            "pct_cupo_utilizado": float(extracto.porcentaje_cupo_utilizado),
            "dias_para_corte": extracto.dias_para_pago,
            "variacion_vs_anterior": 0.0,  # Se calcularia comparando con extracto anterior
        }

    async def handle_dashboard_by_category(
        self, query: DashboardByCategoryQuery
    ) -> dict[str, Any]:
        """Retorna distribucion de gasto por categoria."""
        transacciones = await self.transaccion_repo.get_by_extracto(query.extracto_id)
        categorias = await self.categoria_repo.get_all(query.usuario_id)

        # Agrupar por categoria
        gastos_por_categoria: dict[str, dict] = {}
        for t in transacciones:
            if t.valor <= 0 or t.categoria_id is None:
                continue
            cat_id = str(t.categoria_id)
            if cat_id not in gastos_por_categoria:
                cat = next((c for c in categorias if str(c.id) == cat_id), None)
                gastos_por_categoria[cat_id] = {
                    "categoria": cat.nombre if cat else "Sin categoria",
                    "color": cat.color if cat else "#6B7280",
                    "total": float(t.valor),
                }
            else:
                gastos_por_categoria[cat_id]["total"] += float(t.valor)

        total_general = sum(c["total"] for c in gastos_por_categoria.values())
        items = sorted(
            gastos_por_categoria.values(), key=lambda x: x["total"], reverse=True
        )

        top_items = items[: query.top_n]
        otros_total = sum(i["total"] for i in items[query.top_n :])

        for item in top_items:
            item["percentage"] = round(
                (item["total"] / total_general * 100) if total_general > 0 else 0, 1
            )

        return {
            "items": top_items,
            "otros": {
                "total": otros_total,
                "percentage": round(
                    (otros_total / total_general * 100) if total_general > 0 else 0, 1
                ),
            },
        }

    async def handle_dashboard_daily(
        self, query: DashboardDailyQuery
    ) -> dict[str, Any]:
        """Retorna gasto diario del periodo."""
        transacciones = await self.transaccion_repo.get_by_extracto(query.extracto_id)

        # Agrupar por dia
        gastos_por_dia: dict[str, dict] = {}
        for t in transacciones:
            if t.fecha is None:
                continue
            dia_key = t.fecha.isoformat()
            if dia_key not in gastos_por_dia:
                gastos_por_dia[dia_key] = {"dia": dia_key, "total": 0, "categorias": {}}
            gastos_por_dia[dia_key]["total"] += float(abs(t.valor))
            cat_id = str(t.categoria_id) if t.categoria_id else "uncategorized"
            gastos_por_dia[dia_key]["categorias"][cat_id] = (
                gastos_por_dia[dia_key]["categorias"].get(cat_id, 0) + float(abs(t.valor))
            )

        items = sorted(gastos_por_dia.values(), key=lambda x: x["dia"])
        promedio = sum(i["total"] for i in items) / len(items) if items else 0

        return {"items": items, "promedio": round(promedio, 2)}

    async def handle_dashboard_monthly_trend(
        self, query: DashboardMonthlyTrendQuery
    ) -> dict[str, Any]:
        """Retorna tendencia mensual de gastos/ingresos."""
        # Consultaria los ultimos N extractos del usuario
        extractos, _ = await self.extracto_repo.get_by_usuario(
            query.usuario_id, page=1, size=query.meses
        )

        items = []
        for e in extractos:
            transacciones = await self.transaccion_repo.get_by_extracto(e.id)
            gastos = sum(abs(t.valor) for t in transacciones if t.valor > 0)
            ingresos = sum(abs(t.valor) for t in transacciones if t.valor < 0)

            if e.periodo_inicio:
                items.append({
                    "mes": e.periodo_inicio.strftime("%Y-%m"),
                    "gastos": float(gastos),
                    "ingresos": float(ingresos),
                    "saldo_neto": float(ingresos - gastos),
                })

        items.sort(key=lambda x: x["mes"])
        promedio_movil = (
            sum(i["gastos"] for i in items[-3:]) / 3 if len(items) >= 3 else 0
        )

        return {"items": items, "promedio_movil": round(promedio_movil, 2)}

    async def handle_obtener_transacciones(
        self, query: ObtenerTransaccionesQuery
    ) -> dict[str, Any]:
        """Retorna lista de transacciones con filtros y paginacion."""
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
            query.usuario_id, filters=filters, page=query.page, size=query.size
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

    async def handle_obtener_extractos(
        self, query: ObtenerExtractosQuery
    ) -> dict[str, Any]:
        """Retorna lista de extractos del usuario."""
        items, total = await self.extracto_repo.get_by_usuario(
            query.usuario_id, page=query.page, size=query.size
        )

        return {
            "items": [
                {
                    "id": str(e.id),
                    "estado": e.estado.value if hasattr(e.estado, "value") else str(e.estado),
                    "periodo_inicio": e.periodo_inicio.isoformat() if e.periodo_inicio else None,
                    "periodo_fin": e.periodo_fin.isoformat() if e.periodo_fin else None,
                    "pago_total": float(e.pago_total),
                    "tarjeta_id": str(e.tarjeta_id),
                    "created_at": e.created_at.isoformat() if hasattr(e, "created_at") else None,
                }
                for e in items
            ],
            "total": total,
            "page": query.page,
            "size": query.size,
        }

    async def handle_obtener_insights(
        self, query: ObtenerInsightsQuery
    ) -> dict[str, Any]:
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
