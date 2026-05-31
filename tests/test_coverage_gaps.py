from datetime import date
from decimal import Decimal

from sqlmodel import Session

from app.models.bank import BankMovement, Reconciliation
from app.models.invoice import Invoice, InvoiceLine
from app.models.lease import Lease, RentCondition, TaxProfile
from app.models.payment import Payment
from app.services.index_update_service import IndexUpdateService
from app.services.lease_service import NoActiveRentError
from app.services.payment_service import PaymentService
from app.services.pdf_service import PDFGenerationError, PDFService
from app.services.reconciliation_service import ReconciliationService


class TestIndexUpdateServiceCoverage:
    def test_lease_not_found(self, session: Session):
        from pytest import raises

        with raises(NoActiveRentError, match="Lease 999 not found"):
            IndexUpdateService.apply_index(session, 999, Decimal("0.02"), date(2024, 7, 1))


class TestPaymentServiceCoverage:
    def test_payment_status_stays_draft_when_no_payments(
        self, session: Session, sample_lease: Lease
    ):
        inv = Invoice(
            period="2024-06",
            lease_id=sample_lease.id,
            issue_date=date(2024, 6, 1),
            status="draft",
            total_base=Decimal("850.00"),
            total_vat=Decimal("0"),
            total_irpf_withholding=Decimal("0"),
            total=Decimal("850.00"),
        )
        session.add(inv)
        session.commit()

        PaymentService._update_invoice_status(session, inv)
        session.commit()

        updated = session.get(Invoice, inv.id)
        assert updated.status == "draft"


class TestPDFServiceCoverage:
    def test_invoice_no_lines_raises(self, session: Session, sample_lease: Lease):
        inv = Invoice(
            period="2024-06",
            lease_id=sample_lease.id,
            issue_date=date(2024, 6, 1),
            status="draft",
            total_base=Decimal("850.00"),
            total_vat=Decimal("0"),
            total_irpf_withholding=Decimal("0"),
            total=Decimal("850.00"),
        )
        session.add(inv)
        session.commit()

        from pytest import raises

        with raises(PDFGenerationError, match="has no lines"):
            PDFService.render_invoice(session, inv.id)

    def test_owner_with_address_in_pdf(self, session: Session, sample_lease: Lease):
        sample_lease.owner.address = "Calle Mayor 1, Madrid"
        session.commit()

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
        session.flush()

        inv = Invoice(
            period="2024-06",
            lease_id=sample_lease.id,
            issue_date=date(2024, 6, 1),
            status="draft",
            total_base=Decimal("850.00"),
            total_vat=Decimal("0"),
            total_irpf_withholding=Decimal("0"),
            total=Decimal("850.00"),
        )
        session.add(inv)
        session.flush()

        line = InvoiceLine(
            invoice_id=inv.id,
            concept="Alquiler 2024-06",
            base_amount=Decimal("850.00"),
            vat_rate=Decimal("0"),
            vat_amount=Decimal("0"),
            irpf_rate=Decimal("0"),
            irpf_withholding=Decimal("0"),
        )
        session.add(line)
        session.commit()

        path = PDFService.render_invoice(session, inv.id)
        assert path.exists()


class TestReconciliationCoverage:
    def test_skip_already_confirmed_payment(self, session: Session, sample_lease: Lease):
        payment = Payment(
            invoice_id=0,
            amount=Decimal("100.00"),
            payment_date=date(2024, 7, 1),
            method="transferencia",
        )
        inv = Invoice(
            period="2024-07",
            lease_id=sample_lease.id,
            issue_date=date(2024, 7, 1),
            status="draft",
            total_base=Decimal("100"),
            total_vat=Decimal("0"),
            total_irpf_withholding=Decimal("0"),
            total=Decimal("100"),
        )
        session.add(inv)
        session.commit()
        payment.invoice_id = inv.id
        session.add(payment)
        session.commit()

        movement = BankMovement(
            entry_date=date(2024, 7, 1),
            amount=Decimal("100.00"),
            concept="Test",
            status="unmatched",
        )
        session.add(movement)
        session.commit()

        # Payment already matched to another movement
        other = BankMovement(
            entry_date=date(2024, 7, 1),
            amount=Decimal("100.00"),
            concept="Other",
            status="confirmed",
        )
        session.add(other)
        session.commit()
        existing = Reconciliation(
            bank_movement_id=other.id,
            payment_id=payment.id,
            score=Decimal("0.9"),
            confirmed_at=__import__("datetime").datetime.now(),
        )
        session.add(existing)
        session.commit()

        recs = ReconciliationService.propose_matches(session, movement.id)
        assert len(recs) == 0

    def test_concept_match_contributes_score(self, session: Session, sample_lease: Lease):
        payment = Payment(
            invoice_id=0,
            amount=Decimal("850.00"),
            payment_date=date(2024, 7, 1),
            method="transferencia",
        )
        inv = Invoice(
            period="2024-07",
            lease_id=sample_lease.id,
            issue_date=date(2024, 7, 1),
            status="draft",
            total_base=Decimal("850"),
            total_vat=Decimal("0"),
            total_irpf_withholding=Decimal("0"),
            total=Decimal("850"),
        )
        session.add(inv)
        session.commit()
        payment.invoice_id = inv.id
        session.add(payment)
        session.flush()

        movement = BankMovement(
            entry_date=date(2024, 7, 1),
            amount=Decimal("850.00"),
            concept="1",
            iban_origin="ES9121000418450200051332",
            status="unmatched",
        )
        session.add(movement)
        session.commit()

        score = ReconciliationService._match_score(movement, payment)
        assert score > Decimal("0.5")
