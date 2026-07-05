"""
Script para eliminar todos los extractos cargados y sus transacciones asociadas.

Uso:
    docker compose exec backend python scripts/limpiar_extractos.py

Las transacciones se eliminan automaticamente en cascada por la FK
con ondelete="CASCADE" en transacciones.extracto_id.
"""

import asyncio
import sys
import os

# Agregar src al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from src.infrastructure.persistence.models import ExtractoModel, TransaccionModel


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@postgres:5432/finance_report",
)


async def limpiar_extractos(confirmar: bool = False) -> None:
    """Elimina todos los extractos y sus transacciones en cascada."""
    engine = create_async_engine(DATABASE_URL, echo=False)

    async with AsyncSession(engine) as session:
        # Contar antes de eliminar
        count_extractos = await session.scalar(
            select(func.count()).select_from(ExtractoModel)
        )
        count_transacciones = await session.scalar(
            select(func.count()).select_from(TransaccionModel)
        )

        if count_extractos == 0:
            print("✅ No hay extractos para eliminar.")
            await engine.dispose()
            return

        print(f"📊 Extractos encontrados:  {count_extractos}")
        print(f"📊 Transacciones actuales: {count_transacciones}")

        if not confirmar:
            print("\n⚠️  Ejecuta con --confirmar para eliminar:")
            print("   docker compose exec backend python scripts/limpiar_extractos.py --confirmar")
            await engine.dispose()
            return

        print("\n🗑️  Eliminando extractos...")

        # Eliminar en orden: primero transacciones (por si acaso), luego extractos
        result_trans = await session.execute(delete(TransaccionModel))
        result_extr = await session.execute(delete(ExtractoModel))
        await session.commit()

        print(f"   ✅ {result_trans.rowcount} transacciones eliminadas")
        print(f"   ✅ {result_extr.rowcount} extractos eliminados")
        print("🏁 Limpieza completada.")

    await engine.dispose()


if __name__ == "__main__":
    confirmar = "--confirmar" in sys.argv or "-y" in sys.argv
    asyncio.run(limpiar_extractos(confirmar=confirmar))
