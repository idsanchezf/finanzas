"""Tests para el metodo clasificar() de Transaccion.

Verifica asignacion de categoria, confianza, y generacion
de evento de dominio TransaccionClasificada.

Convencion TDD:
- Carpeta: TransaccionTests/
- Archivo: test_clasificar.py
"""

from decimal import Decimal
from uuid import uuid4

from src.domain.entities.transaccion import Transaccion
from src.domain.events import TransaccionClasificada


class TestClasificar:
    """Tests para clasificar(categoria_id, confidence)."""

    def test_Should_AssignCategory_When_ValidCategoryAndConfidence(self):
        """Asigna categoria_id y confidence a la transaccion."""
        # Arrange --------------------------------------------------------
        tx = Transaccion(valor=Decimal("50000.00"))
        cat_id = uuid4()

        # Act ------------------------------------------------------------
        events = tx.clasificar(cat_id, Decimal("95.50"))

        # Assert ----------------------------------------------------------
        assert tx.categoria_id == cat_id
        assert tx.confidence == Decimal("95.50")

    def test_Should_ReturnClasificadaEvent_When_Classified(self):
        """Retorna lista con evento TransaccionClasificada."""
        # Arrange --------------------------------------------------------
        tx = Transaccion(
            extracto_id=uuid4(),
            comercio_original="UBER TRIP",
        )
        cat_id = uuid4()

        # Act ------------------------------------------------------------
        events = tx.clasificar(cat_id, Decimal("85.00"))

        # Assert ----------------------------------------------------------
        assert len(events) == 1
        event = events[0]
        assert isinstance(event, TransaccionClasificada)
        assert event.transaction_id == tx.id
        assert event.extracto_id == tx.extracto_id
        assert event.categoria_id == cat_id
        assert event.confidence == Decimal("85.00")

    def test_Should_IncludePreviousCategory_When_Reclassifying(self):
        """Incluye categoria_anterior cuando se re-clasifica."""
        # Arrange --------------------------------------------------------
        cat_old = uuid4()
        cat_new = uuid4()
        tx = Transaccion(
            extracto_id=uuid4(),
            categoria_id=cat_old,
            confidence=Decimal("70.00"),
        )

        # Act ------------------------------------------------------------
        events = tx.clasificar(cat_new, Decimal("90.00"))

        # Assert ----------------------------------------------------------
        assert tx.categoria_id == cat_new
        event = events[0]
        assert event.categoria_anterior == cat_old

    def test_Should_SetCategoriaAnteriorNone_When_FirstClassification(self):
        """categoria_anterior=None cuando es la primera clasificacion."""
        # Arrange --------------------------------------------------------
        tx = Transaccion(extracto_id=uuid4())
        cat_id = uuid4()

        # Act ------------------------------------------------------------
        events = tx.clasificar(cat_id, Decimal("100.00"))

        # Assert ----------------------------------------------------------
        assert events[0].categoria_anterior is None

    def test_Should_AcceptMaxConfidence_When_100(self):
        """Acepta confidence=100 (maxima certeza)."""
        # Arrange --------------------------------------------------------
        tx = Transaccion()
        cat_id = uuid4()

        # Act ------------------------------------------------------------
        events = tx.clasificar(cat_id, Decimal("100.00"))

        # Assert ----------------------------------------------------------
        assert tx.confidence == Decimal("100.00")
        assert len(events) == 1

    def test_Should_AcceptMinConfidence_When_Zero(self):
        """Acepta confidence=0 (sin certeza)."""
        # Arrange --------------------------------------------------------
        tx = Transaccion()
        cat_id = uuid4()

        # Act ------------------------------------------------------------
        events = tx.clasificar(cat_id, Decimal("0.00"))

        # Assert ----------------------------------------------------------
        assert tx.confidence == Decimal("0.00")
        assert tx.categoria_id == cat_id
