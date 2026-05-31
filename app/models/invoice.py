from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Column, Numeric
from sqlmodel import Field, Relationship

from app.models.base import AuditMixin

if TYPE_CHECKING:
    from app.models.lease import Lease
    from app.models.payment import Payment


class Invoice(AuditMixin, table=True):
    __tablename__ = "invoice"

    period: str = Field(max_length=7, nullable=False)
    lease_id: int = Field(foreign_key="lease.id", nullable=False)
    issue_date: date = Field(nullable=False)
    status: str = Field(max_length=20, default="draft")
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

    invoice_id: int = Field(foreign_key="invoice.id", nullable=False)
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
