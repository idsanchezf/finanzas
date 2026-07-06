"""Servicio de dominio — Clasificador de gastos.

Orquesta la clasificacion hibrida (reglas + ML) de transacciones.
Define la interfaz que la capa de infraestructura implementara con scikit-learn.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ClasificadorGastos(ABC):
    """Servicio de dominio para clasificacion de transacciones.

    La capa de infraestructura implementa la logica concreta:
    - Fase 1: Reglas deterministicas (palabras clave, regex, traducciones)
    - Fase 2: ML (TF-IDF + cosine similarity, embeddings semanticos)
    """

    @abstractmethod
    def clasificar_por_reglas(
        self, comercio: str, categorias: list[Any]
    ) -> tuple[Any | None, float]:
        """Clasifica un comercio usando reglas deterministicas.

        Args:
            comercio: Nombre original del comercio en el extracto.
            categorias: Lista de categorias con sus palabras clave.

        Returns:
            Tupla (categoria, confidence 0-100) o (None, 0) si no hay match.
        """
        ...

    @abstractmethod
    def clasificar_por_ml(
        self, comercio: str, transacciones_previas: list[Any]
    ) -> tuple[Any | None, float]:
        """Clasifica un comercio usando aprendizaje previo (ML).

        Args:
            comercio: Nombre original del comercio.
            transacciones_previas: Transacciones ya clasificadas por el usuario.

        Returns:
            Tupla (categoria, confidence 0-100) o (None, 0) si no hay datos.
        """
        ...

    @abstractmethod
    def aprender_correccion(
        self, comercio: str, categoria_id: Any, categoria_anterior: Any | None
    ) -> None:
        """Aprende de una correccion del usuario para mejorar futuras clasificaciones.

        Args:
            comercio: Nombre original del comercio.
            categoria_id: Nueva categoria asignada por el usuario.
            categoria_anterior: Categoria anterior (si existia).
        """
        ...

    @abstractmethod
    def clasificar(
        self, comercio: str, categorias: list[Any], historial: list[Any]
    ) -> tuple[Any | None, float, str]:
        """Pipeline completo de clasificacion hibrida.

        1. Intenta reglas deterministicas.
        2. Si no hay match o confidence < 70%, intenta ML.
        3. Retorna la mejor clasificacion.

        Args:
            comercio: Nombre del comercio a clasificar.
            categorias: Categorias disponibles.
            historial: Transacciones previamente clasificadas.

        Returns:
            Tupla (categoria, confidence, fuente: "rules"|"ml"|"none").
        """
        ...
