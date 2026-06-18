"""Clasificador deterministico por reglas — Implementacion concreta.

Motor de clasificacion basado en palabras clave de las 14 categorias
predefinidas. Usa busqueda case-insensitive de substrings con scoring
para determinar la categoria mas probable y un nivel de confianza.

Algoritmo:
1. Normaliza el nombre del comercio (lowercase, strip).
2. Para cada categoria, cuenta cuantas palabras clave matchean
   como substrings en el comercio normalizado.
3. Calcula confianza basada en:
   - Numero de keywords matcheadas
   - Longitud de la keyword vs longitud del comercio
4. Retorna la categoria con mayor score y su confianza (0-100).
"""

from __future__ import annotations

import re
from typing import Any


class ClasificadorReglas:
    """Clasificador deterministico basado en reglas de palabras clave.

    Implementa la interfaz ClasificadorGastos para la fase 1 del
    motor hibrido (reglas deterministicas).
    """

    # Umbral minimo de confianza para considerar una clasificacion valida
    CONFIDENCE_THRESHOLD = 20.0

    # Maxima confianza achievable por reglas (no llega a 100, deja espacio para ML)
    MAX_CONFIDENCE = 90.0

    # Confianza base cuando hay al menos un match
    BASE_CONFIDENCE = 55.0

    def clasificar_por_reglas(
        self, comercio: str | None, categorias: list[Any]
    ) -> tuple[Any | None, float]:
        """Clasifica un comercio usando reglas deterministicas.

        Args:
            comercio: Nombre original del comercio en el extracto.
            categorias: Lista de entidades Categoria con palabras_clave.

        Returns:
            Tupla (categoria_id, confidence 0-100) o (None, 0) si no hay match.
        """
        # Validaciones tempranas
        if comercio is None or not isinstance(comercio, str):
            return None, 0.0

        comercio_norm = comercio.strip().lower()
        if not comercio_norm:
            return None, 0.0

        if not categorias:
            return None, 0.0

        # Scoring: para cada categoria, contar keywords que matchean
        best_category_id = None
        best_score = 0
        best_match_count = 0
        best_confidence = 0.0

        for cat in categorias:
            if not hasattr(cat, "palabras_clave") or not cat.palabras_clave:
                continue

            match_count = 0
            total_keyword_len = 0
            for keyword in cat.palabras_clave:
                keyword_lower = keyword.strip().lower()
                if not keyword_lower:
                    continue
                if keyword_lower in comercio_norm:
                    match_count += 1
                    total_keyword_len += len(keyword_lower)

            if match_count == 0:
                continue

            # Score compuesto: match_count pesa mas, keyword_len como tiebreaker
            score = match_count * 100 + total_keyword_len

            # Calcular confianza para esta categoria
            confidence = self.BASE_CONFIDENCE
            # Bonus por multiples keywords
            confidence += (match_count - 1) * 15
            # Bonus por keywords largas (muy especificas)
            if total_keyword_len >= 10:
                confidence += 10
            if total_keyword_len >= 15:
                confidence += 10

            if score > best_score or (score == best_score and match_count > best_match_count):
                best_score = score
                best_match_count = match_count
                best_category_id = cat.id
                best_confidence = min(self.MAX_CONFIDENCE, confidence)

        if best_category_id is None:
            return None, 0.0

        return best_category_id, best_confidence

    def clasificar_por_ml(
        self, comercio: str, transacciones_previas: list[Any]
    ) -> tuple[Any | None, float]:
        """Fase 2: ML — No implementado en MVP (solo reglas)."""
        return None, 0.0

    def aprender_correccion(
        self, comercio: str, categoria_id: Any, categoria_anterior: Any | None
    ) -> None:
        """Aprendizaje de correcciones — No implementado en MVP."""
        pass

    def clasificar(
        self, comercio: str, categorias: list[Any], historial: list[Any]
    ) -> tuple[Any | None, float, str]:
        """Pipeline completo de clasificacion hibrida.

        1. Intenta reglas deterministicas.
        2. Si no hay match o confidence < 70%, intenta ML.
        3. Retorna la mejor clasificacion.

        En MVP, solo usa reglas (ML no implementado).
        """
        cat_id, confidence = self.clasificar_por_reglas(comercio, categorias)

        if cat_id is not None and confidence >= 70:
            return cat_id, confidence, "rules"

        if cat_id is not None:
            return cat_id, confidence, "rules"

        # Intentar ML si hubiera implementacion
        ml_id, ml_conf = self.clasificar_por_ml(comercio, historial)
        if ml_id is not None:
            return ml_id, ml_conf, "ml"

        return None, 0.0, "none"
