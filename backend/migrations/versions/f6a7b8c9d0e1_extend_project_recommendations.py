"""extend_project_recommendations

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-10-07 20:05:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('project_recommendations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('job_analysis_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('why_recommended', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('estimated_hours', sa.Integer(), nullable=True, server_default='10'))
        batch_op.add_column(sa.Column('resume_bullet', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True))
        batch_op.create_foreign_key(
            'fk_project_recommendations_job_analysis_id',
            'job_analyses',
            ['job_analysis_id'],
            ['id'],
            ondelete='SET NULL'
        )


def downgrade() -> None:
    with op.batch_alter_table('project_recommendations', schema=None) as batch_op:
        batch_op.drop_constraint('fk_project_recommendations_job_analysis_id', type_='foreignkey')
        batch_op.drop_column('updated_at')
        batch_op.drop_column('resume_bullet')
        batch_op.drop_column('estimated_hours')
        batch_op.drop_column('why_recommended')
        batch_op.drop_column('job_analysis_id')
