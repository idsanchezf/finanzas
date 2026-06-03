"""Handlers de CQRS — Implementan la logica de ejecucion de commands y queries.

Los handlers son clases que reciben un command/query y ejecutan la logica de negocio
necesaria, orquestando repositorios, servicios de dominio y publicando eventos.
"""

from src.application.handlers.command_handlers import CommandHandler
from src.application.handlers.query_handlers import QueryHandler

__all__ = [
    "CommandHandler",
    "QueryHandler",
]
