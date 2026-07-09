"""Tests para el metodo save del TransaccionRepository."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.models import TransaccionModel

pytestmark = pytest.mark.integration


class TestSave:
    """Escenarios del metodo save."""

    @pytest.mark.asyncio
    async def test_Should_PersistNewTransaccion_When_ValidModel(
        self,
        db_session: AsyncSession,
    ):
        """Crea y persiste una nueva transaccion."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.transaccion_repo import (
            TransaccionRepository,
        )

        repo = TransaccionRepository(db_session)
        model = TransaccionModel(
            id=uuid.uuid4(),
            extracto_id=uuid.uuid4(),
            usuario_id=uuid.uuid4(),
            fecha=date(2026, 6, 10),
            comercio_original="AMAZON PRIME",
            comercio_traducido="Amazon Prime Video",
            valor=Decimal("29.90"),
            numero_cuotas="1/1",
            cuotas_totales=1,
            cuota_actual=1,
            moneda_original="USD",
            valor_moneda_original=Decimal("7.49"),
            categoria_id=uuid.uuid4(),
            confidence=Decimal("85.00"),
            es_abono=False,
            es_cuota=False,
        )

        # Act ------------------------------------------------------------
        saved = await repo.save(model)

        # Assert ----------------------------------------------------------
        assert saved is not None
        assert saved.id == model.id
        assert saved.comercio_original == "AMAZON PRIME"

        # Verify persistence
        retrieved = await repo.get_by_id(model.id)
        assert retrieved is not None
        assert retrieved.valor == Decimal("29.90")

    @pytest.mark.asyncio
    async def test_Should_UpdateExistingTransaccion_When_Merged(
        self,
        db_session: AsyncSession,
        transaccion_prueba: TransaccionModel,
    ):
        """Actualiza una transaccion existente via merge."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.transaccion_repo import (
            TransaccionRepository,
        )

        repo = TransaccionRepository(db_session)
        transaccion_prueba.comercio_traducido = "Nombre Modificado"

        # Act ------------------------------------------------------------
        saved = await repo.save(transaccion_prueba)

        # Assert ----------------------------------------------------------
        assert saved.comercio_traducido == "Nombre Modificado"

        retrieved = await repo.get_by_id(transaccion_prueba.id)
        assert retrieved is not None
        assert retrieved.comercio_traducido == "Nombre Modificado"

    @pytest.mark.asyncio
    async def test_Should_PersistInstallmentData_When_CuotasProvided(
        self,
        db_session: AsyncSession,
    ):
        """Persiste correctamente datos de cuotas."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.transaccion_repo import (
            TransaccionRepository,
        )

        repo = TransaccionRepository(db_session)
        model = TransaccionModel(
            id=uuid.uuid4(),
            extracto_id=uuid.uuid4(),
            usuario_id=uuid.uuid4(),
            fecha=date(2026, 6, 5),
            comercio_original="COMPRA CUOTAS",
            valor=Decimal("1200.00"),
            numero_cuotas="3/36",
            cuotas_totales=36,
            cuota_actual=3,
            valor_cuota=Decimal("33.33"),
            interes_mensual_pct=Decimal("2.5"),
            interes_anual_pct=Decimal("30.0"),
            saldo_pendiente=Decimal("1100.00"),
            es_cuota=True,
        )

        # Act ------------------------------------------------------------
        saved = await repo.save(model)

        # Assert ----------------------------------------------------------
        retrieved = await repo.get_by_id(model.id)
        assert retrieved.cuotas_totales == 36
        assert retrieved.cuota_actual == 3
        assert retrieved.valor_cuota == Decimal("33.33")
        assert retrieved.saldo_pendiente == Decimal("1100.00")

    @pytest.mark.asyncio
    async def test_Should_PersistNegativeValueAsAbono_When_Negative(
        self,
        db_session: AsyncSession,
    ):
        """Persiste valores negativos como abonos."""
        # Arrange --------------------------------------------------------
        from src.infrastructure.persistence.repositories.transaccion_repo import (
            TransaccionRepository,
        )

        repo = TransaccionRepository(db_session)
        model = TransaccionModel(
            id=uuid.uuid4(),
            extracto_id=uuid.uuid4(),
            usuario_id=uuid.uuid4(),
            fecha=date(2026, 6, 8),
            comercio_original="PAGO TARJETA",
            valor=Decimal("-500.00"),
            es_abono=True,
        )

        # Act ------------------------------------------------------------
        saved = await repo.save(model)

        # Assert ----------------------------------------------------------
        retrieved = await repo.get_by_id(model.id)
        assert retrieved.valor == Decimal("-500.00")
        assert retrieved.es_abono is True
