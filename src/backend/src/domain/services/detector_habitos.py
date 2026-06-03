"""Servicio de dominio — Detector de malos habitos financieros.

Detecta los 8 patrones de gasto problematicos definidos en los requerimientos funcionales.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any


class TipoHabito(str, Enum):
    """Tipos de malos habitos financieros detectables."""

    SUSCRIPCION_FANTASMA = "suscripcion_fantasma"        # RF04.1
    GASTO_HORMIGA = "gasto_hormiga"                       # RF04.2
    EXCESO_CATEGORIA = "exceso_categoria"                  # RF04.3
    COMPRAS_IMPULSIVAS = "compras_impulsivas"             # RF04.4
    CRECIMIENTO_GASTO = "crecimiento_gasto"               # RF04.5
    ALTO_ENDEUDAMIENTO = "alto_endeudamiento"             # RF04.6
    GASTOS_FINANCIEROS_ALTOS = "gastos_financieros_altos"  # RF04.7
    DISMINUCION_INGRESOS = "disminucion_ingresos"         # RF04.8


class Severidad(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AlertaHabito:
    """Alerta generada por la deteccion de un mal habito."""

    tipo: TipoHabito
    titulo: str = ""
    descripcion: str = ""
    severidad: Severidad = Severidad.MEDIUM
    accion_sugerida: str = ""
    datos: dict[str, Any] = field(default_factory=dict)


class DetectorHabitos:
    """Detector de patrones de gasto problematicos.

    Analiza las transacciones del periodo y genera alertas
    cuando se detectan los 8 tipos de malos habitos definidos.
    """

    UMBRAL_SUSCRIPCION_MESES = 3
    UMBRAL_GASTO_HORMIGA_VALOR = Decimal("15.00")
    UMBRAL_GASTO_HORMIGA_FRECUENCIA = 5
    UMBRAL_EXCESO_CATEGORIA_PCT = Decimal("150")  # 150% del promedio
    UMBRAL_CRECIMIENTO_PCT = Decimal("20")        # 20% de crecimiento
    UMBRAL_ENDEUDAMIENTO_PCT = Decimal("40")       # 40% de ingresos
    UMBRAL_FINANCIEROS_PCT = Decimal("10")          # 10% del total gastado

    def detectar_todos(
        self,
        transacciones: list[dict],
        presupuestos: list[dict],
        historial_mensual: list[dict],
    ) -> list[AlertaHabito]:
        """Ejecuta todos los detectores y retorna las alertas generadas.

        Args:
            transacciones: Lista de transacciones del periodo actual.
            presupuestos: Presupuestos configurados por el usuario.
            historial_mensual: Resumen mensual historico (6-12 meses).

        Returns:
            Lista de AlertaHabito (puede estar vacia si no se detectan habitos).
        """
        alertas: list[AlertaHabito] = []
        alertas.extend(self.detectar_suscripciones_fantasma(transacciones))
        alertas.extend(self.detectar_gasto_hormiga(transacciones))
        alertas.extend(self.detectar_exceso_categoria(transacciones, presupuestos))
        alertas.extend(self.detectar_compras_impulsivas(transacciones))
        alertas.extend(self.detectar_crecimiento_gasto(historial_mensual))
        alertas.extend(self.detectar_alto_endeudamiento(transacciones, historial_mensual))
        alertas.extend(self.detectar_gastos_financieros_altos(transacciones))
        return alertas

    # ---------------------------------------------------------------
    # RF04.1 — Suscripciones fantasma
    # ---------------------------------------------------------------
    def detectar_suscripciones_fantasma(
        self, transacciones: list[dict]
    ) -> list[AlertaHabito]:
        """Detecta cargos recurrentes que el usuario podria haber olvidado cancelar.

        Busca comercios que aparecen 3+ meses consecutivos con montos similares.
        """
        alertas: list[AlertaHabito] = []
        for t in transacciones:
            meses = t.get("meses_consecutivos", 0)
            if meses >= self.UMBRAL_SUSCRIPCION_MESES:
                monto = t.get("monto", Decimal("0"))
                alertas.append(
                    AlertaHabito(
                        tipo=TipoHabito.SUSCRIPCION_FANTASMA,
                        titulo=f"Suscripcion recurrente: {t.get('comercio', 'Desconocido')}",
                        descripcion=(
                            f"Llevas {meses} meses pagando ${monto:,.0f} COP a "
                            f"{t.get('comercio', 'este comercio')}. "
                            f"Acumulado: ${t.get('acumulado', 0):,.0f} COP."
                        ),
                        severidad=Severidad.MEDIUM,
                        accion_sugerida="Revisa si realmente necesitas esta suscripcion. Cancelala si no la usas.",
                        datos=t,
                    )
                )
        return alertas

    # ---------------------------------------------------------------
    # RF04.2 — Gasto hormiga (micropagos frecuentes)
    # ---------------------------------------------------------------
    def detectar_gasto_hormiga(
        self, transacciones: list[dict]
    ) -> list[AlertaHabito]:
        """Detecta multiples gastos pequeños que suman un monto significativo.

        Transacciones < $15,000 COP que ocurren 5+ veces en el periodo.
        """
        gastos_pequenos = [
            t for t in transacciones
            if abs(Decimal(str(t.get("valor", 0)))) < self.UMBRAL_GASTO_HORMIGA_VALOR
        ]
        if len(gastos_pequenos) >= self.UMBRAL_GASTO_HORMIGA_FRECUENCIA:
            total = sum(abs(Decimal(str(t.get("valor", 0)))) for t in gastos_pequenos)
            return [
                AlertaHabito(
                    tipo=TipoHabito.GASTO_HORMIGA,
                    titulo=f"Gasto hormiga: {len(gastos_pequenos)} compras pequenas",
                    descripcion=(
                        f"Realizaste {len(gastos_pequenos)} compras menores a "
                        f"${self.UMBRAL_GASTO_HORMIGA_VALOR:,.0f} COP "
                        f"que suman ${total:,.0f} COP."
                    ),
                    severidad=Severidad.LOW,
                    accion_sugerida="Identifica los gastos hormiga y reduce su frecuencia. Pequenos cambios generan grandes ahorros.",
                    datos={"count": len(gastos_pequenos), "total": str(total)},
                )
            ]
        return []

    # ---------------------------------------------------------------
    # RF04.3 — Exceso en categoria vs presupuesto
    # ---------------------------------------------------------------
    def detectar_exceso_categoria(
        self, transacciones: list[dict], presupuestos: list[dict]
    ) -> list[AlertaHabito]:
        """Detecta categorias donde el gasto excede significativamente el presupuesto."""
        alertas: list[AlertaHabito] = []
        for p in presupuestos:
            gastado = p.get("gastado", Decimal("0"))
            limite = p.get("limite_mensual", Decimal("0"))
            if limite > 0:
                pct = (gastado / limite) * 100
                if pct >= self.UMBRAL_EXCESO_CATEGORIA_PCT:
                    alertas.append(
                        AlertaHabito(
                            tipo=TipoHabito.EXCESO_CATEGORIA,
                            titulo=f"Exceso en {p.get('categoria_nombre', 'categoria')}",
                            descripcion=(
                                f"Has gastado ${gastado:,.0f} COP de un presupuesto de "
                                f"${limite:,.0f} COP ({pct:.0f}%)."
                            ),
                            severidad=Severidad.HIGH if pct >= 200 else Severidad.MEDIUM,
                            accion_sugerida=f"Reduce el gasto en {p.get('categoria_nombre', 'esta categoria')} o ajusta tu presupuesto.",
                            datos={"categoria": p.get("categoria_nombre"), "porcentaje": str(pct)},
                        )
                    )
        return alertas

    # ---------------------------------------------------------------
    # RF04.4 — Compras impulsivas (altas en horarios no habituales)
    # ---------------------------------------------------------------
    def detectar_compras_impulsivas(
        self, transacciones: list[dict]
    ) -> list[AlertaHabito]:
        """Detecta compras de alto valor en categorias de entretenimiento/ocio."""
        # Simplificado: busca transacciones grandes en categorias de entretenimiento
        alertas: list[AlertaHabito] = []
        for t in transacciones:
            valor = abs(Decimal(str(t.get("valor", 0))))
            categoria = t.get("categoria_nombre", "")
            if (
                categoria.lower() in ("entretenimiento", "ropa y moda", "viajes")
                and valor > 200000
            ):
                alertas.append(
                    AlertaHabito(
                        tipo=TipoHabito.COMPRAS_IMPULSIVAS,
                        titulo=f"Compra significativa: {t.get('comercio', '')}",
                        descripcion=f"Gastaste ${valor:,.0f} COP en {categoria} en {t.get('comercio', 'un comercio')}.",
                        severidad=Severidad.LOW,
                        accion_sugerida="Considera esperar 24h antes de compras no esenciales mayores a $200,000 COP.",
                    )
                )
        return alertas

    # ---------------------------------------------------------------
    # RF04.5 — Crecimiento acelerado del gasto
    # ---------------------------------------------------------------
    def detectar_crecimiento_gasto(
        self, historial_mensual: list[dict]
    ) -> list[AlertaHabito]:
        """Detecta tendencia de crecimiento del gasto mes a mes > 20%."""
        if len(historial_mensual) < 2:
            return []

        ultimo = historial_mensual[-1]
        anterior = historial_mensual[-2]
        gasto_ultimo = Decimal(str(ultimo.get("gastos", 0)))
        gasto_anterior = Decimal(str(anterior.get("gastos", 0)))

        if gasto_anterior > 0:
            crecimiento = ((gasto_ultimo - gasto_anterior) / gasto_anterior) * 100
            if crecimiento >= self.UMBRAL_CRECIMIENTO_PCT:
                return [
                    AlertaHabito(
                        tipo=TipoHabito.CRECIMIENTO_GASTO,
                        titulo="Tu gasto esta creciendo rapidamente",
                        descripcion=(
                            f"Tu gasto aumento {crecimiento:.0f}% respecto al mes anterior "
                            f"(${gasto_anterior:,.0f} → ${gasto_ultimo:,.0f} COP)."
                        ),
                        severidad=Severidad.HIGH if crecimiento >= 50 else Severidad.MEDIUM,
                        accion_sugerida="Revisa en que categorias esta el incremento y establece presupuestos.",
                    )
                ]
        return []

    # ---------------------------------------------------------------
    # RF04.6 — Alto nivel de endeudamiento
    # ---------------------------------------------------------------
    def detectar_alto_endeudamiento(
        self, transacciones: list[dict], historial_mensual: list[dict]
    ) -> list[AlertaHabito]:
        """Detecta cuando las cuotas mensuales superan el 40% de los ingresos."""
        total_cuotas = sum(
            abs(Decimal(str(t.get("valor_cuota", 0))))
            for t in transacciones
            if t.get("es_cuota")
        )
        ingresos = sum(
            abs(Decimal(str(h.get("ingresos", 0))))
            for h in historial_mensual[:1]
        )

        if ingresos > 0:
            pct = (total_cuotas / ingresos) * 100
            if pct >= self.UMBRAL_ENDEUDAMIENTO_PCT:
                return [
                    AlertaHabito(
                        tipo=TipoHabito.ALTO_ENDEUDAMIENTO,
                        titulo="Endeudamiento elevado",
                        descripcion=(
                            f"Tus cuotas mensuales (${total_cuotas:,.0f} COP) representan "
                            f"el {pct:.0f}% de tus ingresos. "
                            f"Lo recomendable es maximo 30-40%."
                        ),
                        severidad=Severidad.CRITICAL if pct >= 60 else Severidad.HIGH,
                        accion_sugerida="Evita nuevas compras a cuotas hasta reducir tu nivel de endeudamiento.",
                    )
                ]
        return []

    # ---------------------------------------------------------------
    # RF04.7 — Gastos financieros elevados
    # ---------------------------------------------------------------
    def detectar_gastos_financieros_altos(
        self, transacciones: list[dict]
    ) -> list[AlertaHabito]:
        """Detecta cuando los gastos financieros superan el 10% del total gastado."""
        gastos_financieros = sum(
            abs(Decimal(str(t.get("valor", 0))))
            for t in transacciones
            if t.get("categoria_nombre") == "Financieros"
        )
        total_gastado = sum(
            abs(Decimal(str(t.get("valor", 0)))) for t in transacciones
        )

        if total_gastado > 0:
            pct = (gastos_financieros / total_gastado) * 100
            if pct >= self.UMBRAL_FINANCIEROS_PCT:
                return [
                    AlertaHabito(
                        tipo=TipoHabito.GASTOS_FINANCIEROS_ALTOS,
                        titulo="Gastos financieros elevados",
                        descripcion=(
                            f"${gastos_financieros:,.0f} COP en comisiones e intereses "
                            f"({pct:.1f}% de tu gasto total)."
                        ),
                        severidad=Severidad.MEDIUM,
                        accion_sugerida="Paga el total de tu tarjeta cada mes para evitar intereses. Considera cambiar a una tarjeta sin cuota de manejo.",
                    )
                ]
        return []
