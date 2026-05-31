from datetime import date
from decimal import Decimal

from sqlmodel import Session, select

from app.models.invoice import Invoice, InvoiceLine
from app.models.lease import RentCondition, TaxProfile
from app.models.payment import Payment
from app.services.payment_service import PaymentError, PaymentService


class TestRegisterPayment:
    def _create_invoice(self, session: Session, sample_lease, total: Decimal):
        rc = RentCondition(
            lease_id=sample_lease.id,
            start_date=date(2024, 1, 1),
            monthly_rent=total,
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
            total_base=total,
            total_vat=Decimal("0"),
            total_irpf_withholding=Decimal("0"),
            total=total,
        )
        session.add(inv)
        session.flush()

        line = InvoiceLine(
            invoice_id=inv.id,
            concept="Alquiler 2024-06",
            base_amount=total,
            vat_rate=Decimal("0"),
            vat_amount=Decimal("0"),
            irpf_rate=Decimal("0"),
            irpf_withholding=Decimal("0"),
        )
        session.add(line)
        session.commit()
        return inv

    def test_full_payment_marks_invoice_paid(self, session: Session, sample_lease):
        inv = self._create_invoice(session, sample_lease, Decimal("850.00"))

        payment = PaymentService.register(session, inv.id, Decimal("850.00"), date(2024, 7, 1))

        assert payment.amount == Decimal("850.00")
        assert payment.method == "transferencia"
        assert payment.invoice_id == inv.id

        updated = session.get(Invoice, inv.id)
        assert updated.status == "paid"

    def test_partial_payment_marks_invoice_partial(self, session: Session, sample_lease):
        inv = self._create_invoice(session, sample_lease, Decimal("850.00"))

        PaymentService.register(session, inv.id, Decimal("400.00"), date(2024, 7, 1))

        updated = session.get(Invoice, inv.id)
        assert updated.status == "partial"

    def test_multiple_partial_payments_sum_to_paid(self, session: Session, sample_lease):
        inv = self._create_invoice(session, sample_lease, Decimal("850.00"))

        PaymentService.register(session, inv.id, Decimal("400.00"), date(2024, 7, 1))
        PaymentService.register(session, inv.id, Decimal("450.00"), date(2024, 7, 15))

        updated = session.get(Invoice, inv.id)
        assert updated.status == "paid"

    def test_invoice_not_found_raises(self, session: Session):
        from pytest import raises

        with raises(PaymentError):
            PaymentService.register(session, 999, Decimal("100"), date(2024, 7, 1))

    def test_zero_amount_raises(self, session: Session, sample_lease):
        inv = self._create_invoice(session, sample_lease, Decimal("100.00"))

        from pytest import raises

        with raises(PaymentError):
            PaymentService.register(session, inv.id, Decimal("0"), date(2024, 7, 1))

    def test_custom_method_and_notes(self, session: Session, sample_lease):
        inv = self._create_invoice(session, sample_lease, Decimal("500.00"))

        payment = PaymentService.register(
            session,
            inv.id,
            Decimal("500.00"),
            date(2024, 7, 1),
            method="bizum",
            notes="Pago completo por Bizum",
        )

        assert payment.method == "bizum"
        assert payment.notes == "Pago completo por Bizum"

        payments = session.exec(select(Payment).where(Payment.invoice_id == inv.id)).all()
        assert len(payments) == 1
