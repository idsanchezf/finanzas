"""add_file_hash_to_extractos

Revision ID: 1e857b45ce5e
Revises: fc45e3945456
Create Date: 2026-07-05 05:23:30.812971
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = '1e857b45ce5e'
down_revision: Union[str, None] = 'fc45e3945456'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Agregar columna file_hash para deteccion de duplicados por hash (feat-003 Fix #3)
    op.add_column('extractos', sa.Column('file_hash', sa.String(length=64), nullable=True))
    op.create_index('ix_extractos_file_hash', 'extractos', ['tarjeta_id', 'file_hash'], unique=False)
    op.create_unique_constraint('uq_extracto_tarjeta_file_hash', 'extractos', ['tarjeta_id', 'file_hash'])


def downgrade() -> None:
    op.drop_constraint('uq_extracto_tarjeta_file_hash', 'extractos', type_='unique')
    op.drop_index('ix_extractos_file_hash', table_name='extractos')
    op.drop_column('extractos', 'file_hash')
