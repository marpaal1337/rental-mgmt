from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Column, Index, Numeric, text
from sqlmodel import Field, Relationship

from app.models.base import AuditMixin

if TYPE_CHECKING:
    from app.models.lease import Lease
    from app.models.payment import Payment


class Invoice(AuditMixin, table=True):
    __tablename__ = "invoice"
    __table_args__ = (
        Index(
            "uq_invoice_lease_period_active",
            "lease_id",
            "period",
            unique=True,
            sqlite_where=text("deleted_at IS NULL AND corrected_invoice_id IS NULL"),
        ),
        Index(
            "uq_invoice_number_active",
            "number",
            unique=True,
            sqlite_where=text("deleted_at IS NULL AND number IS NOT NULL"),
        ),
    )

    period: str = Field(max_length=7, nullable=False, index=True)
    lease_id: int = Field(foreign_key="lease.id", nullable=False, index=True)
    issue_date: date = Field(nullable=False)
    due_date: Optional[date] = Field(default=None)
    status: str = Field(max_length=20, default="draft", index=True)
    series: str = Field(max_length=10, default="A", nullable=False)
    sequence: Optional[int] = Field(default=None)
    number: Optional[str] = Field(default=None, max_length=40)
    fiscal_year: Optional[int] = Field(default=None, index=True)
    corrected_invoice_id: Optional[int] = Field(
        default=None, foreign_key="invoice.id", index=True
    )
    rectification_reason: Optional[str] = Field(default=None, max_length=500)
    issuer_name: Optional[str] = Field(default=None, max_length=255)
    issuer_document_type: Optional[str] = Field(default=None, max_length=10)
    issuer_document_number: Optional[str] = Field(default=None, max_length=50)
    issuer_address: Optional[str] = Field(default=None, max_length=500)
    recipient_name: Optional[str] = Field(default=None, max_length=255)
    recipient_document_type: Optional[str] = Field(default=None, max_length=10)
    recipient_document_number: Optional[str] = Field(default=None, max_length=50)
    recipient_address: Optional[str] = Field(default=None, max_length=500)
    total_base: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(12, 2), nullable=False),
    )
    total_vat: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(12, 2), nullable=False),
    )
    total_irpf_withholding: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(12, 2), nullable=False),
    )
    total: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(12, 2), nullable=False),
    )
    notes: Optional[str] = Field(default=None, max_length=2000)

    lease: "Lease" = Relationship(back_populates="invoices")
    lines: List["InvoiceLine"] = Relationship(back_populates="invoice")
    payments: List["Payment"] = Relationship(back_populates="invoice")


class InvoiceLine(AuditMixin, table=True):
    __tablename__ = "invoice_line"

    invoice_id: int = Field(foreign_key="invoice.id", nullable=False, index=True)
    concept: str = Field(max_length=500, nullable=False)
    base_amount: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(12, 2), nullable=False),
    )
    vat_rate: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(4, 2), nullable=False),
    )
    vat_amount: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(12, 2), nullable=False),
    )
    irpf_rate: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(4, 2), nullable=False),
    )
    irpf_withholding: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(12, 2), nullable=False),
    )

    invoice: "Invoice" = Relationship(back_populates="lines")
