from datetime import date
from decimal import Decimal
from typing import Optional

from sqlmodel import Session, select

from app.models.lease import Lease, RentCondition


class NoActiveRentError(Exception):
    """Raised when no rent condition is active for the given date."""


class LeaseService:
    @staticmethod
    def get_active_rent(
        session: Session, lease_id: int, target_date: Optional[date] = None
    ) -> Decimal:
        if target_date is None:
            target_date = date.today()

        lease = session.get(Lease, lease_id)
        if lease is None or lease.deleted_at is not None:
            raise NoActiveRentError(f"Lease {lease_id} not found")

        statement = (
            select(RentCondition)
            .where(RentCondition.lease_id == lease_id)
            .where(RentCondition.start_date <= target_date)
            .where(RentCondition.deleted_at.is_(None))
            .order_by(RentCondition.start_date.desc())
            .limit(1)
        )
        result = session.exec(statement).first()

        if result is None:
            raise NoActiveRentError(
                f"No active rent condition for lease {lease_id} on {target_date}"
            )

        return result.monthly_rent
