"""add device_id to messages

Revision ID: 8ae2dac54043
Revises: 3179dbab7daa
Create Date: 2025-09-03 14:20:38.372219

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8ae2dac54043'
down_revision: Union[str, Sequence[str], None] = '3179dbab7daa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
