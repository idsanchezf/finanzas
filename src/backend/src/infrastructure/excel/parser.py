"""Parser inteligente de extractos bancarios Excel (.xlsx).

Soporta multiples bancos mediante deteccion automatica de estructura.
Extrae metadatos y transacciones con tolerancia a variaciones de formato.
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from typing import Any

import openpyxl

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

    # ------------------------------------------------------------------
    # Constantes de columnas para formato Bancolombia (indices 0-based)
    # ------------------------------------------------------------------
    BC_COL_AUTORIZACION = 0
    BC_COL_FECHA = 1
    BC_COL_MOVIMIENTOS = 2
    BC_COL_VALOR = 3
    BC_COL_CUOTAS = 4
    BC_COL_VALOR_CUOTA_ABONO = 5
    BC_COL_INTERES_MENSUAL = 6
    BC_COL_INTERES_ANUAL = 7
    BC_COL_SALDO_PENDIENTE = 8

    # ------------------------------------------------------------------
    # Patrones de compilacion
    # ------------------------------------------------------------------
    PATRON_MONEDA_ORIG = re.compile(r"vr\s*moneda\s*orig", re.IGNORECASE)
    PATRON_CUOTAS = re.compile(r"^\d+/\d+$")
    PATRON_SECCION_MOVIMIENTOS = re.compile(
        r"movimientos\s+(durante|antes)\s+(el|del)\s+periodo", re.IGNORECASE
    )
    PATRON_HEADER_AUTORIZACION = re.compile(r"n[uú]mero\s+(de\s+)?autorizaci[oó]n", re.IGNORECASE)
    PATRON_FECHA_DDMMYYYY = re.compile(r"^\d{1,2}/\d{1,2}/\d{4}$")

    # ------------------------------------------------------------------
    # Firmas estructurales de Bancolombia
    # ------------------------------------------------------------------
    BANCOLOMBIA_SIGNATURES = [
        "información cliente",
        "información de la tarjeta",
        "periodo facturado",
    ]

    # ==================================================================
    # Metodo principal
    # ==================================================================

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

            # Obtener todas las filas no vacias como listas
            rows: list[list] = []
            for row in sheet.iter_rows(values_only=True):
                if any(cell is not None for cell in row):
                    rows.append(list(row))

            if not rows:
                resultado.errores.append("No se encontraron datos en el archivo")
                return resultado

            # Detectar banco
            banco = self._detectar_banco(rows, filename)
            resultado.metadatos["banco"] = banco
            logger.info(f"Banco detectado: {banco}")

            # Extraer metadatos
            self._extraer_metadatos(resultado, rows, banco)

            # Extraer transacciones
            self._extraer_transacciones(resultado, rows, banco)

            logger.info(
                f"Parseo completado: {len(resultado.transacciones)} transacciones, "
                f"{len(resultado.errores)} errores, {len(resultado.warnings)} warnings"
            )

        except Exception as e:
            resultado.errores.append(f"Error al parsear el archivo: {str(e)}")
            logger.error("Error en el parseo del extracto", exc_info=True)

        return resultado

    # ==================================================================
    # Deteccion de banco
    # ==================================================================

    def _detectar_banco(self, rows: list[list], filename: str) -> str:
        """Detecta el banco por nombre de archivo o patrones estructurales."""
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

        # Buscar en el contenido textual
        all_text = " ".join(str(c) for row in rows[:40] for c in row if c is not None).lower()

        if "bancolombia" in all_text or "bcolombia" in all_text:
            return "Bancolombia"
        if "davivienda" in all_text:
            return "Davivienda"
        if "bbva" in all_text:
            return "BBVA"

        # Detectar Bancolombia por firmas estructurales
        bc_signatures_found = 0
        for sig in self.BANCOLOMBIA_SIGNATURES:
            if sig in all_text:
                bc_signatures_found += 1

        if bc_signatures_found >= 2:
            return "Bancolombia"

        # Tambien detectar por encabezados de transaccion
        has_vr_moneda = any(
            self.PATRON_MONEDA_ORIG.search(str(c)) for row in rows for c in row if c is not None
        )
        has_header_auth = any(
            self.PATRON_HEADER_AUTORIZACION.search(str(c))
            for row in rows
            for c in row
            if c is not None
        )
        if has_vr_moneda and has_header_auth:
            return "Bancolombia"

        return "Desconocido"

    # ==================================================================
    # Extraccion de metadatos
    # ==================================================================

    def _extraer_metadatos(self, resultado: ExtractoParseado, rows: list[list], banco: str) -> None:
        """Extrae metadatos del extracto."""
        if banco == "Bancolombia":
            self._extraer_metadatos_bancolombia(resultado, rows)
        else:
            self._extraer_metadatos_generico(resultado, rows)

    def _extraer_metadatos_bancolombia(self, resultado: ExtractoParseado, rows: list[list]) -> None:
        """Extrae metadatos del formato Bancolombia."""
        # Buscar en las primeras filas (zona de metadata, antes de transacciones)
        tx_start = self._find_transaction_header_row(rows)
        metadata_rows = rows[:tx_start] if tx_start > 0 else rows[:30]

        for row in metadata_rows:
            # Construir texto completo de la fila para busqueda de patrones
            row_text = " ".join(str(v) for v in row if v is not None)

            # Periodo facturado
            if "periodo facturado" in row_text.lower():
                dates = self._extract_dates_from_row(row)
                if len(dates) >= 2:
                    resultado.metadatos["periodo_inicio"] = dates[0]
                    resultado.metadatos["periodo_fin"] = dates[1]
                elif len(dates) == 1:
                    resultado.metadatos["periodo_inicio"] = dates[0]

            # Fecha de pago
            if "pagar antes" in row_text.lower():
                dates = self._extract_dates_from_row(row)
                if dates:
                    resultado.metadatos["fecha_limite_pago"] = dates[0]

            # Pago minimo
            if "pago m" in row_text.lower():  # Cubre "Pago mínimo" y "Pago minimo"
                val = self._parse_colombian_number(row, prefer_index=1)
                if val is not None:
                    resultado.metadatos["pago_minimo"] = val

            # Pago total
            if "pago total" in row_text.lower():
                val = self._parse_colombian_number(row, prefer_index=1)
                if val is not None:
                    resultado.metadatos["pago_total"] = val

            # Cupo total
            if "cupo total" in row_text.lower():
                val = self._parse_colombian_number(row, prefer_index=1)
                if val is not None:
                    resultado.metadatos["cupo_total"] = val

            # Cupo disponible
            if "cupo disponible" in row_text.lower():
                val = self._parse_colombian_number(row, prefer_index=1)
                if val is not None:
                    resultado.metadatos["cupo_disponible"] = val

            # Moneda
            if "moneda:" in row_text.lower():
                for v in row:
                    if isinstance(v, str) and v.strip().upper() in (
                        "PESOS",
                        "DOLARES",
                        "USD",
                        "COP",
                    ):
                        resultado.metadatos["moneda"] = v.strip().upper()
                        break

        # Inferir fecha de corte = periodo_fin si disponible
        if "periodo_fin" in resultado.metadatos:
            resultado.metadatos["fecha_corte"] = resultado.metadatos["periodo_fin"]

    def _extraer_metadatos_generico(self, resultado: ExtractoParseado, rows: list[list]) -> None:
        """Extrae metadatos de formato generico/desconocido."""
        for row in rows[:30]:
            row_text = " ".join(str(v) for v in row if v is not None).lower()

            if "fecha" in row_text and "corte" in row_text:
                dates = self._extract_dates_from_row(row)
                if dates:
                    resultado.metadatos["fecha_corte"] = dates[0]

            if "cupo" in row_text:
                val = self._parse_colombian_number(row)
                if val is not None and val > 100000:
                    if "cupo_total" not in resultado.metadatos:
                        resultado.metadatos["cupo_total"] = val
                    elif "cupo_disponible" not in resultado.metadatos:
                        resultado.metadatos["cupo_disponible"] = val

    # ==================================================================
    # Extraccion de transacciones
    # ==================================================================

    def _extraer_transacciones(
        self, resultado: ExtractoParseado, rows: list[list], banco: str
    ) -> None:
        """Extrae transacciones del extracto."""
        if banco == "Bancolombia":
            self._extraer_transacciones_bancolombia(resultado, rows)
        else:
            self._extraer_transacciones_generico(resultado, rows)

    def _extraer_transacciones_bancolombia(
        self, resultado: ExtractoParseado, rows: list[list]
    ) -> None:
        """Extrae transacciones del formato Bancolombia usando indices fijos."""
        # Encontrar todas las secciones de transacciones
        section_starts = self._find_transaction_sections(rows)

        if not section_starts:
            # Intentar con el primer header de autorizacion
            header_row = self._find_transaction_header_row(rows)
            if header_row >= 0:
                section_starts = [header_row]

        if not section_starts:
            resultado.errores.append("No se encontraron secciones de transacciones en el extracto")
            return

        for section_start in section_starts:
            # El header esta en section_start, las transacciones empiezan en section_start + 1
            self._parse_transaction_section_bancolombia(resultado, rows, section_start)

        # Si no se extrajeron transacciones, es un error
        if not resultado.transacciones:
            resultado.errores.append("No se pudieron extraer transacciones del extracto")
            return

        # Post-procesamiento: calcular campos derivados
        for t in resultado.transacciones:
            if t.get("cuotas_totales") and t["cuotas_totales"] > 1:
                t["es_cuota"] = True
                try:
                    t["valor_cuota"] = (t["valor"] / t["cuotas_totales"]).quantize(Decimal("0.01"))
                except Exception:
                    t["valor_cuota"] = t["valor"]
            else:
                t["es_cuota"] = False

    def _parse_transaction_section_bancolombia(
        self, resultado: ExtractoParseado, rows: list[list], header_idx: int
    ) -> None:
        """Parsea una seccion de transacciones Bancolombia."""
        i = header_idx + 1  # Saltar el header
        while i < len(rows):
            row = rows[i]

            # Detener si encontramos otra seccion de movimientos o header
            row_text = " ".join(str(v) for v in row if v is not None)
            if self.PATRON_SECCION_MOVIMIENTOS.search(row_text):
                break
            if self.PATRON_HEADER_AUTORIZACION.search(row_text):
                break

            # Verificar si es una sub-fila VR MONEDA ORIG
            col2_val = (
                str(row[self.BC_COL_MOVIMIENTOS])
                if len(row) > self.BC_COL_MOVIMIENTOS and row[self.BC_COL_MOVIMIENTOS] is not None
                else ""
            )

            if self.PATRON_MONEDA_ORIG.search(col2_val):
                # Asociar a la transaccion anterior
                if resultado.transacciones:
                    prev = resultado.transacciones[-1]
                    self._parse_vr_moneda_orig(row, prev)
                i += 1
                continue

            # Verificar si es una transaccion valida: debe tener comercio en col 2
            comercio = self._safe_str(row, self.BC_COL_MOVIMIENTOS)
            if not comercio:
                i += 1
                continue

            # Parsear campos
            autorizacion = self._safe_str(row, self.BC_COL_AUTORIZACION)
            autorizacion = autorizacion if autorizacion else None

            fecha = self._parse_fecha(self._safe_str(row, self.BC_COL_FECHA))
            valor = self._parse_colombian_number(row, prefer_index=self.BC_COL_VALOR)
            if valor is None:
                valor = Decimal("0.00")

            cuotas_str = self._safe_str(row, self.BC_COL_CUOTAS)
            cuotas_totales = None
            cuota_actual = None
            if cuotas_str and self.PATRON_CUOTAS.match(cuotas_str):
                partes = cuotas_str.split("/")
                try:
                    cuota_actual = int(partes[0].strip())
                    cuotas_totales = int(partes[1].strip())
                except ValueError:
                    pass

            transaccion = {
                "numero_autorizacion": autorizacion,
                "fecha": fecha,
                "comercio_original": comercio[:500],
                "valor": valor,
                "numero_cuotas": cuotas_str if cuotas_str else None,
                "cuotas_totales": cuotas_totales,
                "cuota_actual": cuota_actual,
                "moneda_original": None,
                "valor_moneda_original": None,
            }
            resultado.transacciones.append(transaccion)
            i += 1

        # Fin de la seccion

    def _parse_vr_moneda_orig(self, row: list, transaccion: dict) -> None:
        """Extrae el valor en moneda original de una sub-fila VR MONEDA ORIG."""
        col2_val = (
            str(row[self.BC_COL_MOVIMIENTOS])
            if len(row) > self.BC_COL_MOVIMIENTOS and row[self.BC_COL_MOVIMIENTOS] is not None
            else ""
        )

        # Formato: "VR MONEDA ORIG 118.6 EC" o "VR MONEDA ORIG 74.8 EC"
        # Extraer valor y codigo de moneda
        match = re.search(
            r"vr\s*moneda\s*orig\s+([\d,.]+)\s*(\w+)",
            col2_val,
            re.IGNORECASE,
        )
        if match:
            valor_str = match.group(1)
            moneda_code = match.group(2).upper().strip()

            # El valor en VR MONEDA ORIG usa punto como decimal
            try:
                valor_orig = Decimal(valor_str.replace(",", ""))
            except Exception:
                # Intentar parsear como numero colombiano
                valor_orig = self._parse_colombian_number_from_string(valor_str)
                if valor_orig is None:
                    return

            transaccion["moneda_original"] = moneda_code
            transaccion["valor_moneda_original"] = valor_orig

    def _extraer_transacciones_generico(
        self, resultado: ExtractoParseado, rows: list[list]
    ) -> None:
        """Extrae transacciones de formato generico/desconocido usando heuristica."""
        # Intenta encontrar headers de transaccion por columnas comunes
        # Buscar filas que parezcan encabezados
        header_idx = -1
        fecha_col = -1
        comercio_col = -1
        valor_col = -1
        cuotas_col = -1
        autorizacion_col = -1

        for i, row in enumerate(rows):
            if i > 40:  # Solo buscar en las primeras 40 filas
                break
            row_lower = [str(c).lower() if c is not None else "" for c in row]
            row_str = " ".join(row_lower)

            if "fecha" in row_str and (
                "movimiento" in row_str or "descrip" in row_str or "comercio" in row_str
            ):
                header_idx = i
                # Identificar columnas
                for j, col_name in enumerate(row_lower):
                    if col_name and "fecha" in col_name:
                        fecha_col = j
                    if col_name and any(
                        w in col_name for w in ("movimiento", "descrip", "comercio", "establec")
                    ):
                        comercio_col = j
                    if col_name and any(w in col_name for w in ("valor", "monto", "importe")):
                        valor_col = j
                    if col_name and "cuota" in col_name:
                        cuotas_col = j
                    if col_name and "autoriz" in col_name:
                        autorizacion_col = j
                break

        if comercio_col < 0 or valor_col < 0:
            resultado.errores.append("No se pudieron identificar las columnas de comercio o valor")
            return

        # Parsear transacciones desde header_idx + 1
        for i in range(header_idx + 1, len(rows)):
            row = rows[i]

            # Detener si encontramos otro header o seccion
            row_text = " ".join(str(v) for v in row if v is not None)
            if self.PATRON_SECCION_MOVIMIENTOS.search(
                row_text
            ) or self.PATRON_HEADER_AUTORIZACION.search(row_text):
                continue  # Saltar headers repetidos

            comercio = self._safe_str(row, comercio_col)
            if not comercio:
                continue

            # VR MONEDA ORIG
            if self.PATRON_MONEDA_ORIG.search(comercio):
                if resultado.transacciones:
                    prev = resultado.transacciones[-1]
                    self._parse_vr_moneda_orig_generico(row, prev)
                continue

            valor = self._parse_colombian_number(row, prefer_index=valor_col)
            if valor is None:
                valor = Decimal("0.00")

            fecha = self._parse_fecha(self._safe_str(row, fecha_col)) if fecha_col >= 0 else None
            autorizacion = self._safe_str(row, autorizacion_col) if autorizacion_col >= 0 else None
            autorizacion = autorizacion if autorizacion else None

            cuotas_str = self._safe_str(row, cuotas_col) if cuotas_col >= 0 else None
            cuotas_totales = None
            cuota_actual = None
            if cuotas_str and self.PATRON_CUOTAS.match(cuotas_str):
                partes = cuotas_str.split("/")
                try:
                    cuota_actual = int(partes[0].strip())
                    cuotas_totales = int(partes[1].strip())
                except ValueError:
                    pass

            transaccion = {
                "numero_autorizacion": autorizacion,
                "fecha": fecha,
                "comercio_original": comercio[:500],
                "valor": valor,
                "numero_cuotas": cuotas_str if cuotas_str else None,
                "cuotas_totales": cuotas_totales,
                "cuota_actual": cuota_actual,
                "moneda_original": None,
                "valor_moneda_original": None,
            }
            resultado.transacciones.append(transaccion)

        if resultado.transacciones:
            for t in resultado.transacciones:
                if t.get("cuotas_totales") and t["cuotas_totales"] > 1:
                    t["es_cuota"] = True
                else:
                    t["es_cuota"] = False

    def _parse_vr_moneda_orig_generico(self, row: list, transaccion: dict) -> None:
        """Extrae moneda original de sub-fila generica."""
        for val in row:
            if val is None:
                continue
            if isinstance(val, int | float) and math.isfinite(val) and val > 0:
                transaccion["moneda_original"] = "USD"
                transaccion["valor_moneda_original"] = Decimal(str(val))
                return
            if isinstance(val, str):
                match = re.search(
                    r"vr\s*moneda\s*orig\s+([\d,.]+)\s*(\w+)",
                    val,
                    re.IGNORECASE,
                )
                if match:
                    valor_str = match.group(1)
                    moneda_code = match.group(2).upper().strip()
                    try:
                        valor_orig = Decimal(valor_str.replace(",", ""))
                    except Exception:
                        continue
                    transaccion["moneda_original"] = moneda_code
                    transaccion["valor_moneda_original"] = valor_orig
                    return

    # ==================================================================
    # Utilidades: busqueda de secciones
    # ==================================================================

    def _find_transaction_header_row(self, rows: list[list]) -> int:
        """Encuentra la primera fila que es un header de transacciones."""
        for i, row in enumerate(rows):
            row_text = " ".join(str(v) for v in row if v is not None)
            if self.PATRON_HEADER_AUTORIZACION.search(row_text):
                return i
        return -1

    def _find_transaction_sections(self, rows: list[list]) -> list[int]:
        """Encuentra todas las filas que inician secciones de transacciones."""
        sections = []
        for i, row in enumerate(rows):
            row_text = " ".join(str(v) for v in row if v is not None)
            # El header tiene "Numero de autorizacion" (o "Número de autorización")
            if self.PATRON_HEADER_AUTORIZACION.search(row_text):
                sections.append(i)
        return sections

    # ==================================================================
    # Utilidades: parseo de numeros colombianos
    # ==================================================================

    def _parse_colombian_number(self, row: list, prefer_index: int | None = None) -> Decimal | None:
        """Extrae un valor numerico de una fila, manejando formato colombiano.

        El formato colombiano es inconsistente:
        - "17.500.000,00" = 17500000.00 (punto=miles, coma=decimal)
        - "950,421.00" = 950421.00 (coma=miles, punto=decimal)
        - "436.372,51" = 436372.51

        Heuristica: si hay ambos separadores, el de mas a la derecha es el decimal.
        """
        # Primero, buscar en el indice preferido
        if prefer_index is not None and prefer_index < len(row):
            val = row[prefer_index]
            result = self._parse_colombian_number_from_value(val)
            if result is not None:
                return result

        # Buscar en toda la fila
        for val in row:
            result = self._parse_colombian_number_from_value(val)
            if result is not None:
                return result

        return None

    def _parse_colombian_number_from_value(self, val: Any) -> Decimal | None:
        """Parsea un valor individual a Decimal, manejando formato colombiano."""
        if val is None:
            return None

        # Si ya es numerico
        if isinstance(val, int | float):
            if math.isfinite(val):
                return Decimal(str(val))
            return None

        # Si es cadena
        if isinstance(val, str):
            return self._parse_colombian_number_from_string(val)

        # Si es Decimal, retornarlo
        if isinstance(val, Decimal):
            return val

        return None

    def _parse_colombian_number_from_string(self, text: str) -> Decimal | None:
        """Parsea una cadena con formato numerico colombiano a Decimal."""
        if not text:
            return None

        text = text.strip().replace("$", "").replace(" ", "").replace("\u00a0", "")

        if not text:
            return None

        is_negative = text.startswith("-")
        if is_negative:
            text = text[1:]

        # Caso simple: sin separadores o solo con punto decimal
        if "," not in text and "." not in text:
            try:
                result = Decimal(text)
                return -result if is_negative else result
            except Exception:
                return None

        # Caso: solo comas
        if "," in text and "." not in text:
            # Si tiene una sola coma y 1-2 digitos despues → decimal
            parts = text.split(",")
            if len(parts) == 2 and len(parts[1]) <= 2 and len(parts[0]) <= 3:
                try:
                    result = Decimal(text.replace(",", "."))
                    return -result if is_negative else result
                except Exception:
                    return None
            # Multiples comas o 3+ digitos despues → miles
            try:
                result = Decimal(text.replace(",", ""))
                return -result if is_negative else result
            except Exception:
                return None

        # Caso: solo puntos
        if "." in text and "," not in text:
            # Si tiene un solo punto y 1-2 digitos despues → probable decimal
            parts = text.split(".")
            if len(parts) == 2 and len(parts[1]) <= 2:
                try:
                    result = Decimal(text)
                    return -result if is_negative else result
                except Exception:
                    return None
            # Multiples puntos → miles
            try:
                result = Decimal(text.replace(".", ""))
                return -result if is_negative else result
            except Exception:
                return None

        # Caso: ambos separadores (formato colombiano mixto)
        # Heuristica: el separador mas a la derecha es el decimal
        last_dot = text.rfind(".")
        last_comma = text.rfind(",")

        if last_comma > last_dot:
            # Comma es decimal, dot es miles: "17.500.000,00"
            cleaned = text.replace(".", "").replace(",", ".")
        else:
            # Dot es decimal, comma es miles: "950,421.00"
            cleaned = text.replace(",", "")

        try:
            result = Decimal(cleaned)
            return -result if is_negative else result
        except Exception:
            return None

    # ==================================================================
    # Utilidades: parseo de fechas
    # ==================================================================

    def _parse_fecha(self, fecha_raw: Any) -> date | None:
        """Convierte un valor a date, manejando distintos formatos."""
        if fecha_raw is None:
            return None

        if isinstance(fecha_raw, datetime):
            return fecha_raw.date()
        if isinstance(fecha_raw, date):
            return fecha_raw

        if isinstance(fecha_raw, str):
            fecha_str = fecha_raw.strip()
            if not fecha_str:
                return None

            # Formato DD/MM/YYYY (Bancolombia)
            if self.PATRON_FECHA_DDMMYYYY.match(fecha_str):
                try:
                    partes = fecha_str.split("/")
                    return date(int(partes[2]), int(partes[1]), int(partes[0]))
                except (ValueError, IndexError):
                    pass

            # Otros formatos comunes
            for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"):
                try:
                    return datetime.strptime(fecha_str, fmt).date()
                except ValueError:
                    continue

        return None

    def _extract_dates_from_row(self, row: list) -> list[date]:
        """Extrae todas las fechas de una fila."""
        dates = []
        for val in row:
            d = self._parse_fecha(val)
            if d is not None:
                dates.append(d)
        return dates

    # ==================================================================
    # Utilidades: acceso seguro a celdas
    # ==================================================================

    def _safe_str(self, row: list, index: int) -> str:
        """Obtiene un valor de fila como string de forma segura."""
        if index < len(row) and row[index] is not None:
            s = str(row[index]).strip()
            if s.lower() in ("nan", "none", ""):
                return ""
            return s
        return ""
