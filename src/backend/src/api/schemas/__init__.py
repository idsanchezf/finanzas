"""Schemas Pydantic v2 — Modelos de request/response para validacion automatica.

FastAPI usa estos schemas para validacion, serializacion y documentacion OpenAPI.
Separados de las entidades de dominio para mantener la independencia de capas.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================
# Extractos
# ============================================================
class ExtractUploadResponse(BaseModel):
    extract_id: UUID
    estado: str
    progress_pct: int


class ExtractStatusResponse(BaseModel):
    status: str
    progress_pct: int
    message: str | None = None


# ============================================================
# Transacciones
# ============================================================
class UpdateCategoryRequest(BaseModel):
    category_id: UUID


class BulkUpdateCategoryRequest(BaseModel):
    transaction_ids: list[UUID]
    category_id: UUID


class TransactionResponse(BaseModel):
    id: UUID
    extracto_id: UUID | None = None
    fecha: date | None = None
    comercio: str
    valor: float
    categoria_id: UUID | None = None
    confidence: float | None = None
    es_cuota: bool = False


# ============================================================
# Dashboard
# ============================================================
class DashboardSummaryResponse(BaseModel):
    total_gastado: float
    total_ingresos: float
    promedio_diario: float
    pct_cupo_utilizado: float
    dias_para_corte: int
    variacion_vs_anterior: float = 0.0


# ============================================================
# Categorias
# ============================================================
class CreateCategoryRequest(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    icono: str = "📁"
    color: str = "#6B7280"
    parent_id: UUID | None = None


# ============================================================
# Presupuestos
# ============================================================
class CreateBudgetRequest(BaseModel):
    category_id: UUID
    limite_mensual: Decimal = Field(..., gt=0)
    alerta_80pct: bool = True
    alerta_100pct: bool = True


# ============================================================
# Metas
# ============================================================
class CreateGoalRequest(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=200)
    monto_objetivo: Decimal = Field(..., gt=0)
    fecha_deseada: date | None = None


# ============================================================
# Chat
# ============================================================
class ChatRequest(BaseModel):
    mensaje: str = Field(..., min_length=1)
    session_id: UUID | None = None


# ============================================================
# Autenticacion
# ============================================================
class LoginRequest(BaseModel):
    provider: str = Field(..., pattern="^(google|microsoft)$")
    id_token: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    user: dict[str, Any]
