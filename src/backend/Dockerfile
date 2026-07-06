# ============================================================
# Finance Report — Backend Dockerfile (multi-stage)
# ============================================================
# Etapas:
#   builder    — Instala dependencias de produccion (pip)
#   development — Imagen para desarrollo con hot-reload
#   production — Imagen final optimizada para produccion
#
# Optimizacion: usa pip install -r requirements.txt en vez de
# poetry install para builds mas rapidos (evita resolver
# dependencias transitivas sin poetry.lock).
# ============================================================

ARG PYTHON_VERSION=3.12-slim
FROM python:${PYTHON_VERSION} AS base

# Variables de build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=120 \
    PIP_RETRIES=5

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app


# ============================================================
# Stage: builder — Dependencias de produccion
# ============================================================
FROM base AS builder

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


# ============================================================
# Stage: development — Para desarrollo con hot-reload
# ============================================================
FROM builder AS development

# Instalar dependencias de desarrollo
COPY requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "debug"]


# ============================================================
# Stage: production — Imagen final optimizada
# ============================================================
FROM python:${PYTHON_VERSION} AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root
RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser

WORKDIR /app

# Copiar dependencias del builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copiar codigo fuente
COPY src/ ./src/
COPY alembic.ini .
COPY alembic/ ./alembic/

# Asegurar permisos
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--log-level", "info"]
