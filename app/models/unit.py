from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship

from app.models.base import AuditMixin

if TYPE_CHECKING:
    from app.models.lease import Lease
    from app.models.property import Property


class Unit(AuditMixin, table=True):
    __tablename__ = "unit"

    property_id: int = Field(foreign_key="property.id", nullable=False)
    name: str = Field(max_length=255, nullable=False)
    unit_type: str = Field(max_length=50, nullable=False)
    area_m2: Optional[float] = Field(default=None)
    is_active: bool = Field(default=True)

    property: "Property" = Relationship(back_populates="units")
    leases: List["Lease"] = Relationship(back_populates="unit")
