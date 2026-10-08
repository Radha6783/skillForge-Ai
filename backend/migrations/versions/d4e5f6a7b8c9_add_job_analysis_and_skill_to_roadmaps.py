"""Add job_analysis_id and description to roadmaps, and skill_name to roadmap_items

Revision ID: d4e5f6a7b8c9
Revises: c3f8a1b2d4e5
Create Date: 2026-10-07 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3f8a1b2d4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use batch_alter_table for SQLite compatibility
    with op.batch_alter_table('roadmaps', schema=None) as batch_op:
        batch_op.add_column(sa.Column('job_analysis_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('description', sa.Text(), nullable=True))
        batch_op.create_foreign_key(
            'fk_roadmaps_job_analysis_id',
            'job_analyses',
            ['job_analysis_id'],
            ['id'],
            ondelete='SET NULL'
        )

    with op.batch_alter_table('roadmap_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('skill_name', sa.String(length=100), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('roadmap_items', schema=None) as batch_op:
        batch_op.drop_column('skill_name')

    with op.batch_alter_table('roadmaps', schema=None) as batch_op:
        batch_op.drop_constraint('fk_roadmaps_job_analysis_id', type_='foreignkey')
        batch_op.drop_column('description')
        batch_op.drop_column('job_analysis_id')
