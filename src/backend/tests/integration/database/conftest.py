"""Fixtures especificas para tests de repositorios."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.persistence.models import CategoriaModel, TransaccionModel


@pytest_asyncio.fixture
async def categoria_repo(db_session: AsyncSession):
    """Repositorio de categorias con sesion de prueba."""
    from src.infrastructure.persistence.repositories.categoria_repo import (
        CategoriaRepository,
    )
    return CategoriaRepository(db_session)


@pytest_asyncio.fixture
async def transaccion_repo(db_session: AsyncSession):
    """Repositorio de transacciones con sesion de prueba."""
    from src.infrastructure.persistence.repositories.transaccion_repo import (
        TransaccionRepository,
    )
    return TransaccionRepository(db_session)


@pytest_asyncio.fixture
async def categoria_predefinida(db_session: AsyncSession) -> CategoriaModel:
    """Crea una categoria predefinida de prueba."""
    model = CategoriaModel(
        id=uuid.uuid4(),
        nombre="Alimentacion",
        icono="🍔",
        color="#FF6B6B",
        es_predefinida=True,
        palabras_clave=["restaurante", "comida"],
    )
    db_session.add(model)
    await db_session.flush()
    return model


@pytest_asyncio.fixture
async def categoria_personalizada(db_session: AsyncSession) -> CategoriaModel:
    """Crea una categoria personalizada de prueba."""
    user_id = uuid.uuid4()
    model = CategoriaModel(
        id=uuid.uuid4(),
        nombre="Mascotas Premium",
        icono="🐾",
        color="#D35400",
        es_predefinida=False,
        usuario_id=user_id,
        palabras_clave=["veterinaria", "concentrado"],
    )
    db_session.add(model)
    await db_session.flush()
    return model


@pytest_asyncio.fixture
async def transaccion_prueba(db_session: AsyncSession) -> TransaccionModel:
    """Crea una transaccion de prueba."""
    extracto_id = uuid.uuid4()
    usuario_id = uuid.uuid4()
    categoria_id = uuid.uuid4()

    model = TransaccionModel(
        id=uuid.uuid4(),
        extracto_id=extracto_id,
        usuario_id=usuario_id,
        numero_autorizacion="AUTH123",
        fecha=date(2026, 6, 1),
        comercio_original="RESTAURANTE DON PEPE",
        comercio_traducido="Don Pepe",
        valor=Decimal("45.50"),
        categoria_id=categoria_id,
        confidence=Decimal("95.00"),
        es_abono=False,
        es_cuota=False,
    )
    db_session.add(model)
    await db_session.flush()
    return model
