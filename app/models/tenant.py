from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship

from app.models.base import AuditMixin

if TYPE_CHECKING:
    from app.models.lease import Lease


class Tenant(AuditMixin, table=True):
    __tablename__ = "tenant"

    name: str = Field(max_length=255, nullable=False)
    document_type: str = Field(max_length=10, nullable=False)
    document_number: str = Field(max_length=50, nullable=False)
    email: str = Field(max_length=255, nullable=False)
    phone: str = Field(max_length=50, nullable=False)
    address: Optional[str] = Field(default=None, max_length=500)

    leases: List["Lease"] = Relationship(back_populates="tenant")
