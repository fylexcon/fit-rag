"""add steps and resting heart rate to activities

Revision ID: b7e2d41c9f10
Revises: a3c8a837c782
Create Date: 2026-10-09 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7e2d41c9f10'
down_revision: Union[str, Sequence[str], None] = 'a3c8a837c782'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('activities', sa.Column('steps', sa.Integer(), nullable=True))
    op.add_column('activities', sa.Column('resting_heart_rate', sa.Integer(), nullable=True))
    op.create_index(
        'ix_activities_user_id_start_time', 'activities', ['user_id', 'start_time']
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_activities_user_id_start_time', table_name='activities')
    op.drop_column('activities', 'resting_heart_rate')
    op.drop_column('activities', 'steps')
