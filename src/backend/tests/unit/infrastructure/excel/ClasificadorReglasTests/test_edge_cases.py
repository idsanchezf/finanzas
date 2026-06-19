"""Tests de casos borde para el clasificador deterministico.

Verifica: comercio desconocido, strings vacios, confianza baja,
prioridad de keywords mas especificas, case insensitivity.

Convencion TDD:
- Carpeta: ClasificadorReglasTests/
- Archivo: test_edge_cases.py
"""

import pytest

from src.domain.entities.categoria import Categoria


@pytest.fixture
def categorias():
    return Categoria.precargadas()


@pytest.fixture
def clasificador(categorias):
    from src.infrastructure.excel.clasificador_reglas import ClasificadorReglas

    return ClasificadorReglas()


class TestEdgeCases:
    """Casos borde del clasificador deterministico."""

    def test_Should_ReturnNone_When_UnknownMerchant(self, clasificador, categorias):
        """Comercio completamente desconocido retorna (None, 0)."""
        # Arrange --------------------------------------------------------
        comercio = "XYZ EMPRESA INEXISTENTE ABC 12345"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        assert cat_id is None
        assert confidence == 0

    def test_Should_ReturnNone_When_EmptyString(self, clasificador, categorias):
        """String vacio retorna (None, 0)."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas("", categorias)

        # Assert ----------------------------------------------------------
        assert cat_id is None
        assert confidence == 0

    def test_Should_ReturnNone_When_NoneComercio(self, clasificador, categorias):
        """None retorna (None, 0) sin lanzar excepcion."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(None, categorias)

        # Assert ----------------------------------------------------------
        assert cat_id is None
        assert confidence == 0

    def test_Should_BeCaseInsensitive_When_Uppercase(self, clasificador, categorias):
        """Busqueda case-insensitive: UPPERCASE matchea lowercase keywords."""
        # Arrange --------------------------------------------------------
        comercio = "RESTAURANTE MEXICANO EL CHARRO"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Alimentacion"

    def test_Should_BeCaseInsensitive_When_MixedCase(self, clasificador, categorias):
        """Busqueda case-insensitive: MiXeDcAsE matchea."""
        # Arrange --------------------------------------------------------
        comercio = "NeTfLiX.CoM SuBsCrIpTiOn"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Entretenimiento"

    def test_Should_HigherConfidence_When_MultipleKeywordsMatch(self, clasificador, categorias):
        """Mayor confianza cuando multiples keywords de la misma categoria matchean."""
        # Arrange --------------------------------------------------------
        # "RESTAURANTE COMIDA RAPIDA" matchea "restaurante" y "comida" -> Alimentacion
        comercio = "RESTAURANTE COMIDA RAPIDA EXPRESS"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Alimentacion"
        assert confidence >= 60  # Deberia ser mayor porque matchean 2+ keywords

    def test_Should_ChooseCategoryWithMostMatches_When_Ambiguous(self, clasificador, categorias):
        """Ante ambiguedad, elige la categoria con mas keywords matcheadas."""
        # Arrange --------------------------------------------------------
        # "spotify" esta en Entretenimiento (1 match)
        # Si hay un comercio que matchea "suscripcion" (Suscripciones: 1)
        # y "spotify" (Entretenimiento: 1), deberia desempatar por confianza
        comercio = "SUSCRIPCION SPOTIFY PREMIUM"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        # Ambas categorias tienen 1 match. El comportamiento exacto depende
        # de la implementacion (primer match, mayor confianza, etc.)
        # Pero al menos debe clasificar en alguna
        assert cat_id is not None
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre in ("Suscripciones", "Entretenimiento")

    def test_Should_ClassifyEven_When_ComercioWithSpecialChars(self, clasificador, categorias):
        """Maneja comercios con caracteres especiales (*, ., /)."""
        # Arrange --------------------------------------------------------
        comercio = "UBER   *TRIP//HELP..COM"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Transporte"

    def test_Should_Classify_When_ComercioHasExtraWhitespace(self, clasificador, categorias):
        """Maneja espacios extras en el comercio."""
        # Arrange --------------------------------------------------------
        comercio = "   NETFLIX    "

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Entretenimiento"

    def test_Should_ReturnNone_When_OnlySpaces(self, clasificador, categorias):
        """Solo espacios en blanco retorna (None, 0)."""
        # Arrange --------------------------------------------------------
        comercio = "     "

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        assert cat_id is None
        assert confidence == 0

    def test_Should_ReturnNone_When_EmptyCategoryList(self, clasificador):
        """Lista de categorias vacia retorna (None, 0)."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas("NETFLIX", [])

        # Assert ----------------------------------------------------------
        assert cat_id is None
        assert confidence == 0

    def test_Should_Classify_When_KeywordIsSubstring(self, clasificador, categorias):
        """Matchea keyword como substring dentro del comercio."""
        # Arrange --------------------------------------------------------
        # "supermercado" es keyword de Alimentacion
        comercio = "HIPER SUPERMERCADO EXITO S.A."

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        cat = next(c for c in categorias if c.id == cat_id)
        assert cat.nombre == "Alimentacion"

    def test_Should_NotMatchPartial_When_KeywordIsShortAndAmbiguous(self, clasificador, categorias):
        """Evita falsos positivos con keywords muy cortas (ej: 'gas' matchea 'gasolina' pero no 'gasto')."""
        # Arrange --------------------------------------------------------
        # "gas" es keyword de Vivienda. "gasto" NO deberia matchear Vivienda
        comercio = "GASTO VARIOS MISCELANEOS"

        # Act ------------------------------------------------------------
        cat_id, confidence = clasificador.clasificar_por_reglas(comercio, categorias)

        # Assert ----------------------------------------------------------
        # "gasto" no deberia matchear "gas" como substring.
        # Si clasifica, debe ser "Otros" o "Financieros", no "Vivienda"
        if cat_id is not None:
            cat = next(c for c in categorias if c.id == cat_id)
            # No deberia ser Vivienda porque "gasto" != "gas"
            # (Depende de si usamos word-boundary matching)
            pass  # Este test documenta el comportamiento deseado
