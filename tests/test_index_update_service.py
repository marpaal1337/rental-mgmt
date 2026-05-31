from datetime import date
from decimal import Decimal

from sqlmodel import Session

from app.models.lease import RentCondition
from app.services.index_update_service import IndexUpdateService
from app.services.lease_service import LeaseService


class TestApplyIndex:
    def test_apply_index_creates_new_rent_and_record(
        self, session: Session, sample_lease
    ):
        rc = RentCondition(
            lease_id=sample_lease.id,
            start_date=date(2024, 1, 1),
            monthly_rent=Decimal("1000.00"),
        )
        session.add(rc)
        session.commit()

        new_condition, index_update = IndexUpdateService.apply_index(
            session=session,
            lease_id=sample_lease.id,
            index_rate=Decimal("0.02"),
            application_date=date(2025, 1, 1),
            index_name="IPC",
        )

        assert new_condition.monthly_rent == Decimal("1020.00")
        assert new_condition.start_date == date(2025, 1, 1)
        assert new_condition.lease_id == sample_lease.id

        assert index_update.previous_rent == Decimal("1000.00")
        assert index_update.new_rent == Decimal("1020.00")
        assert index_update.index_rate == Decimal("0.02")
        assert index_update.index_name == "IPC"
        assert index_update.application_date == date(2025, 1, 1)

        active_rent = LeaseService.get_active_rent(
            session, sample_lease.id, date(2025, 6, 1)
        )
        assert active_rent == Decimal("1020.00")

    def test_apply_index_multiple_times(
        self, session: Session, sample_lease
    ):
        rc = RentCondition(
            lease_id=sample_lease.id,
            start_date=date(2024, 1, 1),
            monthly_rent=Decimal("1000.00"),
        )
        session.add(rc)
        session.commit()

        IndexUpdateService.apply_index(
            session=session,
            lease_id=sample_lease.id,
            index_rate=Decimal("0.02"),
            application_date=date(2025, 1, 1),
        )

        IndexUpdateService.apply_index(
            session=session,
            lease_id=sample_lease.id,
            index_rate=Decimal("0.015"),
            application_date=date(2026, 1, 1),
        )

        active_rent = LeaseService.get_active_rent(
            session, sample_lease.id, date(2026, 6, 1)
        )
        expected = Decimal("1020.00") * Decimal("1.015")
        expected = expected.quantize(Decimal("0.01"))
        assert active_rent == expected

    def test_apply_index_zero_rate(
        self, session: Session, sample_lease
    ):
        rc = RentCondition(
            lease_id=sample_lease.id,
            start_date=date(2024, 1, 1),
            monthly_rent=Decimal("1000.00"),
        )
        session.add(rc)
        session.commit()

        new_condition, _ = IndexUpdateService.apply_index(
            session=session,
            lease_id=sample_lease.id,
            index_rate=Decimal("0"),
            application_date=date(2025, 1, 1),
        )
        assert new_condition.monthly_rent == Decimal("1000.00")
