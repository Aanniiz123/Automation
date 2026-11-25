"""Change to uuid

Revision ID: 40515bfa4c1f
Revises: 31336f3b01bc
Create Date: 2026-11-18 11:20:43.823480

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = '40515bfa4c1f'
down_revision: Union[str, Sequence[str], None] = '31336f3b01bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Keep the existing integer identity columns unchanged."""
    pass


def downgrade() -> None:
    """No schema changes were made by this migration."""
    pass
