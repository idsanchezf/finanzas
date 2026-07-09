"""Tests para el metodo de fabrica precargadas().

Verifica que genera exactamente 14 categorias predefinidas con
los nombres, iconos, colores y palabras clave correctos.

Convencion TDD:
- Carpeta: CategoriaTests/
- Archivo: test_precargadas.py
"""

from src.domain.entities.categoria import Categoria


class TestPrecargadas:
    """Tests para precargadas() classmethod."""

    NOMBRES_ESPERADOS = {
        "Alimentacion",
        "Transporte",
        "Vivienda",
        "Salud",
        "Entretenimiento",
        "Educacion",
        "Ropa y Moda",
        "Financieros",
        "Tecnologia",
        "Viajes",
        "Servicios",
        "Suscripciones",
        "Mascotas",
        "Otros",
    }

    def test_Should_Return14Categories_When_Called(self):
        """Retorna exactamente 14 categorias predefinidas."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        categorias = Categoria.precargadas()

        # Assert ----------------------------------------------------------
        assert len(categorias) == 14

    def test_Should_AllBePredefinidas_When_Precargadas(self):
        """Todas las categorias precargadas tienen es_predefinida=True."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        categorias = Categoria.precargadas()

        # Assert ----------------------------------------------------------
        for cat in categorias:
            assert cat.es_predefinida is True, f"{cat.nombre} debe ser predefinida"

    def test_Should_AllHaveUsuarioIdNone_When_Precargadas(self):
        """Las categorias predefinidas no pertenecen a un usuario."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        categorias = Categoria.precargadas()

        # Assert ----------------------------------------------------------
        for cat in categorias:
            assert cat.usuario_id is None, f"{cat.nombre} no debe tener usuario_id"

    def test_Should_ContainAllExpectedNames_When_Precargadas(self):
        """Contiene los 14 nombres esperados."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        categorias = Categoria.precargadas()
        nombres = {c.nombre for c in categorias}

        # Assert ----------------------------------------------------------
        assert nombres == self.NOMBRES_ESPERADOS

    def test_Should_AllHaveUniqueIds_When_Precargadas(self):
        """Cada categoria tiene un ID unico."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        categorias = Categoria.precargadas()
        ids = [c.id for c in categorias]

        # Assert ----------------------------------------------------------
        assert len(ids) == len(set(ids))

    def test_Should_AllHaveIcon_When_Precargadas(self):
        """Cada categoria tiene un icono definido."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        categorias = Categoria.precargadas()

        # Assert ----------------------------------------------------------
        for cat in categorias:
            assert cat.icono and cat.icono != "📁", f"{cat.nombre} debe tener icono personalizado"

    def test_Should_AllHaveColor_When_Precargadas(self):
        """Cada categoria tiene un color definido (hex)."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        categorias = Categoria.precargadas()

        # Assert ----------------------------------------------------------
        for cat in categorias:
            assert cat.color.startswith("#"), f"{cat.nombre} debe tener color hex"
            assert cat.color != "#6B7280", f"{cat.nombre} debe tener color personalizado"

    def test_Should_AllHaveKeywords_When_Precargadas(self):
        """Cada categoria tiene al menos 2 palabras clave."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        categorias = Categoria.precargadas()

        # Assert ----------------------------------------------------------
        for cat in categorias:
            assert len(cat.palabras_clave) >= 2, (
                f"{cat.nombre} debe tener al menos 2 palabras clave, "
                f"tiene {len(cat.palabras_clave)}"
            )

    def test_Should_HaveAlimentacionFirst_When_Precargadas(self):
        """La primera categoria en la lista es Alimentacion."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        categorias = Categoria.precargadas()

        # Assert ----------------------------------------------------------
        assert categorias[0].nombre == "Alimentacion"

    def test_Should_HaveOtrosLast_When_Precargadas(self):
        """La ultima categoria en la lista es Otros."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        categorias = Categoria.precargadas()

        # Assert ----------------------------------------------------------
        assert categorias[-1].nombre == "Otros"

    def test_Should_AlimentacionHaveExpectedKeywords_When_Precargadas(self):
        """Verifica palabras clave clave de Alimentacion."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        categorias = Categoria.precargadas()
        alim = next(c for c in categorias if c.nombre == "Alimentacion")

        # Assert ----------------------------------------------------------
        assert "restaurante" in alim.palabras_clave
        assert "supermercado" in alim.palabras_clave
        assert "rappi" in alim.palabras_clave
        assert "didi food" in alim.palabras_clave

    def test_Should_TransporteHaveExpectedKeywords_When_Precargadas(self):
        """Verifica palabras clave clave de Transporte."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        categorias = Categoria.precargadas()
        trans = next(c for c in categorias if c.nombre == "Transporte")

        # Assert ----------------------------------------------------------
        assert "uber" in trans.palabras_clave
        assert "taxi" in trans.palabras_clave
        assert "gasolina" in trans.palabras_clave
        assert "transmilenio" in trans.palabras_clave

    def test_Should_SuscripcionesHaveExpectedKeywords_When_Precargadas(self):
        """Verifica palabras clave de Suscripciones."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        categorias = Categoria.precargadas()
        sub = next(c for c in categorias if c.nombre == "Suscripciones")

        # Assert ----------------------------------------------------------
        assert "netflix" not in sub.palabras_clave  # Esta en Entretenimiento
        assert "suscripcion" in sub.palabras_clave
        assert "membresia" in sub.palabras_clave

    def test_Should_FinancierosHaveExpectedKeywords_When_Precargadas(self):
        """Verifica palabras clave de Financieros."""
        # Arrange --------------------------------------------------------

        # Act ------------------------------------------------------------
        categorias = Categoria.precargadas()
        fin = next(c for c in categorias if c.nombre == "Financieros")

        # Assert ----------------------------------------------------------
        assert "comision" in fin.palabras_clave
        assert "interes" in fin.palabras_clave
        assert "cuota manejo" in fin.palabras_clave
        assert "4x1000" in fin.palabras_clave
