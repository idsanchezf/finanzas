"""Interfaces de repositorio — Contratos abstractos (sin implementacion).

Definen el contrato que la capa de infraestructura debe cumplir.
La capa de dominio solo depende de estas interfaces, no de la implementacion concreta.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Any
from uuid import UUID


class IUnitOfWork(ABC):
    """Unidad de trabajo — gestiona transacciones de base de datos.

    Garantiza atomicidad en operaciones que involucran multiples repositorios.
    """

    @abstractmethod
    async def commit(self) -> None:
        """Confirma la transaccion actual."""
        ...

    @abstractmethod
    async def rollback(self) -> None:
        """Revierte la transaccion actual."""
        ...

    @abstractmethod
    async def flush(self) -> None:
        """Flush de cambios pendientes sin commit."""
        ...

    @abstractmethod
    async def __aenter__(self) -> IUnitOfWork:
        ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        ...


class IUsuarioRepository(ABC):
    """Repositorio de usuarios."""

    @abstractmethod
    async def get_by_id(self, usuario_id: UUID) -> Any | None:
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> Any | None:
        ...

    @abstractmethod
    async def get_by_auth_provider(self, provider: str, provider_id: str) -> Any | None:
        ...

    @abstractmethod
    async def save(self, usuario: Any) -> Any:
        ...

    @abstractmethod
    async def delete(self, usuario_id: UUID) -> None:
        ...


class ITarjetaRepository(ABC):
    """Repositorio de tarjetas."""

    @abstractmethod
    async def get_by_id(self, tarjeta_id: UUID) -> Any | None:
        ...

    @abstractmethod
    async def get_by_usuario(self, usuario_id: UUID) -> list[Any]:
        ...

    @abstractmethod
    async def save(self, tarjeta: Any) -> Any:
        ...

    @abstractmethod
    async def delete(self, tarjeta_id: UUID) -> None:
        ...


class IExtractoRepository(ABC):
    """Repositorio de extractos."""

    @abstractmethod
    async def get_by_id(self, extracto_id: UUID) -> Any | None:
        ...

    @abstractmethod
    async def get_by_usuario(
        self, usuario_id: UUID, page: int = 1, size: int = 12
    ) -> tuple[list[Any], int]:
        ...

    @abstractmethod
    async def get_by_tarjeta_and_periodo(
        self, tarjeta_id: UUID, periodo_inicio: Any, periodo_fin: Any
    ) -> Any | None:
        ...

    @abstractmethod
    async def get_by_tarjeta_and_file_hash(
        self, tarjeta_id: UUID, file_hash: str
    ) -> Any | None:
        ...

    @abstractmethod
    async def save(self, extracto: Any) -> Any:
        ...

    @abstractmethod
    async def delete(self, extracto_id: UUID) -> None:
        ...


class ITransaccionRepository(ABC):
    """Repositorio de transacciones."""

    @abstractmethod
    async def get_by_id(self, transaccion_id: UUID) -> Any | None:
        ...

    @abstractmethod
    async def get_by_extracto(
        self, extracto_id: UUID, filters: dict[str, Any] | None = None
    ) -> list[Any]:
        ...

    @abstractmethod
    async def get_by_usuario(
        self, usuario_id: UUID, filters: dict[str, Any] | None = None,
        page: int = 1, size: int = 50
    ) -> tuple[list[Any], int]:
        ...

    @abstractmethod
    async def get_unclassified(self, extracto_id: UUID) -> list[Any]:
        ...

    @abstractmethod
    async def search_comercio(self, usuario_id: UUID, query: str) -> list[Any]:
        ...

    @abstractmethod
    async def save(self, transaccion: Any) -> Any:
        ...

    @abstractmethod
    async def bulk_save(self, transacciones: list[Any]) -> list[Any]:
        ...

    @abstractmethod
    async def bulk_update_category(
        self, transaccion_ids: list[UUID], categoria_id: UUID
    ) -> int:
        ...

    @abstractmethod
    async def buscar_por_periodo(
        self,
        usuario_id: UUID,
        fecha_inicio: date,
        fecha_fin: date,
        page: int = 1,
        size: int = 50,
    ) -> tuple[list[Any], int]:
        """Busca transacciones de un usuario en un rango de fechas con paginacion."""
        ...


class ICategoriaRepository(ABC):
    """Repositorio de categorias."""

    @abstractmethod
    async def get_by_id(self, categoria_id: UUID) -> Any | None:
        ...

    @abstractmethod
    async def get_all(self, usuario_id: UUID | None = None) -> list[Any]:
        ...

    @abstractmethod
    async def get_predefinidas(cls) -> list[Any]:
        ...

    @abstractmethod
    async def save(self, categoria: Any) -> Any:
        ...

    @abstractmethod
    async def delete(self, categoria_id: UUID) -> None:
        ...

    @abstractmethod
    async def buscar_por_nombre(
        self, nombre: str, usuario_id: UUID | None = None
    ) -> list[Any]:
        """Busca categorias por coincidencia parcial en el nombre."""
        ...


class IPresupuestoRepository(ABC):
    """Repositorio de presupuestos."""

    @abstractmethod
    async def get_by_id(self, presupuesto_id: UUID) -> Any | None:
        ...

    @abstractmethod
    async def get_by_usuario(self, usuario_id: UUID) -> list[Any]:
        ...

    @abstractmethod
    async def save(self, presupuesto: Any) -> Any:
        ...

    @abstractmethod
    async def delete(self, presupuesto_id: UUID) -> None:
        ...


__all__ = [
    "IUnitOfWork",
    "IUsuarioRepository",
    "ITarjetaRepository",
    "IExtractoRepository",
    "ITransaccionRepository",
    "ICategoriaRepository",
    "IPresupuestoRepository",
]
