from datetime import date
from decimal import Decimal
from typing import Optional

from sqlmodel import Session, select

from app.models.lease import IndexUpdate, Lease, RentCondition
from app.services.lease_service import LeaseService, NoActiveRentError

MAX_INDEX_RATE = Decimal("0.5")


class IndexUpdateError(Exception):
    """Raised when an index update cannot be applied."""


class IndexUpdateService:
    @staticmethod
    def apply_index(
        session: Session,
        lease_id: int,
        index_rate: Decimal,
        application_date: date,
        index_name: str = "IPC",
        notes: Optional[str] = None,
    ) -> tuple[RentCondition, IndexUpdate]:
        lease = session.get(Lease, lease_id)
        if lease is None or lease.deleted_at is not None:
            raise NoActiveRentError(f"Lease {lease_id} not found")

        if index_rate <= Decimal("-1") or index_rate > MAX_INDEX_RATE:
            raise IndexUpdateError(
                f"Index rate {index_rate} out of range (must be > -1 and <= {MAX_INDEX_RATE})"
            )

        existing = session.exec(
            select(IndexUpdate).where(
                IndexUpdate.lease_id == lease_id,
                IndexUpdate.application_date == application_date,
                IndexUpdate.deleted_at.is_(None),
            )
        ).first()
        if existing is not None:
            raise IndexUpdateError(
                f"An index update for lease {lease_id} on {application_date} already exists"
            )

        previous_rent = LeaseService.get_active_rent(session, lease_id, application_date)

        new_rent = (previous_rent * (Decimal("1") + index_rate)).quantize(Decimal("0.01"))

        new_condition = RentCondition(
            lease_id=lease_id,
            start_date=application_date,
            monthly_rent=new_rent,
            notes=notes,
        )
        session.add(new_condition)
        session.flush()

        index_update = IndexUpdate(
            lease_id=lease_id,
            application_date=application_date,
            previous_rent=previous_rent,
            new_rent=new_rent,
            index_rate=index_rate,
            index_name=index_name,
            notes=notes,
        )
        session.add(index_update)
        session.flush()

        return new_condition, index_update
