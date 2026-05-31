from datetime import date
from decimal import Decimal

from sqlmodel import Session

from app.models.bank import BankMovement, Reconciliation
from app.models.invoice import Invoice, InvoiceLine
from app.models.lease import RentCondition, TaxProfile
from app.models.payment import Payment
from app.services.bank_adapter import BankRow, GenericBankAdapter
from app.services.reconciliation_service import (
    ReconciliationError,
    ReconciliationService,
)


class _TestAdapter(GenericBankAdapter):
    """Adapter that returns pre-built rows for testing."""

    def __init__(self, rows: list[BankRow]) -> None:
        self._rows = rows
        super().__init__()

    def parse(self, file_path: str) -> list[BankRow]:
        return self._rows


class TestImportCSV:
    def test_import_creates_movements(self, session: Session):
        rows = [
            BankRow(
                entry_date=date(2024, 7, 1),
                concept="Transferencia inquilino",
                amount=Decimal("850.00"),
            ),
            BankRow(
                entry_date=date(2024, 7, 15),
                concept="Pago comunidad",
                amount=Decimal("-85.00"),
            ),
        ]
        adapter = _TestAdapter(rows)

        movements = ReconciliationService.import_csv(session, "/fake/path.csv", adapter)

        assert len(movements) == 2
        assert movements[0].amount == Decimal("850.00")
        assert movements[0].status == "unmatched"
        assert movements[1].concept == "Pago comunidad"

    def test_import_with_iban(self, session: Session):
        rows = [
            BankRow(
                entry_date=date(2024, 7, 1),
                concept="Transferencia",
                amount=Decimal("850.00"),
                iban_origin="ES9121000418450200051332",
                reference="REF001",
            ),
        ]
        adapter = _TestAdapter(rows)

        movements = ReconciliationService.import_csv(session, "/fake/path.csv", adapter)

        assert movements[0].iban_origin == "ES9121000418450200051332"
        assert movements[0].reference == "REF001"


class TestProposeMatches:
    def _create_payment(
        self, session: Session, sample_lease, amount: Decimal, when: date
    ) -> Payment:
        rc = RentCondition(
            lease_id=sample_lease.id,
            start_date=date(2024, 1, 1),
            monthly_rent=amount,
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
            period="2024-07",
            lease_id=sample_lease.id,
            issue_date=date(2024, 7, 1),
            status="draft",
            total_base=amount,
            total_vat=Decimal("0"),
            total_irpf_withholding=Decimal("0"),
            total=amount,
        )
        session.add(inv)
        session.flush()

        line = InvoiceLine(
            invoice_id=inv.id,
            concept="Alquiler 2024-07",
            base_amount=amount,
            vat_rate=Decimal("0"),
            vat_amount=Decimal("0"),
            irpf_rate=Decimal("0"),
            irpf_withholding=Decimal("0"),
        )
        session.add(line)
        session.flush()

        payment = Payment(
            invoice_id=inv.id,
            amount=amount,
            payment_date=when,
            method="transferencia",
        )
        session.add(payment)
        session.commit()
        return payment

    def test_exact_match_found(self, session: Session, sample_lease):
        payment = self._create_payment(session, sample_lease, Decimal("850.00"), date(2024, 7, 1))

        movement = BankMovement(
            entry_date=date(2024, 7, 1),
            amount=Decimal("850.00"),
            concept="Transferencia nomina inquilino",
            iban_origin="ES9121000418450200051332",
        )
        session.add(movement)
        session.commit()

        recs = ReconciliationService.propose_matches(session, movement.id)

        assert len(recs) >= 1
        best = max(recs, key=lambda r: r.score)
        assert best.payment_id == payment.id
        assert best.score > Decimal("0.5")

    def test_no_match_different_amount(self, session: Session, sample_lease):
        self._create_payment(session, sample_lease, Decimal("850.00"), date(2024, 7, 1))

        movement = BankMovement(
            entry_date=date(2024, 8, 1),
            amount=Decimal("999.99"),
            concept="Otro concepto",
        )
        session.add(movement)
        session.commit()

        recs = ReconciliationService.propose_matches(session, movement.id)

        assert len(recs) == 0

    def test_movement_not_found_raises(self, session: Session):
        from pytest import raises

        with raises(ReconciliationError, match="BankMovement 999 not found"):
            ReconciliationService.propose_matches(session, 999)

    def test_movement_already_confirmed_raises(self, session: Session):
        movement = BankMovement(
            entry_date=date(2024, 7, 1),
            amount=Decimal("100.00"),
            concept="Test",
            status="confirmed",
        )
        session.add(movement)
        session.commit()

        from pytest import raises

        with raises(ReconciliationError, match="already confirmed"):
            ReconciliationService.propose_matches(session, movement.id)


class TestConfirmMatch:
    def test_confirm_updates_status(self, session: Session, sample_lease):
        payment = Payment(
            invoice_id=0,
            amount=Decimal("100.00"),
            payment_date=date(2024, 7, 1),
            method="transferencia",
        )

        # Create a minimal invoice
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
            status="proposed",
        )
        session.add(movement)
        session.commit()

        rec = Reconciliation(
            bank_movement_id=movement.id,
            payment_id=payment.id,
            score=Decimal("0.9"),
        )
        session.add(rec)
        session.commit()

        confirmed = ReconciliationService.confirm_match(session, rec.id)

        assert confirmed.confirmed_at is not None
        moved = session.get(BankMovement, movement.id)
        assert moved.status == "confirmed"

    def test_not_found_raises(self, session: Session):
        from pytest import raises

        with raises(ReconciliationError, match="Reconciliation 999 not found"):
            ReconciliationService.confirm_match(session, 999)


class TestListUnmatched:
    def test_list_unmatched(self, session: Session):
        m1 = BankMovement(
            entry_date=date(2024, 7, 1),
            amount=Decimal("100.00"),
            concept="A",
            status="unmatched",
        )
        m2 = BankMovement(
            entry_date=date(2024, 7, 2),
            amount=Decimal("200.00"),
            concept="B",
            status="confirmed",
        )
        m3 = BankMovement(
            entry_date=date(2024, 7, 3),
            amount=Decimal("300.00"),
            concept="C",
            status="unmatched",
        )
        session.add(m1)
        session.add(m2)
        session.add(m3)
        session.commit()

        unmatched = ReconciliationService.list_unmatched(session)
        assert len(unmatched) == 2
        assert all(m.status == "unmatched" for m in unmatched)
