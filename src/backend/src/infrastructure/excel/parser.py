"""Parser inteligente de extractos bancarios Excel (.xlsx).

Soporta multiples bancos mediante deteccion automatica de estructura.
Extrae metadatos y transacciones con tolerancia a variaciones de formato.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from typing import Any

import openpyxl
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ExtractoParseado:
    """Resultado del parseo de un extracto Excel."""

    metadatos: dict[str, Any] = field(default_factory=dict)
    transacciones: list[dict[str, Any]] = field(default_factory=list)
    errores: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def exitoso(self) -> bool:
        return len(self.errores) == 0 and len(self.transacciones) > 0


class ExtractoExcelParser:
    """Parser inteligente de extractos bancarios en Excel.

    Soporta deteccion automatica de:
    - Multiples secciones (metadatos, encabezados, tabla de transacciones)
    - Sub-filas VR MONEDA ORIG (asociadas a su transaccion padre)
    - Formato de cuotas ("1/36", "1/1")
    - Multiples bancos (Bancolombia, Davivienda, BBVA, etc.)
    """

    # Posibles nombres de columnas en diferentes bancos
    COLUMNAS_FECHA = ["fecha", "fecha transaccion", "fecha operacion", "dia"]
    COLUMNAS_COMERCIO = ["comercio", "descripcion", "descripcion transaccion", "establecimiento", "nombre"]
    COLUMNAS_VALOR = ["valor", "monto", "importe", "valor transaccion", "total"]
    COLUMNAS_CUOTAS = ["cuotas", "numero cuotas", "plan", "pago diferido"]
    COLUMNAS_AUTORIZACION = ["autorizacion", "num autorizacion", "codigo", "referencia"]

    # Patrones para detectar secciones del extracto
    PATRON_MONEDA_ORIG = re.compile(r"vr\s*moneda\s*orig", re.IGNORECASE)
    PATRON_CUOTAS = re.compile(r"^\d+/\d+$")
    PATRON_FECHA_CORTE = re.compile(r"(fecha\s*(de)?\s*corte|corte\s*(del)?\s*periodo)", re.IGNORECASE)
    PATRON_FECHA_PAGO = re.compile(r"(fecha\s*(limite|maxima|de)?\s*pago|pago\s*(oportuno|minimo)?)", re.IGNORECASE)
    PATRON_CUPO = re.compile(r"(cupo\s*(total|disponible|credito)|limite\s*(de)?\s*credito)", re.IGNORECASE)

    def parse(self, file_content: bytes, filename: str = "") -> ExtractoParseado:
        """Parsea un archivo Excel de extracto bancario.

        Args:
            file_content: Contenido binario del archivo .xlsx.
            filename: Nombre del archivo (para logging y deteccion de banco).

        Returns:
            ExtractoParseado con metadatos, transacciones y errores.
        """
        resultado = ExtractoParseado()

        try:
            workbook = openpyxl.load_workbook(BytesIO(file_content), data_only=True)
            sheet = workbook.active

            if sheet is None:
                resultado.errores.append("El archivo Excel no tiene hojas activas")
                return resultado

            # Convertir a DataFrame para analisis
            data = self._sheet_to_dataframe(sheet)

            if data.empty:
                resultado.errores.append("No se encontraron datos en el archivo")
                return resultado

            # Detectar banco
            banco = self._detectar_banco(data, filename)
            resultado.metadatos["banco"] = banco
            logger.info(f"Banco detectado: {banco}")

            # Extraer metadatos
            self._extraer_metadatos(resultado, data, sheet)

            # Extraer transacciones
            self._extraer_transacciones(resultado, data)

            logger.info(
                f"Parseo completado: {len(resultado.transacciones)} transacciones, "
                f"{len(resultado.errores)} errores, {len(resultado.warnings)} warnings"
            )

        except Exception as e:
            resultado.errores.append(f"Error al parsear el archivo: {str(e)}")
            logger.error("Error en el parseo del extracto", exc_info=True)

        return resultado

    def _sheet_to_dataframe(self, sheet) -> pd.DataFrame:
        """Convierte una hoja de openpyxl a DataFrame de pandas."""
        rows = []
        for row in sheet.iter_rows(values_only=True):
            # Filtrar filas completamente vacias
            if any(cell is not None for cell in row):
                rows.append(list(row))

        if not rows:
            return pd.DataFrame()

        # Usar primera fila como encabezado si parece tener nombres de columna
        df = pd.DataFrame(rows[1:], columns=rows[0]) if len(rows) > 1 else pd.DataFrame(rows)
        return df

    def _detectar_banco(self, df: pd.DataFrame, filename: str) -> str:
        """Intenta detectar el banco a partir del contenido del archivo."""
        # Buscar en el nombre del archivo
        if filename:
            filename_lower = filename.lower()
            if "bancolombia" in filename_lower or "bcolombia" in filename_lower:
                return "Bancolombia"
            if "davivienda" in filename_lower:
                return "Davivienda"
            if "bbva" in filename_lower:
                return "BBVA"
            if "banco de bogota" in filename_lower or "bogota" in filename_lower:
                return "Banco de Bogota"

        # Buscar en el contenido (primeras filas suelen tener metadata del banco)
        for _, row in df.head(20).iterrows():
            row_text = " ".join(str(v) for v in row.values if pd.notna(v)).lower()
            if "bancolombia" in row_text:
                return "Bancolombia"
            if "davivienda" in row_text:
                return "Davivienda"
            if "bbva" in row_text:
                return "BBVA"

        return "Desconocido"

    def _extraer_metadatos(
        self, resultado: ExtractoParseado, df: pd.DataFrame, sheet
    ) -> None:
        """Extrae metadatos del extracto: periodo, fechas de corte/pago, cupos, tasas."""
        # Buscar en las primeras 20 filas (zona de metadatos)
        for _, row in df.head(20).iterrows():
            row_text = " ".join(str(v) for v in row.values if pd.notna(v)).lower()

            # Detectar fecha de corte
            if self.PATRON_FECHA_CORTE.search(row_text):
                for val in row.values:
                    if isinstance(val, (datetime, date)):
                        resultado.metadatos["fecha_corte"] = (
                            val.date() if isinstance(val, datetime) else val
                        )

            # Detectar fecha limite de pago
            if self.PATRON_FECHA_PAGO.search(row_text):
                for val in row.values:
                    if isinstance(val, (datetime, date)):
                        resultado.metadatos["fecha_limite_pago"] = (
                            val.date() if isinstance(val, datetime) else val
                        )

            # Detectar cupos
            if self.PATRON_CUPO.search(row_text):
                for val in row.values:
                    if isinstance(val, (int, float)):
                        monto = Decimal(str(val))
                        if monto > 100000:  # Asumir que cupos son montos grandes
                            if "cupo_total" not in resultado.metadatos:
                                resultado.metadatos["cupo_total"] = monto
                            elif "cupo_disponible" not in resultado.metadatos:
                                resultado.metadatos["cupo_disponible"] = monto

    def _extraer_transacciones(
        self, resultado: ExtractoParseado, df: pd.DataFrame
    ) -> None:
        """Extrae las transacciones de la tabla principal del extracto."""
        # Normalizar nombres de columnas
        df.columns = [str(c).strip().lower() for c in df.columns]

        # Identificar columnas relevantes
        col_fecha = self._find_column(df, self.COLUMNAS_FECHA)
        col_comercio = self._find_column(df, self.COLUMNAS_COMERCIO)
        col_valor = self._find_column(df, self.COLUMNAS_VALOR)
        col_cuotas = self._find_column(df, self.COLUMNAS_CUOTAS)
        col_autorizacion = self._find_column(df, self.COLUMNAS_AUTORIZACION)

        if not col_comercio or not col_valor:
            resultado.errores.append(
                "No se pudieron identificar las columnas de comercio o valor en el extracto"
            )
            return

        # Filtrar filas que parecen ser transacciones (tienen fecha o comercio)
        for idx, row in df.iterrows():
            try:
                # Saltar filas que son sub-filas de moneda original
                row_text = " ".join(str(v) for v in row.values if pd.notna(v))
                if self.PATRON_MONEDA_ORIG.search(row_text):
                    # Asociar a la transaccion anterior como sub-fila
                    if resultado.transacciones:
                        prev = resultado.transacciones[-1]
                        self._extraer_moneda_original(row, prev)
                    continue

                comercio = str(row.get(col_comercio, "")).strip()
                if not comercio or comercio.lower() in ("nan", "none", ""):
                    continue

                valor = self._parse_valor(row.get(col_valor))
                fecha = self._parse_fecha(row.get(col_fecha)) if col_fecha else None
                autorizacion = str(row.get(col_autorizacion, "")) if col_autorizacion else None
                cuotas_str = str(row.get(col_cuotas, "")) if col_cuotas else None

                # Parsear cuotas
                cuotas_totales = None
                cuota_actual = None
                if cuotas_str and self.PATRON_CUOTAS.match(cuotas_str):
                    partes = cuotas_str.split("/")
                    cuota_actual = int(partes[0].strip())
                    cuotas_totales = int(partes[1].strip())

                transaccion = {
                    "numero_autorizacion": autorizacion if autorizacion and autorizacion.lower() != "nan" else None,
                    "fecha": fecha,
                    "comercio_original": comercio[:500],
                    "valor": valor,
                    "numero_cuotas": cuotas_str if cuotas_str and cuotas_str.lower() != "nan" else None,
                    "cuotas_totales": cuotas_totales,
                    "cuota_actual": cuota_actual,
                    "moneda_original": None,
                    "valor_moneda_original": None,
                }
                resultado.transacciones.append(transaccion)

            except Exception as e:
                resultado.warnings.append(f"Fila {idx}: {str(e)}")

        # Post-procesamiento: calcular valores de cuota para compras a cuotas
        for t in resultado.transacciones:
            if t.get("cuotas_totales") and t["cuotas_totales"] > 1:
                t["es_cuota"] = True
                t["valor_cuota"] = (t["valor"] / t["cuotas_totales"]).quantize(Decimal("0.01"))
            else:
                t["es_cuota"] = False

    def _extraer_moneda_original(self, row: pd.Series, transaccion: dict) -> None:
        """Extrae el valor en moneda original de una sub-fila VR MONEDA ORIG."""
        for val in row.values:
            if isinstance(val, (int, float)) and val > 0 and val < transaccion.get("valor", 0):
                transaccion["moneda_original"] = "USD"
                transaccion["valor_moneda_original"] = Decimal(str(val))
                break

    def _find_column(self, df: pd.DataFrame, candidates: list[str]) -> str | None:
        """Busca una columna por nombre entre candidatos posibles."""
        for candidate in candidates:
            for col in df.columns:
                if candidate.lower() in str(col).lower():
                    return col
        return None

    def _parse_valor(self, valor_raw: Any) -> Decimal:
        """Convierte un valor a Decimal, manejando formatos colombianos."""
        if valor_raw is None:
            return Decimal("0.00")

        if isinstance(valor_raw, (int, float)):
            return Decimal(str(valor_raw)).quantize(Decimal("0.01"))

        if isinstance(valor_raw, str):
            # Remover simbolos y caracteres no numericos
            cleaned = valor_raw.replace("$", "").replace("COP", "").replace(",", "").strip()
            try:
                return Decimal(cleaned).quantize(Decimal("0.01"))
            except Exception:
                pass

        return Decimal("0.00")

    def _parse_fecha(self, fecha_raw: Any) -> date | None:
        """Convierte un valor a date, manejando distintos formatos."""
        if isinstance(fecha_raw, datetime):
            return fecha_raw.date()
        if isinstance(fecha_raw, date):
            return fecha_raw
        if isinstance(fecha_raw, str):
            # Intentar formatos comunes: DD/MM/YYYY, YYYY-MM-DD
            for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"):
                try:
                    return datetime.strptime(fecha_raw.strip(), fmt).date()
                except ValueError:
                    continue
        return None
