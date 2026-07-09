"""Script para sembrar datos iniciales en la BD.

Ejecutar: python scripts/seed_data.py

Crea:
- Categorias predefinidas (14 categorias del sistema)
- Usuario demo (si no existe)
- Tarjeta demo
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.domain.entities.categoria import Categoria

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def seed_categories() -> int:
    """Siembra las 14 categorias predefinidas."""
    from src.infrastructure.persistence.unit_of_work import create_session_factory
    from src.infrastructure.persistence.repositories.categoria_repo import CategoriaRepository

    db_url = os.getenv(
        "DATABASE_URL_SYNC", "postgresql://postgres:postgres@localhost:5432/finance_report"
    )
    db_url_async = db_url.replace("postgresql://", "postgresql+asyncpg://")

    session_factory = await create_session_factory(db_url_async)

    async with session_factory() as session:
        repo = CategoriaRepository(session)
        existing = await repo.get_predefinidas()

        if existing:
            logger.info(f"{len(existing)} categorias ya existen. Saltando seed.")
            return len(existing)

        categorias = Categoria.precargadas()
        for cat in categorias:
            await repo.save(cat)

        await session.commit()
        logger.info(f"{len(categorias)} categorias predefinidas creadas.")
        return len(categorias)


async def main() -> None:
    logger.info("Iniciando seed de datos...")
    count = await seed_categories()
    logger.info(f"Seed completado: {count} categorias.")


if __name__ == "__main__":
    asyncio.run(main())
