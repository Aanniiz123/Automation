"""custom migration

Revision ID: b43b8f600435
Revises: 40515bfa4c1f
Create Date: 2026-11-24 15:10:07.417205

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b43b8f600435'
down_revision: Union[str, Sequence[str], None] = '40515bfa4c1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
