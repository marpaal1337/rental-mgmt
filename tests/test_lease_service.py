from datetime import date
from decimal import Decimal

from sqlmodel import Session

from app.models.lease import RentCondition
from app.services.lease_service import LeaseService, NoActiveRentError


class TestGetActiveRent:
    def test_single_rent_condition(self, session: Session, sample_lease):
        rc = RentCondition(
            lease_id=sample_lease.id,
            start_date=date(2024, 1, 1),
            monthly_rent=Decimal("850.00"),
        )
        session.add(rc)
        session.commit()

        rent = LeaseService.get_active_rent(session, sample_lease.id, date(2024, 6, 1))
        assert rent == Decimal("850.00")

    def test_multiple_rent_conditions(self, session: Session, sample_lease):
        rc1 = RentCondition(
            lease_id=sample_lease.id,
            start_date=date(2024, 1, 1),
            monthly_rent=Decimal("850.00"),
        )
        rc2 = RentCondition(
            lease_id=sample_lease.id,
            start_date=date(2025, 1, 1),
            monthly_rent=Decimal("875.00"),
        )
        session.add(rc1)
        session.add(rc2)
        session.commit()

        rent_before = LeaseService.get_active_rent(session, sample_lease.id, date(2024, 6, 1))
        assert rent_before == Decimal("850.00")

        rent_after = LeaseService.get_active_rent(session, sample_lease.id, date(2025, 6, 1))
        assert rent_after == Decimal("875.00")

        rent_exact = LeaseService.get_active_rent(session, sample_lease.id, date(2025, 1, 1))
        assert rent_exact == Decimal("875.00")

    def test_no_rent_condition_raises(self, session: Session, sample_lease):
        from pytest import raises

        with raises(NoActiveRentError):
            LeaseService.get_active_rent(session, sample_lease.id, date(2024, 6, 1))

    def test_date_before_any_condition_raises(self, session: Session, sample_lease):
        rc = RentCondition(
            lease_id=sample_lease.id,
            start_date=date(2024, 6, 1),
            monthly_rent=Decimal("850.00"),
        )
        session.add(rc)
        session.commit()

        from pytest import raises

        with raises(NoActiveRentError):
            LeaseService.get_active_rent(session, sample_lease.id, date(2024, 1, 1))

    def test_unknown_lease_raises(self, session: Session):
        from pytest import raises

        with raises(NoActiveRentError):
            LeaseService.get_active_rent(session, 999, date(2024, 6, 1))

    def test_default_date(self, session: Session, sample_lease):
        rc = RentCondition(
            lease_id=sample_lease.id,
            start_date=date(2000, 1, 1),
            monthly_rent=Decimal("500.00"),
        )
        session.add(rc)
        session.commit()

        rent = LeaseService.get_active_rent(session, sample_lease.id)
        assert rent == Decimal("500.00")
