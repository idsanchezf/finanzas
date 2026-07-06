# ============================================================
# Finance Report — Alembic env.py
# ============================================================
# Configura el contexto de migraciones con soporte para:
# - SQLAlchemy 2.0 async (el modelo usa async, pero Alembic usa sync)
# - Carga de modelos ORM desde src.infrastructure.persistence.models
# - URL desde variable de entorno DATABASE_URL_SYNC
# ============================================================

import os
import sys
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

# Cargar variables de entorno
load_dotenv()

# Asegurar que src/ esta en el path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Alembic Config object
config = context.config

# Interpretar la configuracion de logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Importar modelos para que Alembic pueda detectarlos en autogenerate
from src.infrastructure.persistence.models import Base  # noqa: E402, F401

# Metadata de todos los modelos registrados
target_metadata = Base.metadata

# Otras configuraciones desde el ini
# my_important_option = config.get_main_option("my_important_option")


def get_url() -> str:
    """Obtiene la URL de la base de datos sincrona desde variables de entorno."""
    url = os.getenv("DATABASE_URL_SYNC")
    if url is None:
        # Fallback: convertir async URL a sync URL si es necesario
        async_url = os.getenv("DATABASE_URL", "")
        url = async_url.replace("+asyncpg", "").replace("postgresql+asyncpg", "postgresql")
    if not url:
        raise ValueError(
            "DATABASE_URL_SYNC no esta configurada. "
            "Define DATABASE_URL_SYNC o DATABASE_URL en el entorno."
        )
    return url


def run_migrations_offline() -> None:
    """Ejecuta migraciones en modo 'offline'.

    Configura el contexto solo con la URL (sin Engine).
    Las llamadas a context.execute() emiten SQL al output del script.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # Detectar cambios en tipos de columna
        compare_server_default=True,  # Detectar cambios en defaults
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Ejecuta migraciones en modo 'online'.

    Crea un Engine y asocia la conexion con el contexto.
    """
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
