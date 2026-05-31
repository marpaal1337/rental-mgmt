from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, Numeric
from sqlmodel import Field, Relationship

from app.models.base import AuditMixin

if TYPE_CHECKING:
    from app.models.lease import Lease
    from app.models.property import Property


EXPENSE_CATEGORIES = [
    "community",
    "repairs",
    "supplies",
    "taxes",
    "insurance",
    "admin_fees",
    "other",
]


class Expense(AuditMixin, table=True):
    __tablename__ = "expense"

    property_id: int = Field(foreign_key="property.id", nullable=False)
    lease_id: Optional[int] = Field(
        default=None, foreign_key="lease.id", nullable=True
    )
    category: str = Field(max_length=50, nullable=False)
    amount: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(12, 2), nullable=False),
    )
    expense_date: date = Field(nullable=False)
    deductible: bool = Field(default=True)
    supplier: Optional[str] = Field(default=None, max_length=255)
    invoice_number: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = Field(default=None, max_length=2000)

    property: "Property" = Relationship(back_populates="expenses")
    lease: Optional["Lease"] = Relationship(back_populates="expenses")
