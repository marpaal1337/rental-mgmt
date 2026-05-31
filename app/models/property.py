from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship

from app.models.base import AuditMixin

if TYPE_CHECKING:
    from app.models.expense import Expense
    from app.models.owner import Owner
    from app.models.unit import Unit


class Property(AuditMixin, table=True):
    __tablename__ = "property"

    name: str = Field(max_length=255, nullable=False)
    address: str = Field(max_length=500, nullable=False)
    city: str = Field(max_length=100, nullable=False)
    province: str = Field(max_length=100, nullable=False)
    zip_code: str = Field(max_length=10, nullable=False)
    cadastral_ref: Optional[str] = Field(default=None, max_length=50)
    owner_id: int = Field(foreign_key="owner.id", nullable=False)

    owner: "Owner" = Relationship(back_populates="properties")
    units: List["Unit"] = Relationship(back_populates="property")
    expenses: List["Expense"] = Relationship(back_populates="property")
