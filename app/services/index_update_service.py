from datetime import date
from decimal import Decimal
from typing import Optional

from sqlmodel import Session

from app.models.lease import IndexUpdate, Lease, RentCondition
from app.services.lease_service import LeaseService, NoActiveRentError


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
        if lease is None:
            raise NoActiveRentError(f"Lease {lease_id} not found")

        previous_rent = LeaseService.get_active_rent(
            session, lease_id, application_date
        )

        new_rent = (previous_rent * (Decimal("1") + index_rate)).quantize(
            Decimal("0.01")
        )

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
