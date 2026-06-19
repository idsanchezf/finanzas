"""Data Transfer Objects — DTOs compartidos entre capas."""

from src.application.dtos.dashboard_dto import DashboardSummaryDTO
from src.application.dtos.extracto_dto import ExtractoDTO
from src.application.dtos.transaccion_dto import TransaccionDTO

__all__ = [
    "ExtractoDTO",
    "TransaccionDTO",
    "DashboardSummaryDTO",
]
