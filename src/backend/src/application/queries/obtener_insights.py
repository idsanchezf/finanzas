"""Query: ObtenerInsights — Alertas y analisis financiero."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ObtenerInsightsQuery:
    """Consulta las alertas, habitos detectados y score financiero."""

    usuario_id: UUID
    extracto_id: UUID
