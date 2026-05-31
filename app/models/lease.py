from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Column, Numeric
from sqlmodel import Field, Relationship

from app.models.base import AuditMixin

if TYPE_CHECKING:
    from app.models.expense import Expense
    from app.models.invoice import Invoice
    from app.models.owner import Owner
    from app.models.tenant import Tenant
    from app.models.unit import Unit


class Lease(AuditMixin, table=True):
    __tablename__ = "lease"

    unit_id: int = Field(foreign_key="unit.id", nullable=False)
    tenant_id: int = Field(foreign_key="tenant.id", nullable=False)
    owner_id: int = Field(foreign_key="owner.id", nullable=False)
    start_date: date = Field(nullable=False)
    end_date: Optional[date] = Field(default=None)
    is_active: bool = Field(default=True)
    notes: Optional[str] = Field(default=None, max_length=2000)

    unit: "Unit" = Relationship(back_populates="leases")
    tenant: "Tenant" = Relationship(back_populates="leases")
    owner: "Owner" = Relationship(back_populates="leases")
    rent_conditions: List["RentCondition"] = Relationship(
        back_populates="lease"
    )
    tax_profile: Optional["TaxProfile"] = Relationship(
        back_populates="lease",
        sa_relationship_kwargs={"uselist": False},
    )
    deposit: Optional["Deposit"] = Relationship(
        back_populates="lease",
        sa_relationship_kwargs={"uselist": False},
    )
    index_updates: List["IndexUpdate"] = Relationship(
        back_populates="lease"
    )
    invoices: List["Invoice"] = Relationship(
        back_populates="lease"
    )
    expenses: List["Expense"] = Relationship(back_populates="lease")


class RentCondition(AuditMixin, table=True):
    __tablename__ = "rent_condition"

    lease_id: int = Field(foreign_key="lease.id", nullable=False)
    start_date: date = Field(nullable=False)
    monthly_rent: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(10, 2), nullable=False),
    )
    notes: Optional[str] = Field(default=None, max_length=1000)

    lease: "Lease" = Relationship(back_populates="rent_conditions")


class TaxProfile(AuditMixin, table=True):
    __tablename__ = "tax_profile"

    lease_id: int = Field(
        foreign_key="lease.id", nullable=False, unique=True
    )
    vat_rate: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(4, 2), nullable=False),
    )
    irpf_rate: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(4, 2), nullable=False),
    )
    vat_exempt: bool = Field(default=False)
    withholding_applies: bool = Field(default=False)

    lease: "Lease" = Relationship(back_populates="tax_profile")


class Deposit(AuditMixin, table=True):
    __tablename__ = "deposit"

    lease_id: int = Field(
        foreign_key="lease.id", nullable=False, unique=True
    )
    amount: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(10, 2), nullable=False),
    )
    deposit_date: date = Field(nullable=False)
    agency: str = Field(max_length=255, nullable=False)
    return_date: Optional[date] = Field(default=None)

    lease: "Lease" = Relationship(back_populates="deposit")


class IndexUpdate(AuditMixin, table=True):
    __tablename__ = "index_update"

    lease_id: int = Field(foreign_key="lease.id", nullable=False)
    application_date: date = Field(nullable=False)
    previous_rent: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(10, 2), nullable=False),
    )
    new_rent: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(10, 2), nullable=False),
    )
    index_rate: Decimal = Field(
        default=Decimal("0"),
        sa_column=Column(Numeric(6, 4), nullable=False),
    )
    index_name: str = Field(max_length=50, default="IPC")
    notes: Optional[str] = Field(default=None, max_length=1000)

    lease: "Lease" = Relationship(back_populates="index_updates")
