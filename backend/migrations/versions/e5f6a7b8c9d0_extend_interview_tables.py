"""Extend interview tables with job_analysis_id, interview_type, total_questions, question_type, skill_name, and score attributes

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-10-07 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use batch_alter_table for SQLite compatibility
    with op.batch_alter_table('interview_sessions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('job_analysis_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('interview_type', sa.String(length=50), server_default='MIXED', nullable=False))
        batch_op.add_column(sa.Column('total_questions', sa.Integer(), server_default='5', nullable=False))
        batch_op.create_foreign_key(
            'fk_interview_sessions_job_analysis_id',
            'job_analyses',
            ['job_analysis_id'],
            ['id'],
            ondelete='SET NULL'
        )

    with op.batch_alter_table('interview_questions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('question_type', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('skill_name', sa.String(length=100), nullable=True))

    with op.batch_alter_table('interview_answers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('relevance_score', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('technical_depth_score', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('improvement_suggestion', sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('interview_answers', schema=None) as batch_op:
        batch_op.drop_column('improvement_suggestion')
        batch_op.drop_column('technical_depth_score')
        batch_op.drop_column('relevance_score')

    with op.batch_alter_table('interview_questions', schema=None) as batch_op:
        batch_op.drop_column('skill_name')
        batch_op.drop_column('question_type')

    with op.batch_alter_table('interview_sessions', schema=None) as batch_op:
        batch_op.drop_constraint('fk_interview_sessions_job_analysis_id', type_='foreignkey')
        batch_op.drop_column('total_questions')
        batch_op.drop_column('interview_type')
        batch_op.drop_column('job_analysis_id')
