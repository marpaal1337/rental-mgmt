from typing import Optional

from sqlmodel import Field

from app.models.base import AuditMixin


class EventLog(AuditMixin, table=True):
    __tablename__ = "event_log"

    event_type: str = Field(max_length=100, nullable=False)
    description: str = Field(max_length=500, nullable=False)
    details: Optional[str] = Field(default=None, max_length=5000)
    level: str = Field(max_length=20, default="info")
