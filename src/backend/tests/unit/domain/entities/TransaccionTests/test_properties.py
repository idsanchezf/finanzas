"""Tests para las propiedades de Transaccion.

Verifica es_confianza_baja, nombre_visible, es_sub_fila.

Convencion TDD:
- Carpeta: TransaccionTests/
- Archivo: test_properties.py
"""

from decimal import Decimal
from uuid import uuid4

from src.domain.entities.transaccion import Transaccion


class TestEsConfianzaBaja:
    """Tests para la propiedad es_confianza_baja."""

    def test_Should_ReturnTrue_When_ConfidenceBelow70(self):
        """Confianza < 70 es baja."""
        # Arrange --------------------------------------------------------
        tx = Transaccion(confidence=Decimal("69.99"))

        # Act ------------------------------------------------------------
        result = tx.es_confianza_baja

        # Assert ----------------------------------------------------------
        assert result is True

    def test_Should_ReturnTrue_When_ConfidenceIsZero(self):
        """Confianza 0 es baja."""
        # Arrange --------------------------------------------------------
        tx = Transaccion(confidence=Decimal("0.00"))

        # Act ------------------------------------------------------------
        result = tx.es_confianza_baja

        # Assert ----------------------------------------------------------
        assert result is True

    def test_Should_ReturnFalse_When_ConfidenceIs70(self):
        """Confianza = 70 NO es baja (>= 70)."""
        # Arrange --------------------------------------------------------
        tx = Transaccion(confidence=Decimal("70.00"))

        # Act ------------------------------------------------------------
        result = tx.es_confianza_baja

        # Assert ----------------------------------------------------------
        assert result is False

    def test_Should_ReturnFalse_When_ConfidenceIs100(self):
        """Confianza 100 no es baja."""
        # Arrange --------------------------------------------------------
        tx = Transaccion(confidence=Decimal("100.00"))

        # Act ------------------------------------------------------------
        result = tx.es_confianza_baja

        # Assert ----------------------------------------------------------
        assert result is False

    def test_Should_ReturnFalse_When_ConfidenceIsNone(self):
        """Sin confianza (None), no se considera baja."""
        # Arrange --------------------------------------------------------
        tx = Transaccion(confidence=None)

        # Act ------------------------------------------------------------
        result = tx.es_confianza_baja

        # Assert ----------------------------------------------------------
        assert result is False


class TestNombreVisible:
    """Tests para la propiedad nombre_visible."""

    def test_Should_ReturnTraducido_When_TranslationExists(self):
        """Prefiere comercio_traducido sobre comercio_original."""
        # Arrange --------------------------------------------------------
        tx = Transaccion(
            comercio_original="DLO*DIDI FOOD CO PAYIN",
            comercio_traducido="Didi Food",
        )

        # Act ------------------------------------------------------------
        result = tx.nombre_visible

        # Assert ----------------------------------------------------------
        assert result == "Didi Food"

    def test_Should_ReturnOriginal_When_NoTranslation(self):
        """Usa comercio_original si no hay traduccion."""
        # Arrange --------------------------------------------------------
        tx = Transaccion(
            comercio_original="UBER *TRIP HELP.UBER.COM",
            comercio_traducido=None,
        )

        # Act ------------------------------------------------------------
        result = tx.nombre_visible

        # Assert ----------------------------------------------------------
        assert result == "UBER *TRIP HELP.UBER.COM"

    def test_Should_ReturnEmpty_When_BothAreEmpty(self):
        """Retorna string vacio si ambos estan vacios."""
        # Arrange --------------------------------------------------------
        tx = Transaccion(
            comercio_original="",
            comercio_traducido=None,
        )

        # Act ------------------------------------------------------------
        result = tx.nombre_visible

        # Assert ----------------------------------------------------------
        assert result == ""


class TestEsSubFila:
    """Tests para la propiedad es_sub_fila."""

    def test_Should_ReturnTrue_When_HasParent(self):
        """Sub-fila VR MONEDA ORIG con parent_transaccion_id."""
        # Arrange --------------------------------------------------------
        tx = Transaccion(parent_transaccion_id=uuid4())

        # Act ------------------------------------------------------------
        result = tx.es_sub_fila

        # Assert ----------------------------------------------------------
        assert result is True

    def test_Should_ReturnFalse_When_NoParent(self):
        """Transaccion normal sin parent."""
        # Arrange --------------------------------------------------------
        tx = Transaccion()

        # Act ------------------------------------------------------------
        result = tx.es_sub_fila

        # Assert ----------------------------------------------------------
        assert result is False

    def test_Should_ReturnFalse_When_ParentIsNone(self):
        """parent_transaccion_id=None explicitamente."""
        # Arrange --------------------------------------------------------
        tx = Transaccion(parent_transaccion_id=None)

        # Act ------------------------------------------------------------
        result = tx.es_sub_fila

        # Assert ----------------------------------------------------------
        assert result is False
