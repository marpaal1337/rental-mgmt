from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlmodel import Session, select

from app.config import INVOICE_PAYMENT_TERMS_DAYS
from app.models.invoice import Invoice
from app.models.lease import RentCondition, TaxProfile
from app.models.owner import Owner
from app.models.tenant import Tenant
from app.services.invoice_numbering_service import (
    InvoiceNumberingError,
    InvoiceNumberingService,
)
from app.services.invoice_service import InvoiceRectificationError, InvoiceService
from app.services.payment_service import PaymentError, PaymentService


def _add_rent(session: Session, lease_id: int, rent: str, start: date = date(2024, 1, 1)) -> None:
    session.add(
        RentCondition(
            lease_id=lease_id,
            start_date=start,
            monthly_rent=Decimal(rent),
        )
    )
    session.commit()


def _add_tax_profile(
    session: Session,
    lease_id: int,
    *,
    vat: str = "0",
    irpf: str = "0",
    exempt: bool = True,
    withholding: bool = False,
) -> None:
    session.add(
        TaxProfile(
            lease_id=lease_id,
            vat_rate=Decimal(vat),
            irpf_rate=Decimal(irpf),
            vat_exempt=exempt,
            withholding_applies=withholding,
        )
    )
    session.commit()


def _new_invoice(
    lease_id: int, issue_date: date, period: str | None = None
) -> Invoice:
    return Invoice(
        period=period or f"{issue_date.year}-{issue_date.month:02d}",
        lease_id=lease_id,
        issue_date=issue_date,
        status="issued",
        total_base=Decimal("100.00"),
        total_vat=Decimal("0"),
        total_irpf_withholding=Decimal("0"),
        total=Decimal("100.00"),
    )


def _issued_invoice(session: Session, sample_lease, rent: str = "1000.00") -> Invoice:
    _add_rent(session, sample_lease.id, rent)
    _add_tax_profile(session, sample_lease.id)
    invoices = InvoiceService.generate_monthly(session, "2024-06")
    session.commit()
    return invoices[0]


class TestNumberingService:
    def test_format_number(self):
        assert InvoiceNumberingService.format_number("A", 2026, 1) == "A-2026-0001"
        assert InvoiceNumberingService.format_number("R", 2026, 42) == "R-2026-0042"

    def test_sequential_within_series_and_year(self, session: Session, sample_lease):
        first = _new_invoice(sample_lease.id, date(2024, 1, 10))
        second = _new_invoice(sample_lease.id, date(2024, 2, 10), period="2024-02")

        assert InvoiceNumberingService.assign_number(session, first) == "A-2024-0001"
        assert InvoiceNumberingService.assign_number(session, second) == "A-2024-0002"
        session.commit()

    def test_sequence_restarts_each_year(self, session: Session, sample_lease):
        old = _new_invoice(sample_lease.id, date(2024, 1, 10))
        new = _new_invoice(sample_lease.id, date(2025, 1, 10))

        InvoiceNumberingService.assign_number(session, old)
        assert InvoiceNumberingService.assign_number(session, new) == "A-2025-0001"

    def test_series_are_independent(self, session: Session, sample_lease):
        ordinary = _new_invoice(sample_lease.id, date(2024, 1, 10))
        rectification = _new_invoice(sample_lease.id, date(2024, 2, 11))

        assert InvoiceNumberingService.assign_number(session, ordinary) == "A-2024-0001"
        number = InvoiceNumberingService.assign_number(
            session,
            rectification,
            series=InvoiceNumberingService.RECTIFICATION_SERIES,
        )
        assert number == "R-2024-0001"

    def test_deleted_invoice_does_not_release_number(self, session: Session, sample_lease):
        first = _new_invoice(sample_lease.id, date(2024, 1, 10))
        InvoiceNumberingService.assign_number(session, first)
        session.commit()

        first.deleted_at = first.created_at
        session.add(first)
        session.commit()

        second = _new_invoice(sample_lease.id, date(2024, 2, 10), period="2024-02")
        assert InvoiceNumberingService.assign_number(session, second) == "A-2024-0002"

    def test_existing_number_is_returned_unchanged(self, session: Session, sample_lease):
        invoice = _new_invoice(sample_lease.id, date(2024, 1, 10))
        assert InvoiceNumberingService.assign_number(session, invoice) == "A-2024-0001"

        invoice.issue_date = date(2025, 1, 10)
        assert InvoiceNumberingService.assign_number(session, invoice) == "A-2024-0001"

    def test_exhausted_attempts_raise(self, session: Session, sample_lease, monkeypatch):
        first = _new_invoice(sample_lease.id, date(2024, 1, 10))
        InvoiceNumberingService.assign_number(session, first)
        session.commit()

        monkeypatch.setattr(
            InvoiceNumberingService,
            "_next_sequence",
            staticmethod(lambda session, series, fiscal_year: 1),
        )
        conflicting = _new_invoice(sample_lease.id, date(2024, 2, 10), period="2024-02")
        with pytest.raises(InvoiceNumberingError):
            InvoiceNumberingService.assign_number(session, conflicting)


