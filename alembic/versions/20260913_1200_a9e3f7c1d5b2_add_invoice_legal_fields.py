"""add invoice legal fields (numbering, due date, snapshot, rectification)

Revision ID: a9e3f7c1d5b2
Revises: b7d1c9e2a4f0
Create Date: 2026-09-13 12:00:00.000000

"""

from collections import defaultdict
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a9e3f7c1d5b2"
down_revision: Union[str, Sequence[str], None] = "b7d1c9e2a4f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_SERIES = "A"
LEGACY_PAYMENT_TERMS_DAYS = 30

INVOICE_COLUMNS = [
    sa.Column("sequence", sa.Integer(), nullable=True),
    sa.Column("number", sa.String(length=40), nullable=True),
    sa.Column("fiscal_year", sa.Integer(), nullable=True),
    sa.Column("due_date", sa.Date(), nullable=True),
    sa.Column("rectification_reason", sa.String(length=500), nullable=True),
    sa.Column("issuer_name", sa.String(length=255), nullable=True),
    sa.Column("issuer_document_type", sa.String(length=10), nullable=True),
    sa.Column("issuer_document_number", sa.String(length=50), nullable=True),
    sa.Column("issuer_address", sa.String(length=500), nullable=True),
    sa.Column("recipient_name", sa.String(length=255), nullable=True),
    sa.Column("recipient_document_type", sa.String(length=10), nullable=True),
    sa.Column("recipient_document_number", sa.String(length=50), nullable=True),
    sa.Column("recipient_address", sa.String(length=500), nullable=True),
]


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("tenant", sa.Column("address", sa.String(length=500), nullable=True))
    op.add_column("owner", sa.Column("iban", sa.String(length=34), nullable=True))

    op.drop_index("uq_invoice_lease_period_active", table_name="invoice")

    op.add_column(
        "invoice",
        sa.Column(
            "series",
            sa.String(length=10),
            nullable=False,
            server_default=DEFAULT_SERIES,
        ),
    )
    for column in INVOICE_COLUMNS:
        op.add_column("invoice", column)
    op.execute(
        "ALTER TABLE invoice ADD COLUMN corrected_invoice_id INTEGER "
        "REFERENCES invoice(id)"
    )

    op.create_index("ix_invoice_fiscal_year", "invoice", ["fiscal_year"])
    op.create_index(
        "ix_invoice_corrected_invoice_id", "invoice", ["corrected_invoice_id"]
    )
    op.create_index(
        "uq_invoice_number_active",
        "invoice",
        ["number"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL AND number IS NOT NULL"),
    )
    op.create_index(
        "uq_invoice_lease_period_active",
        "invoice",
        ["lease_id", "period"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL AND corrected_invoice_id IS NULL"),
    )

    _backfill_legal_data()


def _backfill_legal_data() -> None:
    """Numera las facturas existentes y congela los datos fiscales actuales."""
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            "SELECT id, issue_date, lease_id FROM invoice ORDER BY issue_date, id"
        )
    ).fetchall()
    counters: dict[int, int] = defaultdict(int)

    for row in rows:
        issue = row.issue_date
        year = int(str(issue)[:4]) if not hasattr(issue, "year") else issue.year
        counters[year] += 1
        sequence = counters[year]
        bind.execute(
            sa.text(
                "UPDATE invoice SET series = :series, fiscal_year = :year, "
                "sequence = :sequence, number = :number, "
                f"due_date = date(issue_date, '+{LEGACY_PAYMENT_TERMS_DAYS} days') "
                "WHERE id = :id"
            ),
            {
                "series": DEFAULT_SERIES,
                "year": year,
                "sequence": sequence,
                "number": f"{DEFAULT_SERIES}-{year}-{sequence:04d}",
                "id": row.id,
            },
        )

        party = bind.execute(
            sa.text(
                "SELECT o.name AS owner_name, o.document_type AS owner_document_type, "
                "o.document_number AS owner_document_number, o.address AS owner_address, "
                "t.name AS tenant_name, t.document_type AS tenant_document_type, "
                "t.document_number AS tenant_document_number, t.address AS tenant_address "
                "FROM lease l "
                "LEFT JOIN owner o ON o.id = l.owner_id "
                "LEFT JOIN tenant t ON t.id = l.tenant_id "
                "WHERE l.id = :lease_id"
            ),
            {"lease_id": row.lease_id},
        ).mappings().first()

        if party is None:
            continue
        bind.execute(
            sa.text(
                "UPDATE invoice SET issuer_name = :owner_name, "
                "issuer_document_type = :owner_document_type, "
                "issuer_document_number = :owner_document_number, "
                "issuer_address = :owner_address, "
                "recipient_name = :tenant_name, "
                "recipient_document_type = :tenant_document_type, "
                "recipient_document_number = :tenant_document_number, "
                "recipient_address = :tenant_address "
                "WHERE id = :id"
            ),
            {**party, "id": row.id},
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("uq_invoice_lease_period_active", table_name="invoice")
    op.drop_index("uq_invoice_number_active", table_name="invoice")
    op.drop_index("ix_invoice_corrected_invoice_id", table_name="invoice")
    op.drop_index("ix_invoice_fiscal_year", table_name="invoice")

    op.drop_column("invoice", "corrected_invoice_id")
    for column in reversed(INVOICE_COLUMNS):
        op.drop_column("invoice", column.name)
    op.drop_column("invoice", "series")

    op.create_index(
        "uq_invoice_lease_period_active",
        "invoice",
        ["lease_id", "period"],
        unique=True,
        sqlite_where=sa.text("deleted_at IS NULL"),
    )

    op.drop_column("owner", "iban")
    op.drop_column("tenant", "address")
