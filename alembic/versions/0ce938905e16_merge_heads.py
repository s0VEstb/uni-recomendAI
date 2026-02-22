"""merge heads

Revision ID: 0ce938905e16
Revises: 128af0e500a5, 8958fc34f6f5
Create Date: 2026-02-22 11:38:54.764797

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0ce938905e16'
down_revision: Union[str, Sequence[str], None] = ('128af0e500a5', '8958fc34f6f5')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