class TestGenerateMonthlyLegalData:
    def test_assigns_number_due_date_and_fiscal_year(self, session: Session, sample_lease):
        invoice = _issued_invoice(session, sample_lease)

        today = date.today()
        assert invoice.number == f"A-{today.year}-0001"
        assert invoice.series == "A"
        assert invoice.sequence == 1
        assert invoice.fiscal_year == today.year
        assert invoice.due_date == today + timedelta(days=INVOICE_PAYMENT_TERMS_DAYS)

    def test_numbers_are_sequential_across_leases(self, session: Session, sample_lease):
        _add_rent(session, sample_lease.id, "1000.00")
        _add_tax_profile(session, sample_lease.id)

        other_tenant = Tenant(
            name="Other Tenant",
            document_type="DNI",
            document_number="33333333C",
            email="other@test.com",
            phone="+34 622 222 222",
        )
        session.add(other_tenant)
        session.flush()
        from app.models.lease import Lease

        other_lease = Lease(
            unit_id=sample_lease.unit_id,
            tenant_id=other_tenant.id,
            owner_id=sample_lease.owner_id,
            start_date=date(2024, 1, 1),
            is_active=True,
        )
        session.add(other_lease)
        session.flush()
        _add_rent(session, other_lease.id, "500.00")
        _add_tax_profile(session, other_lease.id)

        invoices = InvoiceService.generate_monthly(session, "2024-06")
        session.commit()

        numbers = {invoice.number for invoice in invoices}
        year = date.today().year
        assert numbers == {f"A-{year}-0001", f"A-{year}-0002"}

    def test_snapshot_is_frozen_at_generation(self, session: Session, sample_lease):
        owner = session.get(Owner, sample_lease.owner_id)
        tenant = session.get(Tenant, sample_lease.tenant_id)
        owner.address = "Calle Emisor 1"
        tenant.address = "Calle Receptor 1"
        session.add(owner)
        session.add(tenant)
        session.commit()

        invoice = _issued_invoice(session, sample_lease)

        owner.address = "Calle Emisor 2"
        owner.name = "Owner Renombrado"
        owner.document_number = "99999999Z"
        tenant.address = "Calle Receptor 2"
        session.add(owner)
        session.add(tenant)
        session.commit()

        session.refresh(invoice)
        assert invoice.issuer_name == "Test Owner"
        assert invoice.issuer_document_number == "11111111A"
        assert invoice.issuer_address == "Calle Emisor 1"
        assert invoice.recipient_name == "Test Tenant"
        assert invoice.recipient_address == "Calle Receptor 1"


class TestRectify:
    def test_creates_negative_invoice_in_rectification_series(
        self, session: Session, sample_lease
    ):
        original = _issued_invoice(session, sample_lease, rent="1500.00")

        rectification = InvoiceService.rectify(session, original.id, "Importe incorrecto")
        session.commit()

        assert rectification.corrected_invoice_id == original.id
        assert rectification.series == "R"
        assert rectification.number == f"R-{date.today().year}-0001"
        assert rectification.rectification_reason == "Importe incorrecto"
        assert rectification.total == -original.total
        assert rectification.total_base == -original.total_base
        assert rectification.period == original.period
        assert len(rectification.lines) == 1
        assert rectification.lines[0].base_amount == -original.lines[0].base_amount
        assert "Rectificación" in rectification.lines[0].concept
        assert original.deleted_at is None

    def test_double_rectification_rejected(self, session: Session, sample_lease):
        original = _issued_invoice(session, sample_lease)
        InvoiceService.rectify(session, original.id, "Primera")
        session.commit()

        with pytest.raises(InvoiceRectificationError, match="already rectified"):
            InvoiceService.rectify(session, original.id, "Segunda")

    def test_cannot_rectify_a_rectification(self, session: Session, sample_lease):
        original = _issued_invoice(session, sample_lease)
        rectification = InvoiceService.rectify(session, original.id, "Motivo")
        session.commit()

        with pytest.raises(InvoiceRectificationError, match="cannot be rectified"):
            InvoiceService.rectify(session, rectification.id, "Otra")

    def test_reason_is_required(self, session: Session, sample_lease):
        original = _issued_invoice(session, sample_lease)
        with pytest.raises(InvoiceRectificationError, match="reason is required"):
            InvoiceService.rectify(session, original.id, "   ")

    def test_not_found(self, session: Session):
        with pytest.raises(InvoiceRectificationError, match="not found"):
            InvoiceService.rectify(session, 999, "Motivo")

    def test_generation_is_not_repeated_after_rectification(
        self, session: Session, sample_lease
    ):
        original = _issued_invoice(session, sample_lease)
        InvoiceService.rectify(session, original.id, "Motivo")
        session.commit()

        assert InvoiceService.generate_monthly(session, "2024-06") == []

    def test_payment_on_rectification_is_rejected(self, session: Session, sample_lease):
        original = _issued_invoice(session, sample_lease)
        rectification = InvoiceService.rectify(session, original.id, "Motivo")
        session.commit()

        with pytest.raises(PaymentError, match="no payable amount"):
            PaymentService.register(
                session, rectification.id, Decimal("10.00"), date(2024, 7, 1)
            )

    def test_rectification_status_stays_issued(self, session: Session, sample_lease):
        original = _issued_invoice(session, sample_lease)
        rectification = InvoiceService.rectify(session, original.id, "Motivo")
        session.commit()

        PaymentService._update_invoice_status(session, rectification)
        assert rectification.status == "issued"

    def test_rectification_status_resets_if_marked_paid(self, session: Session, sample_lease):
        original = _issued_invoice(session, sample_lease)
        rectification = InvoiceService.rectify(session, original.id, "Motivo")
        rectification.status = "paid"
        session.add(rectification)
        session.flush()

        PaymentService._update_invoice_status(session, rectification)
        assert rectification.status == "issued"

    def test_numbers_continue_after_rectification(self, session: Session, sample_lease):
        original = _issued_invoice(session, sample_lease)
        InvoiceService.rectify(session, original.id, "Motivo")
        session.commit()

        invoices = session.exec(select(Invoice)).all()
        ordinary = [i for i in invoices if i.corrected_invoice_id is None]
        rectifications = [i for i in invoices if i.corrected_invoice_id is not None]
        assert ordinary[0].number == f"A-{date.today().year}-0001"
        assert rectifications[0].number == f"R-{date.today().year}-0001"
