"""Fuk you

Revision ID: 3012993ac6b4
Revises: b43b8f600435
Create Date: 2026-11-24 15:12:21.952106

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3012993ac6b4'
down_revision: Union[str, Sequence[str], None] = 'b43b8f600435'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
