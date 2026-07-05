"""Metricas Prometheus — Contadores e histogramas de negocio.

Incluye:
- extractos_duplicated_total (feat-003): contador de extractos duplicados
- Metricas base del sistema via prometheus_client
- Endpoint /metrics para scraping por Prometheus
"""

from __future__ import annotations

import logging
from typing import Any

from prometheus_client import Counter, Gauge, Histogram, generate_latest
from prometheus_client import REGISTRY as PROMETHEUS_REGISTRY

logger = logging.getLogger(__name__)

# ============================================================
# Contadores de negocio
# ============================================================

# feat-003: Extractos duplicados
extracts_duplicated_total = Counter(
    "extracts_duplicated_total",
    "Total de intentos de carga de extractos duplicados detectados",
    labelnames=["detection_method"],
    # detection_method: "preflight" | "race_condition"
)

# Extractos cargados exitosamente
extracts_uploaded_total = Counter(
    "extracts_uploaded_total",
    "Total de extractos cargados exitosamente",
    labelnames=["banco"],
)

# Errores en carga de extractos (por codigo de error)
extracts_upload_errors_total = Counter(
    "extracts_upload_errors_total",
    "Total de errores en carga de extractos",
    labelnames=["error_code"],
    # error_code: EXTRACTO_DUPLICADO, VALIDACION_FALLIDA, TARJETA_NO_ENCONTRADA
)

# Transacciones procesadas
transactions_processed_total = Counter(
    "transactions_processed_total",
    "Total de transacciones procesadas",
)

# Clasificaciones realizadas
classifications_total = Counter(
    "classifications_total",
    "Total de clasificaciones realizadas",
    labelnames=["source"],
    # source: "auto" | "manual"
)

# ============================================================
# Histogramas de latencia
# ============================================================

# Duracion de carga de extractos
extract_upload_duration_seconds = Histogram(
    "extract_upload_duration_seconds",
    "Duracion del proceso de carga de extractos en segundos",
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0],
)

# Duracion de parseo de Excel
excel_parse_duration_seconds = Histogram(
    "excel_parse_duration_seconds",
    "Duracion del parseo de archivos Excel en segundos",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)

# ============================================================
# Gauges
# ============================================================

# Extractos en estado PENDING/PARSING (por procesar)
extracts_pending_processing = Gauge(
    "extracts_pending_processing",
    "Numero de extractos pendientes de procesamiento",
)

# Tasa de duplicados (porcentaje de intentos duplicados)
duplicate_detection_rate = Gauge(
    "duplicate_detection_rate",
    "Porcentaje de intentos de carga que resultan duplicados (ventana movil)",
)


# ============================================================
# Helpers para incrementar contadores
# ============================================================

def record_extract_duplicated(detection_method: str) -> None:
    """Registra un intento de carga de extracto duplicado.

    Args:
        detection_method: "preflight" (pre-flight check en handler)
                          o "race_condition" (constraint BD)
    """
    extracts_duplicated_total.labels(detection_method=detection_method).inc()
    logger.info(
        "Metrica: extracto_duplicado registrado",
        detection_method=detection_method,
    )


def record_extract_uploaded(banco: str = "desconocido") -> None:
    """Registra un extracto cargado exitosamente."""
    extracts_uploaded_total.labels(banco=banco).inc()


def record_extract_upload_error(error_code: str) -> None:
    """Registra un error en la carga de extractos."""
    extracts_upload_errors_total.labels(error_code=error_code).inc()


def record_transaction_processed() -> None:
    """Registra una transaccion procesada."""
    transactions_processed_total.inc()


def get_metrics_bytes() -> bytes:
    """Retorna las metricas en formato texto para el endpoint /metrics."""
    return generate_latest(PROMETHEUS_REGISTRY)


def get_metrics_text() -> str:
    """Retorna las metricas como string (para debug)."""
    return generate_latest(PROMETHEUS_REGISTRY).decode("utf-8")
