from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, Numeric
from sqlmodel import Field, Relationship

from app.models.base import AuditMixin

if TYPE_CHECKING:
    from app.models.payment import Payment


class BankMovement(AuditMixin, table=True):
    __tablename__ = "bank_movement"

    entry_date: date = Field(nullable=False)
    value_date: Optional[date] = Field(default=None)
    amount: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(12, 2), nullable=False),
    )
    concept: str = Field(max_length=500, nullable=False)
    iban_origin: Optional[str] = Field(default=None, max_length=34)
    reference: Optional[str] = Field(default=None, max_length=100)
    status: str = Field(max_length=20, default="unmatched")
    raw_data: Optional[str] = Field(
        default=None, max_length=2000
    )

    reconciliation: Optional["Reconciliation"] = Relationship(
        back_populates="bank_movement",
        sa_relationship_kwargs={"uselist": False},
    )


class Reconciliation(AuditMixin, table=True):
    __tablename__ = "reconciliation"

    bank_movement_id: int = Field(
        foreign_key="bank_movement.id", nullable=False, unique=True
    )
    payment_id: int = Field(
        foreign_key="payment.id", nullable=False
    )
    score: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(3, 2), nullable=False),
    )
    confirmed_at: Optional[datetime] = Field(default=None)
    notes: Optional[str] = Field(default=None, max_length=1000)

    bank_movement: "BankMovement" = Relationship(
        back_populates="reconciliation"
    )
    payment: "Payment" = Relationship(back_populates="reconciliations")
