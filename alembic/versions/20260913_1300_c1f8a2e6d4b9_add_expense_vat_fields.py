"""add expense vat fields

Revision ID: c1f8a2e6d4b9
Revises: a9e3f7c1d5b2
Create Date: 2026-09-13 13:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c1f8a2e6d4b9"
down_revision: Union[str, Sequence[str], None] = "a9e3f7c1d5b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "expense",
        sa.Column("vat_rate", sa.Numeric(precision=4, scale=2), nullable=False, server_default="0"),
    )
    op.add_column(
        "expense",
        sa.Column(
            "vat_amount", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0"
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("expense", "vat_amount")
    op.drop_column("expense", "vat_rate")
