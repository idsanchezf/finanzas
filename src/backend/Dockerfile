# ============================================================
# Finance Report — Backend Dockerfile (multi-stage)
# ============================================================
# Etapas:
#   builder    — Instala dependencias de produccion (poetry)
#   development — Imagen para desarrollo con hot-reload
#   production — Imagen final optimizada para produccion
# ============================================================

ARG PYTHON_VERSION=3.12-slim
FROM python:${PYTHON_VERSION} AS base

# Variables de build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

WORKDIR /app


# ============================================================
# Stage: builder — Dependencias de produccion
# ============================================================
FROM base AS builder

COPY pyproject.toml poetry.lock* ./

# Instalar solo dependencias de produccion
RUN poetry install --only main --no-root --no-directory


# ============================================================
# Stage: development — Para desarrollo con hot-reload
# ============================================================
FROM base AS development

# Instalar dependencias de desarrollo
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-root --no-directory

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
