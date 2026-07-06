"""Comandos CQRS — Operaciones de escritura (mutaciones de estado).

Cada comando es un DTO inmutable que representa la intencion del usuario.
Los handlers procesan estos comandos y emiten eventos de dominio.
"""

from src.application.commands.cargar_extracto import CargarExtractoCommand
from src.application.commands.clasificar_masivas import ClasificarTransaccionesMasivasCommand
from src.application.commands.clasificar_transaccion import ClasificarTransaccionCommand
from src.application.commands.corregir_categoria import CorregirCategoriaCommand
from src.application.commands.crear_categoria import CrearCategoriaCommand
from src.application.commands.crear_meta import CrearMetaAhorroCommand
from src.application.commands.crear_presupuesto import CrearPresupuestoCommand

__all__ = [
    "CargarExtractoCommand",
    "ClasificarTransaccionCommand",
    "ClasificarTransaccionesMasivasCommand",
    "CorregirCategoriaCommand",
    "CrearCategoriaCommand",
    "CrearPresupuestoCommand",
    "CrearMetaAhorroCommand",
]
