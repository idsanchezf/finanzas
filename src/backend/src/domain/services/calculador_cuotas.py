"""Servicio de dominio — Calculador de cuotas.

Logica pura para calculos de compras a cuotas:
- Costo total del credito (interes compuesto)
- Proyeccion de cuotas pendientes
- Fecha de liberacion de la deuda
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class ProyeccionCuota:
    """Proyeccion de una compra a cuotas."""

    comercio: str
    monto_original: Decimal
    cuota_mensual: Decimal
    cuotas_totales: int
    cuotas_pagadas: int
    cuotas_restantes: int
    interes_pagado: Decimal
    capital_pendiente: Decimal
    fecha_liberacion: date | None = None


class CalculadorCuotas:
    """Calculos financieros para compras a cuotas con interes."""

    @staticmethod
    def calcular_cuota_mensual(
        monto: Decimal, cuotas: int, tasa_mensual: Decimal | None = None
    ) -> Decimal:
        """Calcula el valor de la cuota mensual con sistema de amortizacion frances.

        Formula: C = M * (i * (1+i)^n) / ((1+i)^n - 1)

        Args:
            monto: Monto total de la compra.
            cuotas: Numero de cuotas.
            tasa_mensual: Tasa de interes mensual (ej. 0.02 = 2%). None = sin interes.

        Returns:
            Valor de la cuota mensual.
        """
        if cuotas <= 0:
            raise ValueError("El numero de cuotas debe ser > 0")
        if tasa_mensual is None or tasa_mensual == 0:
            return (monto / Decimal(cuotas)).quantize(Decimal("0.01"))

        i = tasa_mensual
        n = Decimal(cuotas)
        factor = (i * (1 + i) ** n) / ((1 + i) ** n - 1)
        return (monto * factor).quantize(Decimal("0.01"))

    @staticmethod
    def calcular_costo_total(
        monto: Decimal, cuotas: int, tasa_mensual: Decimal | None = None
    ) -> Decimal:
        """Calcula el costo total del credito (capital + intereses).

        Returns:
            Monto total pagado al final del credito.
        """
        cuota_mensual = CalculadorCuotas.calcular_cuota_mensual(monto, cuotas, tasa_mensual)
        return (cuota_mensual * cuotas).quantize(Decimal("0.01"))

    @staticmethod
    def calcular_interes_total(
        monto: Decimal, cuotas: int, tasa_mensual: Decimal | None = None
    ) -> Decimal:
        """Calcula el interes total pagado en el credito.

        Returns:
            Interes total = costo_total - monto_original.
        """
        costo = CalculadorCuotas.calcular_costo_total(monto, cuotas, tasa_mensual)
        return costo - monto

    @staticmethod
    def proyectar_cuotas_pendientes(
        transacciones_cuotas: list[dict],
    ) -> list[ProyeccionCuota]:
        """Proyecta las cuotas pendientes de todas las compras a cuotas activas.

        Args:
            transacciones_cuotas: Lista de dicts con datos de transacciones a cuotas.

        Returns:
            Lista de ProyeccionCuota ordenada por fecha de liberacion.
        """
        proyecciones = []
        for t in transacciones_cuotas:
            cuotas_totales = t.get("cuotas_totales", 1)
            cuota_actual = t.get("cuota_actual", 1)
            cuotas_restantes = cuotas_totales - cuota_actual
            monto = t.get("valor", Decimal("0"))
            tasa = t.get("interes_mensual_pct")

            if cuotas_restantes <= 0:
                continue

            cuota_mensual = CalculadorCuotas.calcular_cuota_mensual(
                monto, cuotas_totales, tasa
            )
            capital_pendiente = cuota_mensual * cuotas_restantes
            interes_pagado = (
                CalculadorCuotas.calcular_interes_total(monto, cuotas_totales, tasa)
                * (cuota_actual / cuotas_totales)
            )

            # Fecha estimada de liberacion
            fecha_transaccion = t.get("fecha")
            if fecha_transaccion and isinstance(fecha_transaccion, date):
                from dateutil.relativedelta import relativedelta
                fecha_liberacion = fecha_transaccion + relativedelta(months=cuotas_totales)
            else:
                fecha_liberacion = None

            proyecciones.append(
                ProyeccionCuota(
                    comercio=t.get("comercio_original", ""),
                    monto_original=monto,
                    cuota_mensual=cuota_mensual,
                    cuotas_totales=cuotas_totales,
                    cuotas_pagadas=cuota_actual,
                    cuotas_restantes=cuotas_restantes,
                    interes_pagado=interes_pagado,
                    capital_pendiente=capital_pendiente,
                    fecha_liberacion=fecha_liberacion,
                )
            )

        return sorted(proyecciones, key=lambda p: p.cuotas_restantes)
