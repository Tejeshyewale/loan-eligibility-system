"""add loan applications history table

Revision ID: 9d2f4b7a1c3e
Revises: 5cfc350c6b36
Create Date: 2026-10-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9d2f4b7a1c3e'
down_revision: Union[str, Sequence[str], None] = '5cfc350c6b36'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'applications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('input_data', sa.Text(), nullable=False),
        sa.Column('prediction', sa.String(), nullable=False),
        sa.Column('probability', sa.Float(), nullable=True),
        sa.Column('model_version', sa.String(), nullable=False),
        sa.Column('is_estimate', sa.Boolean(), nullable=False),
        sa.Column('top_reasons', sa.Text(), nullable=False),
        sa.Column('suggestions', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_applications_user_id', 'applications', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_applications_user_id', table_name='applications')
    op.drop_table('applications')
