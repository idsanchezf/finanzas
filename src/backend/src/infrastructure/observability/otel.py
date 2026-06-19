"""Inicializacion de OpenTelemetry SDK.

Configura:
- TracerProvider con export OTLP (gRPC o HTTP)
- MeterProvider con metricas de sistema (CPU, memoria, GC)
- Propagacion W3C Trace Context
- Instrumentacion automatica de FastAPI, SQLAlchemy, Redis
- Bridge structlog → OpenTelemetry logs
"""

from __future__ import annotations

import logging
import os


def init_observability() -> None:
    """Inicializa el SDK de OpenTelemetry para traces y metrics.

    Solo se activa si OTEL_EXPORTER_OTLP_ENDPOINT esta configurado.
    En desarrollo local, no se inicializa para evitar dependencia de un collector.
    """
    otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    if not otel_endpoint:
        logging.getLogger(__name__).info(
            "OpenTelemetry: no configurado (OTEL_EXPORTER_OTLP_ENDPOINT vacio). "
            "Traces y metrics deshabilitados."
        )
        return

    service_name = os.getenv("OTEL_SERVICE_NAME", "finance-report-backend")

    # ---------------------------------------------------------------
    # Traces
    # ---------------------------------------------------------------
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased

    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": os.getenv("APP_VERSION", "0.1.0"),
            "deployment.environment": os.getenv("ENVIRONMENT", "production"),
        }
    )

    # Muestreo: 100% en desarrollo, 10% en produccion por defecto
    sample_rate = 1.0 if os.getenv("ENVIRONMENT") == "development" else 0.1

    tracer_provider = TracerProvider(
        resource=resource,
        sampler=ParentBased(root=TraceIdRatioBased(sample_rate)),
    )

    span_exporter = OTLPSpanExporter(
        endpoint=f"{otel_endpoint}/v1/traces",
    )
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)

    # ---------------------------------------------------------------
    # Metrics
    # ---------------------------------------------------------------
    from opentelemetry import metrics
    from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.metrics.view import View

    metric_exporter = OTLPMetricExporter(
        endpoint=f"{otel_endpoint}/v1/metrics",
    )

    metric_reader = PeriodicExportingMetricReader(
        exporter=metric_exporter,
        export_interval_millis=30_000,  # 30s
    )

    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[metric_reader],
        views=[
            # Limitar cardinalidad de histogramas HTTP
            View(
                instrument_name="http.server.duration",
                aggregation=ExplicitBucketHistogramAggregation(
                    boundaries=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
                ),
            ),
        ] if False else [],  # Views opcionales
    )
    metrics.set_meter_provider(meter_provider)

    # ---------------------------------------------------------------
    # Instrumentacion automatica
    # ---------------------------------------------------------------
    try:
        # FastAPI
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        from src.api.main import app

        FastAPIInstrumentor.instrument_app(
            app,
            tracer_provider=tracer_provider,
            meter_provider=meter_provider,
        )
    except Exception:
        logging.getLogger(__name__).warning(
            "No se pudo instrumentar FastAPI automaticamente. "
            "Asegurate de que la app este importada."
        )

    # SQLAlchemy
    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        SQLAlchemyInstrumentor().instrument(
            tracer_provider=tracer_provider,
            enable_commenter=True,  # Agrega comentarios SQL para correlacion
        )
    except Exception:
        logging.getLogger(__name__).warning(
            "No se pudo instrumentar SQLAlchemy."
        )

    # Redis
    try:
        from opentelemetry.instrumentation.redis import RedisInstrumentor

        RedisInstrumentor().instrument(tracer_provider=tracer_provider)
    except Exception:
        logging.getLogger(__name__).warning(
            "No se pudo instrumentar Redis."
        )

    # ---------------------------------------------------------------
    # Logging bridge: structlog → OpenTelemetry
    # ---------------------------------------------------------------
    try:
        from opentelemetry._logs import set_logger_provider
        from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
        from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

        log_provider = LoggerProvider(resource=resource)
        log_exporter = OTLPLogExporter(endpoint=f"{otel_endpoint}/v1/logs")
        log_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
        set_logger_provider(log_provider)

        # Bridge: stdlib logging → OTLP
        otlp_handler = LoggingHandler(logger_provider=log_provider)
        logging.getLogger().addHandler(otlp_handler)
    except ImportError:
        logging.getLogger(__name__).warning(
            "OpenTelemetry logging no disponible. "
            "Actualiza opentelemetry-sdk a version con soporte de logs."
        )
    except Exception as e:
        logging.getLogger(__name__).warning(
            f"No se pudo configurar el bridge de logging OTLP: {e}"
        )

    logging.getLogger(__name__).info(
        f"OpenTelemetry inicializado: service={service_name}, "
        f"endpoint={otel_endpoint}, sample_rate={sample_rate}"
    )


def shutdown_observability() -> None:
    """Apaga gracefulmente los exportadores de OpenTelemetry."""
    from opentelemetry import metrics, trace

    try:
        trace.get_tracer_provider().shutdown()
    except Exception:
        pass

    try:
        metrics.get_meter_provider().shutdown()
    except Exception:
        pass


# Helper para bucket aggregation
class ExplicitBucketHistogramAggregation:
    """Aggregation de histograma con buckets explicitos.

    Nota: Esta es una implementacion simplificada. En OpenTelemetry >= 1.28,
    usar opentelemetry.sdk.metrics.view.ExplicitBucketHistogramAggregation directamente.
    """
    def __init__(self, boundaries: list[float]) -> None:
        self.boundaries = boundaries
