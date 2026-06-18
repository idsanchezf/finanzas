"""Tests para el constructor y propiedades de Categoria.

Verifica creacion, valores por defecto, propiedades es_subcategoria
y es_personalizada.

Convencion TDD:
- Carpeta: CategoriaTests/
- Archivo: test_init.py
- Clase: TestInit
"""

from uuid import uuid4

from src.domain.entities.categoria import Categoria


class TestInit:
    """Tests para __init__ y propiedades basicas de Categoria."""

    def test_Should_CreateCategoria_When_ValidNameProvided(self):
        """Camino feliz: crea categoria con nombre."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        cat = Categoria(nombre="Alimentacion")

        # Assert ----------------------------------------------------------
        assert cat.nombre == "Alimentacion"
        assert cat.id is not None
        assert cat.icono == "📁"
        assert cat.color == "#6B7280"
        assert cat.es_predefinida is False
        assert cat.usuario_id is None
        assert cat.palabras_clave == []

    def test_Should_HaveDefaultValues_When_MinimalCreation(self):
        """Valores por defecto son asignados correctamente."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        cat = Categoria()

        # Assert ----------------------------------------------------------
        assert cat.nombre == ""
        assert cat.icono == "📁"
        assert cat.color == "#6B7280"
        assert cat.palabras_clave == []

    def test_Should_SetEsPredefinida_When_True(self):
        """Categoria predefinida con es_predefinida=True."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        cat = Categoria(nombre="Transporte", es_predefinida=True)

        # Assert ----------------------------------------------------------
        assert cat.es_predefinida is True

    def test_Should_AssignUsuarioId_When_Provided(self):
        """Categoria personalizada con usuario_id."""
        # Arrange --------------------------------------------------------
        uid = uuid4()

        # Act ------------------------------------------------------------
        cat = Categoria(nombre="Mi Categoria", usuario_id=uid)

        # Assert ----------------------------------------------------------
        assert cat.usuario_id == uid

    def test_Should_SetParentId_When_Subcategoria(self):
        """Subcategoria con parent_id."""
        # Arrange --------------------------------------------------------
        parent_id = uuid4()

        # Act ------------------------------------------------------------
        sub = Categoria(nombre="Comida Rapida", parent_id=parent_id)

        # Assert ----------------------------------------------------------
        assert sub.parent_id == parent_id

    def test_Should_SetIconoAndColor_When_Provided(self):
        """Icono y color personalizados."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        cat = Categoria(nombre="Salud", icono="🏥", color="#FF0000")

        # Assert ----------------------------------------------------------
        assert cat.icono == "🏥"
        assert cat.color == "#FF0000"


class TestEsSubcategoria:
    """Tests para la propiedad es_subcategoria."""

    def test_Should_ReturnTrue_When_HasParentId(self):
        """Subcategoria cuando tiene parent_id."""
        # Arrange --------------------------------------------------------
        sub = Categoria(nombre="Comida Rapida", parent_id=uuid4())

        # Act ------------------------------------------------------------
        result = sub.es_subcategoria

        # Assert ----------------------------------------------------------
        assert result is True

    def test_Should_ReturnFalse_When_NoParentId(self):
        """No es subcategoria sin parent_id."""
        # Arrange --------------------------------------------------------
        cat = Categoria(nombre="Alimentacion")

        # Act ------------------------------------------------------------
        result = cat.es_subcategoria

        # Assert ----------------------------------------------------------
        assert result is False

    def test_Should_ReturnFalse_When_ParentIdIsNone(self):
        """No es subcategoria con parent_id=None explicitamente."""
        # Arrange --------------------------------------------------------
        cat = Categoria(nombre="Alimentacion", parent_id=None)

        # Act ------------------------------------------------------------
        result = cat.es_subcategoria

        # Assert ----------------------------------------------------------
        assert result is False


class TestEsPersonalizada:
    """Tests para la propiedad es_personalizada."""

    def test_Should_ReturnTrue_When_NotPredefinidaAndHasUsuario(self):
        """Personalizada cuando no es predefinida y tiene usuario."""
        # Arrange --------------------------------------------------------
        cat = Categoria(
            nombre="Mi Cat",
            es_predefinida=False,
            usuario_id=uuid4(),
        )

        # Act ------------------------------------------------------------
        result = cat.es_personalizada

        # Assert ----------------------------------------------------------
        assert result is True

    def test_Should_ReturnFalse_When_Predefinida(self):
        """No es personalizada si es predefinida."""
        # Arrange --------------------------------------------------------
        cat = Categoria(nombre="Alimentacion", es_predefinida=True)

        # Act ------------------------------------------------------------
        result = cat.es_personalizada

        # Assert ----------------------------------------------------------
        assert result is False

    def test_Should_ReturnFalse_When_NoUsuarioId(self):
        """No es personalizada sin usuario_id."""
        # Arrange --------------------------------------------------------
        cat = Categoria(nombre="Test", es_predefinida=False, usuario_id=None)

        # Act ------------------------------------------------------------
        result = cat.es_personalizada

        # Assert ----------------------------------------------------------
        assert result is False

    def test_Should_ReturnFalse_When_PredefinidaEvenWithUsuario(self):
        """Predefinida con usuario_id NO es personalizada."""
        # Arrange --------------------------------------------------------
        cat = Categoria(
            nombre="Alimentacion",
            es_predefinida=True,
            usuario_id=uuid4(),
        )

        # Act ------------------------------------------------------------
        result = cat.es_personalizada

        # Assert ----------------------------------------------------------
        assert result is False
