"""Tests para gestion de palabras clave de Categoria.

Verifica agregar_palabras_clave() y remover_palabras_clave().

Convencion TDD:
- Carpeta: CategoriaTests/
- Archivo: test_palabras_clave.py
"""

from src.domain.entities.categoria import Categoria


class TestAgregarPalabrasClave:
    """Tests para agregar_palabras_clave()."""

    def test_Should_AddNewWord_When_NotAlreadyPresent(self):
        """Agrega palabra que no existe en la lista."""
        # Arrange --------------------------------------------------------
        cat = Categoria(nombre="Alimentacion")

        # Act ------------------------------------------------------------
        cat.agregar_palabras_clave(["restaurante"])

        # Assert ----------------------------------------------------------
        assert "restaurante" in cat.palabras_clave
        assert len(cat.palabras_clave) == 1

    def test_Should_NotDuplicate_When_WordAlreadyExists(self):
        """No duplica palabra que ya existe."""
        # Arrange --------------------------------------------------------
        cat = Categoria(
            nombre="Alimentacion",
            palabras_clave=["restaurante", "comida"],
        )

        # Act ------------------------------------------------------------
        cat.agregar_palabras_clave(["restaurante"])

        # Assert ----------------------------------------------------------
        assert len(cat.palabras_clave) == 2

    def test_Should_AddMultipleWords_When_ListProvided(self):
        """Agrega multiples palabras a la vez."""
        # Arrange --------------------------------------------------------
        cat = Categoria(nombre="Transporte")

        # Act ------------------------------------------------------------
        cat.agregar_palabras_clave(["uber", "taxi", "bus"])

        # Assert ----------------------------------------------------------
        assert len(cat.palabras_clave) == 3
        assert "uber" in cat.palabras_clave
        assert "taxi" in cat.palabras_clave
        assert "bus" in cat.palabras_clave

    def test_Should_Deduplicate_When_SomeWordsExist(self):
        """Solo agrega palabras nuevas; no duplica existentes."""
        # Arrange --------------------------------------------------------
        cat = Categoria(
            nombre="Entretenimiento",
            palabras_clave=["netflix", "spotify"],
        )

        # Act ------------------------------------------------------------
        cat.agregar_palabras_clave(["netflix", "disney", "hbo"])

        # Assert ----------------------------------------------------------
        assert set(cat.palabras_clave) == {"netflix", "spotify", "disney", "hbo"}

    def test_Should_AddCaseInsensitive_When_DifferentCase(self):
        """Las palabras se agregan tal cual; no hay normalizacion de case."""
        # Arrange --------------------------------------------------------
        cat = Categoria(nombre="Test")

        # Act ------------------------------------------------------------
        cat.agregar_palabras_clave(["UBER", "uber"])

        # Assert ----------------------------------------------------------
        assert len(cat.palabras_clave) == 2  # Se agregan ambas como diferentes
        assert "UBER" in cat.palabras_clave
        assert "uber" in cat.palabras_clave


class TestRemoverPalabrasClave:
    """Tests para remover_palabras_clave()."""

    def test_Should_RemoveExistingWord_When_Present(self):
        """Elimina palabra que existe en la lista."""
        # Arrange --------------------------------------------------------
        cat = Categoria(
            nombre="Alimentacion",
            palabras_clave=["restaurante", "comida", "almuerzo"],
        )

        # Act ------------------------------------------------------------
        cat.remover_palabras_clave(["comida"])

        # Assert ----------------------------------------------------------
        assert "comida" not in cat.palabras_clave
        assert len(cat.palabras_clave) == 2
        assert "restaurante" in cat.palabras_clave
        assert "almuerzo" in cat.palabras_clave

    def test_Should_RemoveMultipleWords_When_AllPresent(self):
        """Elimina multiples palabras existentes."""
        # Arrange --------------------------------------------------------
        cat = Categoria(
            nombre="Test",
            palabras_clave=["a", "b", "c", "d"],
        )

        # Act ------------------------------------------------------------
        cat.remover_palabras_clave(["a", "c"])

        # Assert ----------------------------------------------------------
        assert cat.palabras_clave == ["b", "d"]

    def test_Should_DoNothing_When_WordNotPresent(self):
        """No lanza error si la palabra no existe."""
        # Arrange --------------------------------------------------------
        cat = Categoria(
            nombre="Test",
            palabras_clave=["restaurante"],
        )

        # Act ------------------------------------------------------------
        cat.remover_palabras_clave(["no_existe"])

        # Assert ----------------------------------------------------------
        assert cat.palabras_clave == ["restaurante"]

    def test_Should_HandleEmptyList_When_NoWordsToRemove(self):
        """Maneja lista vacia sin cambios."""
        # Arrange --------------------------------------------------------
        cat = Categoria(
            nombre="Test",
            palabras_clave=["restaurante"],
        )

        # Act ------------------------------------------------------------
        cat.remover_palabras_clave([])

        # Assert ----------------------------------------------------------
        assert len(cat.palabras_clave) == 1

    def test_Should_ClearAllWords_When_RemoveAll(self):
        """Elimina todas las palabras si se pasan todas."""
        # Arrange --------------------------------------------------------
        cat = Categoria(
            nombre="Test",
            palabras_clave=["restaurante", "comida"],
        )

        # Act ------------------------------------------------------------
        cat.remover_palabras_clave(["restaurante", "comida"])

        # Assert ----------------------------------------------------------
        assert cat.palabras_clave == []
