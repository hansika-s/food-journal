"""rating with one decimal

Revision ID: 67b24190a949
Revises: dc5d063e0d0e
Create Date: 2026-11-23 18:54:52.834827

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67b24190a949'
down_revision: Union[str, Sequence[str], None] = 'dc5d063e0d0e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "posts",
        "rating",
        type_=sa.Numeric(2, 1),
        postgresql_using="rating::numeric(2,1)",
    )


# Going back rounds ratings such as 4.5 to whole numbers.
def downgrade() -> None:
    op.alter_column(
        "posts",
        "rating",
        type_=sa.Integer(),
        postgresql_using="round(rating)::integer",
    )
