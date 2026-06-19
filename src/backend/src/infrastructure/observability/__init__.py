"""Modulo de observabilidad — OpenTelemetry tracing, metrics y logging.

Inicializa el SDK de OpenTelemetry con:
- Traces: propagacion W3C Trace Context, export OTLP a Grafana Cloud
- Metrics: Prometheus endpoint (/metrics), system metrics
- Logs: integracion structlog → OTLP (via logging bridge)
"""

from src.infrastructure.observability.otel import init_observability, shutdown_observability

__all__ = ["init_observability", "shutdown_observability"]
