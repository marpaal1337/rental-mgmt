from datetime import date
from decimal import Decimal

from sqlmodel import Session, select

from app.models.invoice import Invoice
from app.models.lease import RentCondition, TaxProfile
from app.services.invoice_service import (
    InvoiceGenerationError,
    InvoiceService,
)


class TestGenerateMonthly:
    def test_vivienda_invoice_no_taxes(self, session: Session, sample_lease):
        rc = RentCondition(
            lease_id=sample_lease.id,
            start_date=date(2024, 1, 1),
            monthly_rent=Decimal("850.00"),
        )
        session.add(rc)
        tax = TaxProfile(
            lease_id=sample_lease.id,
            vat_rate=Decimal("0"),
            irpf_rate=Decimal("0"),
            vat_exempt=True,
            withholding_applies=False,
        )
        session.add(tax)
        session.commit()

        invoices = InvoiceService.generate_monthly(session, "2024-06")

        assert len(invoices) == 1
        inv = invoices[0]
        assert inv.period == "2024-06"
        assert inv.total_base == Decimal("850.00")
        assert inv.total_vat == Decimal("0")
        assert inv.total_irpf_withholding == Decimal("0")
        assert inv.total == Decimal("850.00")
        assert inv.status == "draft"
        assert inv.lease_id == sample_lease.id

    def test_local_invoice_with_taxes(self, session: Session, sample_lease):
        rc = RentCondition(
            lease_id=sample_lease.id,
            start_date=date(2024, 1, 1),
            monthly_rent=Decimal("1500.00"),
        )
        session.add(rc)
        tax = TaxProfile(
            lease_id=sample_lease.id,
            vat_rate=Decimal("21.00"),
            irpf_rate=Decimal("19.00"),
            vat_exempt=False,
            withholding_applies=True,
        )
        session.add(tax)
        session.commit()

        invoices = InvoiceService.generate_monthly(session, "2024-06")

        assert len(invoices) == 1
        inv = invoices[0]
        assert inv.total_base == Decimal("1500.00")
        assert inv.total_vat == Decimal("315.00")
        assert inv.total_irpf_withholding == Decimal("285.00")
        assert inv.total == Decimal("1530.00")

    def test_idempotent_does_not_duplicate(self, session: Session, sample_lease):
        rc = RentCondition(
            lease_id=sample_lease.id,
            start_date=date(2024, 1, 1),
            monthly_rent=Decimal("1000.00"),
        )
        session.add(rc)
        tax = TaxProfile(
            lease_id=sample_lease.id,
            vat_rate=Decimal("0"),
            irpf_rate=Decimal("0"),
            vat_exempt=True,
            withholding_applies=False,
        )
        session.add(tax)
        session.commit()

        first = InvoiceService.generate_monthly(session, "2024-06")
        second = InvoiceService.generate_monthly(session, "2024-06")

        assert len(first) == 1
        assert len(second) == 0

        all_invoices = session.exec(select(Invoice)).all()
        assert len(all_invoices) == 1

    def test_leases_without_tax_profile_raises(self, session: Session, sample_lease):
        rc = RentCondition(
            lease_id=sample_lease.id,
            start_date=date(2024, 1, 1),
            monthly_rent=Decimal("1000.00"),
        )
        session.add(rc)
        session.commit()

        from pytest import raises

        with raises(InvoiceGenerationError):
            InvoiceService.generate_monthly(session, "2024-06")

    def test_inactive_lease_ignored(self, session: Session, sample_lease):
        sample_lease.is_active = False
        rc = RentCondition(
            lease_id=sample_lease.id,
            start_date=date(2024, 1, 1),
            monthly_rent=Decimal("1000.00"),
        )
        session.add(rc)
        tax = TaxProfile(
            lease_id=sample_lease.id,
            vat_rate=Decimal("0"),
            irpf_rate=Decimal("0"),
            vat_exempt=True,
            withholding_applies=False,
        )
        session.add(tax)
        session.commit()

        invoices = InvoiceService.generate_monthly(session, "2024-06")
        assert len(invoices) == 0
