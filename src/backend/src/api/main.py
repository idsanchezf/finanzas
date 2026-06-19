"""FastAPI Application — Entry point del backend Finance Report.

Configura la aplicacion FastAPI con:
- Lifespan para conexion a BD, Redis, RabbitMQ al iniciar/detener
- Middleware: CORS, logging estructurado, error handler, correlation ID
- Routers: 10 grupos de endpoints REST
- Health checks: /health (liveness) y /health/ready (readiness)
- OpenAPI docs: /docs (Swagger UI) y /redoc
"""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Cargar variables de entorno antes de importar modulos
load_dotenv()

# Configurar structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer() if os.getenv("ENVIRONMENT") == "development"
        else structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Inicializar OpenTelemetry (traces + metrics) si esta configurado
try:
    from src.infrastructure.observability.otel import init_observability
    init_observability()
except Exception as e:
    logging.getLogger(__name__).warning(
        f"No se pudo inicializar OpenTelemetry: {e}"
    )


# ============================================================
# Lifespan — Inicializacion y cierre de recursos
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Maneja el ciclo de vida de la aplicacion.

    Al iniciar: conecta a BD, Redis, RabbitMQ.
    Al detener: cierra conexiones gracefulmente.
    """
    logger.info("Iniciando Finance Report API...")

    # Inicializar conexiones aqui si es necesario
    # Ej: await get_redis_client(), await get_event_bus()

    yield

    # Cleanup al detener
    logger.info("Deteniendo Finance Report API...")
    try:
        from src.infrastructure.cache.redis_client import _redis_client
        from src.infrastructure.messaging.rabbitmq import _event_bus

        if _redis_client:
            await _redis_client.disconnect()
        if _event_bus:
            await _event_bus.disconnect()
    except Exception:
        pass


# ============================================================
# Crear aplicacion FastAPI
# ============================================================
app = FastAPI(
    title="Finance Report API",
    description="API REST para clasificacion y analisis de gastos personales. "
    "Procesa extractos bancarios, clasifica transacciones con ML, "
    "y ofrece dashboards financieros con asistente IA.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ============================================================
# Middleware
# ============================================================
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de logging y correlation ID
from src.api.middleware.error_handler import ErrorHandlerMiddleware
from src.api.middleware.logging import LoggingMiddleware

app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(LoggingMiddleware)


# ============================================================
# Health checks
# ============================================================
@app.get("/health", tags=["Health"])
async def health_liveness():
    """Liveness probe — verifica que la aplicacion esta viva."""
    return {"status": "ok", "service": "finance-report-api"}


@app.get("/health/ready", tags=["Health"])
async def health_readiness():
    """Readiness probe — verifica que la aplicacion puede recibir trafico.

    Comprueba conexion a BD y Redis.
    """
    checks = {"database": False, "redis": False}

    # Verificar BD
    try:
        from sqlalchemy import text

        from src.infrastructure.persistence.unit_of_work import create_session_factory

        db_url = os.getenv("DATABASE_URL", "")
        if db_url:
            session_factory = await create_session_factory(db_url)
            async with session_factory() as session:
                await session.execute(text("SELECT 1"))
            checks["database"] = True
    except Exception as e:
        logger.warning("Health check: base de datos no disponible", error=str(e))

    # Verificar Redis
    try:
        from src.infrastructure.cache.redis_client import get_redis_client
        redis = await get_redis_client()
        await redis.client.ping()
        checks["redis"] = True
    except Exception as e:
        logger.warning("Health check: Redis no disponible", error=str(e))

    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503

    return JSONResponse(
        content={"status": "ok" if all_healthy else "degraded", "checks": checks},
        status_code=status_code,
    )


# ============================================================
# Routers — API v1
# ============================================================
from src.api.routers import (
    auth,
    budgets,
    categories,
    chat,
    dashboard,
    extracts,
    insights,
    merchants,
    notifications,
    transactions,
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Autenticacion"])
app.include_router(extracts.router, prefix="/api/v1/extracts", tags=["Extractos"])
app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["Transacciones"])
app.include_router(categories.router, prefix="/api/v1/categories", tags=["Categorias"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(insights.router, prefix="/api/v1/insights", tags=["Insights"])
app.include_router(budgets.router, prefix="/api/v1/budgets", tags=["Presupuestos"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat IA"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notificaciones"])
app.include_router(merchants.router, prefix="/api/v1/merchants", tags=["Comercios"])


# ============================================================
# Entry point para ejecucion directa
# ============================================================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("ENVIRONMENT") == "development",
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
