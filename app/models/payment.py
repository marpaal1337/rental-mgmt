from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, Numeric
from sqlmodel import Field, Relationship

from app.models.base import AuditMixin

if TYPE_CHECKING:
    from app.models.invoice import Invoice


class Payment(AuditMixin, table=True):
    __tablename__ = "payment"

    invoice_id: int = Field(foreign_key="invoice.id", nullable=False)
    amount: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(12, 2), nullable=False),
    )
    payment_date: date = Field(nullable=False)
    method: str = Field(max_length=50, nullable=False)
    notes: Optional[str] = Field(default=None, max_length=1000)

    invoice: "Invoice" = Relationship(back_populates="payments")
