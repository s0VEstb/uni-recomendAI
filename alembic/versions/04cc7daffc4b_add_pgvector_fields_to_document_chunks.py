"""add pgvector fields to document_chunks

Revision ID: 04cc7daffc4b
Revises: 64ed094f2a24
Create Date: 2026-02-21 13:13:31.898314

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '04cc7daffc4b'
down_revision: Union[str, Sequence[str], None] = '64ed094f2a24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
