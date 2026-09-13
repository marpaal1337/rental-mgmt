"""add indexes and invoice uniqueness

Revision ID: b7d1c9e2a4f0
Revises: 8c8362e4c3d6
Create Date: 2026-09-12 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7d1c9e2a4f0"
down_revision: Union[str, Sequence[str], None] = "8c8362e4c3d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEXES: list[tuple[str, str, list[str]]] = [
    ("ix_property_owner_id", "property", ["owner_id"]),
    ("ix_unit_property_id", "unit", ["property_id"]),
    ("ix_lease_unit_id", "lease", ["unit_id"]),
    ("ix_lease_tenant_id", "lease", ["tenant_id"]),
    ("ix_lease_owner_id", "lease", ["owner_id"]),
    ("ix_rent_condition_lease_id", "rent_condition", ["lease_id"]),
    ("ix_rent_condition_start_date", "rent_condition", ["start_date"]),
    ("ix_index_update_lease_id", "index_update", ["lease_id"]),
    ("ix_index_update_application_date", "index_update", ["application_date"]),
    ("ix_invoice_period", "invoice", ["period"]),
    ("ix_invoice_lease_id", "invoice", ["lease_id"]),
    ("ix_invoice_status", "invoice", ["status"]),
    ("ix_invoice_line_invoice_id", "invoice_line", ["invoice_id"]),
    ("ix_payment_invoice_id", "payment", ["invoice_id"]),
    ("ix_payment_payment_date", "payment", ["payment_date"]),
    ("ix_expense_property_id", "expense", ["property_id"]),
    ("ix_expense_lease_id", "expense", ["lease_id"]),
    ("ix_expense_expense_date", "expense", ["expense_date"]),
    ("ix_bank_movement_entry_date", "bank_movement", ["entry_date"]),
    ("ix_bank_movement_status", "bank_movement", ["status"]),
    ("ix_reconciliation_bank_movement_id", "reconciliation", ["bank_movement_id"]),
    ("ix_reconciliation_payment_id", "reconciliation", ["payment_id"]),
]


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table(
        "reconciliation",
        naming_convention={"uq": "uq_%(table_name)s_%(column_0_name)s"},
    ) as batch_op:
        batch_op.drop_constraint("uq_reconciliation_bank_movement_id", type_="unique")

    for name, table, columns in INDEXES:
        op.create_index(name, table, columns)

    op.create_index(
        "uq_invoice_lease_period_active",
        "invoice",
        ["lease_id", "period"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("uq_invoice_lease_period_active", table_name="invoice")
    for name, table, _columns in reversed(INDEXES):
        op.drop_index(name, table_name=table)

    with op.batch_alter_table(
        "reconciliation",
        naming_convention={"uq": "uq_%(table_name)s_%(column_0_name)s"},
    ) as batch_op:
        batch_op.create_unique_constraint(
            "uq_reconciliation_bank_movement_id", ["bank_movement_id"]
        )
