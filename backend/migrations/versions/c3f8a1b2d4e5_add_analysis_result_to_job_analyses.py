"""Add analysis_result column to job_analyses

Revision ID: c3f8a1b2d4e5
Revises: befb4ae4bc1f
Create Date: 2026-10-07 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3f8a1b2d4e5'
down_revision: Union[str, Sequence[str], None] = 'befb4ae4bc1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add analysis_result JSON column to job_analyses table."""
    with op.batch_alter_table('job_analyses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('analysis_result', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Remove analysis_result column from job_analyses table."""
    with op.batch_alter_table('job_analyses', schema=None) as batch_op:
        batch_op.drop_column('analysis_result')
