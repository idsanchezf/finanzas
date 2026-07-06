"""Tests para el metodo corregir_categoria() de Transaccion.

Verifica correccion manual de categoria por el usuario,
confidence=100, y generacion de evento CategoriaCorregida.

Convencion TDD:
- Carpeta: TransaccionTests/
- Archivo: test_corregir_categoria.py
"""

from decimal import Decimal
from uuid import uuid4

from src.domain.entities.transaccion import Transaccion
from src.domain.events import CategoriaCorregida


class TestCorregirCategoria:
    """Tests para corregir_categoria(categoria_id)."""

    def test_Should_SetNewCategory_When_Corrected(self):
        """Cambia la categoria al nuevo ID."""
        # Arrange --------------------------------------------------------
        old_cat = uuid4()
        new_cat = uuid4()
        tx = Transaccion(
            categoria_id=old_cat,
            confidence=Decimal("70.00"),
            comercio_original="RESTAURANTE LA CASONA",
        )

        # Act ------------------------------------------------------------
        events = tx.corregir_categoria(new_cat)

        # Assert ----------------------------------------------------------
        assert tx.categoria_id == new_cat

    def test_Should_SetConfidence100_When_Corrected(self):
        """La correccion manual fija confidence en 100."""
        # Arrange --------------------------------------------------------
        tx = Transaccion(
            categoria_id=uuid4(),
            confidence=Decimal("55.00"),
        )

        # Act ------------------------------------------------------------
        tx.corregir_categoria(uuid4())

        # Assert ----------------------------------------------------------
        assert tx.confidence == Decimal("100.00")

    def test_Should_ReturnCategoriaCorregidaEvent_When_Corrected(self):
        """Retorna evento CategoriaCorregida con datos de aprendizaje."""
        # Arrange --------------------------------------------------------
        old_cat = uuid4()
        new_cat = uuid4()
        tx = Transaccion(
            categoria_id=old_cat,
            comercio_original="DLO*DIDI FOOD",
        )

        # Act ------------------------------------------------------------
        events = tx.corregir_categoria(new_cat)

        # Assert ----------------------------------------------------------
        assert len(events) == 1
        event = events[0]
        assert isinstance(event, CategoriaCorregida)
        assert event.transaction_id == tx.id
        assert event.categoria_anterior == old_cat
        assert event.categoria_nueva == new_cat
        assert event.comercio_original == "DLO*DIDI FOOD"

    def test_Should_IncludePreviousCategoryInEvent_When_Corrected(self):
        """El evento CategoriaCorregida incluye la categoria anterior."""
        # Arrange --------------------------------------------------------
        old_cat = uuid4()
        new_cat = uuid4()
        tx = Transaccion(categoria_id=old_cat)

        # Act ------------------------------------------------------------
        events = tx.corregir_categoria(new_cat)

        # Assert ----------------------------------------------------------
        event = events[0]
        assert event.categoria_anterior == old_cat
        assert event.categoria_nueva == new_cat

    def test_Should_SetConfidence100_When_PreviouslyUnclassified(self):
        """Aunque no tuviera categoria antes, confidence=100 tras correccion."""
        # Arrange --------------------------------------------------------
        tx = Transaccion(
            categoria_id=None,
            confidence=None,
        )

        # Act ------------------------------------------------------------
        tx.corregir_categoria(uuid4())

        # Assert ----------------------------------------------------------
        assert tx.confidence == Decimal("100.00")
