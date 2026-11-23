"""rename tags to items

Revision ID: dc5d063e0d0e
Revises: db6109b49418
Create Date: 2026-11-23 18:53:13.082395

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'dc5d063e0d0e'
down_revision: Union[str, Sequence[str], None] = 'db6109b49418'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("posts", "tags", new_column_name="items")


def downgrade() -> None:
    op.alter_column("posts", "items", new_column_name="tags")
