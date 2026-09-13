from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.config import API_KEY
from app.models.bank import BankMovement, Reconciliation
from app.models.invoice import Invoice
from app.models.lease import Lease, RentCondition, TaxProfile
from app.models.payment import Payment
from app.services.bank_adapter import BankImportError, GenericBankAdapter
from app.services.index_update_service import IndexUpdateError, IndexUpdateService
from app.services.invoice_service import InvoiceService
from app.services.payment_service import (
    PaymentError,
    PaymentNotFoundError,
    PaymentService,
)
from app.services.reconciliation_service import (
    ReconciliationError,
    ReconciliationService,
)

HEADERS = {"X-API-Key": API_KEY}


def _add_rent_and_tax(session: Session, lease: Lease, rent: Decimal) -> None:
    session.add(
        RentCondition(
            lease_id=lease.id,
            start_date=date(2024, 1, 1),
            monthly_rent=rent,
        )
    )
    session.add(
        TaxProfile(
            lease_id=lease.id,
            vat_rate=Decimal("0"),
            irpf_rate=Decimal("0"),
            vat_exempt=True,
            withholding_applies=False,
        )
    )
    session.commit()


def _create_invoice(
    session: Session,
    lease: Lease,
    total: Decimal,
    *,
    period: str = "2024-06",
    status: str = "issued",
) -> Invoice:
    invoice = Invoice(
        period=period,
        lease_id=lease.id,
        issue_date=date(2024, 6, 1),
        status=status,
        total_base=total,
        total_vat=Decimal("0"),
        total_irpf_withholding=Decimal("0"),
        total=total,
    )
    session.add(invoice)
    session.commit()
    session.refresh(invoice)
    return invoice


class TestPaymentLifecycle:
    def test_delete_payment_recomputes_invoice_status(self, session, sample_lease):
        invoice = _create_invoice(session, sample_lease, Decimal("850.00"))
        payment = PaymentService.register(
            session, invoice.id, Decimal("850.00"), date(2024, 7, 1)
        )
        session.commit()
        assert session.get(Invoice, invoice.id).status == "paid"

        PaymentService.delete(session, payment.id)
        session.commit()

        assert session.get(Invoice, invoice.id).status == "issued"

    def test_update_payment_amount_recomputes_status(self, session, sample_lease):
        invoice = _create_invoice(session, sample_lease, Decimal("850.00"))
        payment = PaymentService.register(
            session, invoice.id, Decimal("400.00"), date(2024, 7, 1)
        )
        session.commit()
        assert session.get(Invoice, invoice.id).status == "partial"

        PaymentService.update(session, payment.id, amount=Decimal("850.00"))
        session.commit()

        assert session.get(Invoice, invoice.id).status == "paid"

    def test_overpayment_rejected(self, session, sample_lease):
        invoice = _create_invoice(session, sample_lease, Decimal("850.00"))

        with pytest.raises(PaymentError, match="exceeds outstanding balance"):
            PaymentService.register(
                session, invoice.id, Decimal("900.00"), date(2024, 7, 1)
            )

    def test_overpayment_via_update_rejected(self, session, sample_lease):
        invoice = _create_invoice(session, sample_lease, Decimal("850.00"))
        payment = PaymentService.register(
            session, invoice.id, Decimal("400.00"), date(2024, 7, 1)
        )
        session.commit()

        with pytest.raises(PaymentError, match="exceeds outstanding balance"):
            PaymentService.update(session, payment.id, amount=Decimal("900.00"))

    def test_delete_missing_payment_raises(self, session):
        with pytest.raises(PaymentNotFoundError):
            PaymentService.delete(session, 999)

    def test_update_missing_payment_raises(self, session):
        with pytest.raises(PaymentNotFoundError):
            PaymentService.update(session, 999, amount=Decimal("10"))


class TestReconciliationCandidates:
    def _create_payment(
        self, session: Session, lease: Lease, amount: Decimal, period: str = "2024-06"
    ):
        invoice = _create_invoice(session, lease, amount, period=period)
        payment = Payment(
            invoice_id=invoice.id,
            amount=amount,
            payment_date=date(2024, 7, 1),
            method="transferencia",
        )
        session.add(payment)
        session.commit()
        return payment

    def test_multiple_candidates_do_not_crash(self, session, sample_lease):
        first = self._create_payment(session, sample_lease, Decimal("850.00"), "2024-06")
        second = self._create_payment(
            session, sample_lease, Decimal("850.00"), "2024-07"
        )

        movement = BankMovement(
            entry_date=date(2024, 7, 1),
            amount=Decimal("850.00"),
            concept="Transferencia alquiler",
        )
        session.add(movement)
        session.commit()

        recs = ReconciliationService.propose_matches(session, movement.id)
        session.commit()

        assert len(recs) == 2
        assert {r.payment_id for r in recs} == {first.id, second.id}
        assert session.get(BankMovement, movement.id).status == "proposed"

    def test_confirm_removes_sibling_proposals(self, session, sample_lease):
        self._create_payment(session, sample_lease, Decimal("850.00"), "2024-06")
        self._create_payment(session, sample_lease, Decimal("850.00"), "2024-07")

        movement = BankMovement(
            entry_date=date(2024, 7, 1),
            amount=Decimal("850.00"),
            concept="Transferencia alquiler",
        )
        session.add(movement)
        session.commit()

        recs = ReconciliationService.propose_matches(session, movement.id)
        session.commit()

        ReconciliationService.confirm_match(session, recs[0].id)
        session.commit()

        remaining = session.exec(select(Reconciliation)).all()
        assert len(remaining) == 1
        assert remaining[0].id == recs[0].id
        assert remaining[0].confirmed_at is not None
        assert session.get(BankMovement, movement.id).status == "confirmed"

    def test_repropose_after_confirm_raises(self, session, sample_lease):
        self._create_payment(session, sample_lease, Decimal("850.00"))
        movement = BankMovement(
            entry_date=date(2024, 7, 1),
            amount=Decimal("850.00"),
            concept="Transferencia alquiler",
        )
        session.add(movement)
        session.commit()

        recs = ReconciliationService.propose_matches(session, movement.id)
        session.commit()
        ReconciliationService.confirm_match(session, recs[0].id)
        session.commit()

        with pytest.raises(ReconciliationError, match="already confirmed"):
            ReconciliationService.propose_matches(session, movement.id)


class TestBankAdapter:
    def _write(self, tmp_path: Path, content: str) -> str:
        path = tmp_path / "movements.csv"
        path.write_text(content, encoding="utf-8")
        return str(path)

    def test_spanish_amount_format(self, tmp_path):
        path = self._write(
            tmp_path,
            "fecha;concepto;importe\n01/07/2024;Transferencia;1.234,56\n",
        )
        rows = GenericBankAdapter(skip_rows=1).parse(path)
        assert rows[0].amount == Decimal("1234.56")

    def test_invalid_amount_raises(self, tmp_path):
        path = self._write(
            tmp_path,
            "fecha;concepto;importe\n01/07/2024;Transferencia;abc\n",
        )
        with pytest.raises(BankImportError, match="invalid amount"):
            GenericBankAdapter(skip_rows=1).parse(path)

    def test_invalid_date_raises(self, tmp_path):
        path = self._write(
            tmp_path,
            "fecha;concepto;importe\n32/13/2024;Transferencia;100,00\n",
        )
        with pytest.raises(BankImportError, match="invalid date"):
            GenericBankAdapter(skip_rows=1).parse(path)

    def test_import_dedupes_repeated_rows(self, session):
        import tempfile

        content = "fecha;concepto;importe\n01/07/2024;Transferencia;850,00\n"
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            first = ReconciliationService.import_csv(
                session, tmp_path, GenericBankAdapter(skip_rows=1)
            )
            second = ReconciliationService.import_csv(
                session, tmp_path, GenericBankAdapter(skip_rows=1)
            )
            session.commit()
        finally:
            Path(tmp_path).unlink(missing_ok=True)

        assert len(first) == 1
        assert second == []


class TestIndexUpdateValidation:
    def test_rate_out_of_range_raises(self, session, sample_lease):
        _add_rent_and_tax(session, sample_lease, Decimal("900.00"))

        with pytest.raises(IndexUpdateError, match="out of range"):
            IndexUpdateService.apply_index(
                session, sample_lease.id, Decimal("0.75"), date(2025, 1, 1)
            )

    def test_duplicate_application_date_raises(self, session, sample_lease):
        _add_rent_and_tax(session, sample_lease, Decimal("900.00"))

        IndexUpdateService.apply_index(
            session, sample_lease.id, Decimal("0.03"), date(2025, 1, 1)
        )
        session.commit()

        with pytest.raises(IndexUpdateError, match="already exists"):
            IndexUpdateService.apply_index(
                session, sample_lease.id, Decimal("0.03"), date(2025, 1, 1)
            )


class TestInvoiceGenerationRobustness:
    def test_skips_incomplete_lease_but_generates_others(self, session, sample_lease):
        from app.models.owner import Owner
        from app.models.property import Property
        from app.models.tenant import Tenant
        from app.models.unit import Unit

        _add_rent_and_tax(session, sample_lease, Decimal("850.00"))

        tenant = Tenant(
            name="Second Tenant",
            document_type="DNI",
            document_number="33333333C",
            email="second@test.com",
            phone="+34 600 000 003",
        )
        session.add(tenant)
        session.flush()
        property_ = session.get(Property, session.get(Unit, sample_lease.unit_id).property_id)
        unit = Unit(property_id=property_.id, name="Second Unit", unit_type="vivienda")
        session.add(unit)
        session.flush()
        owner = session.get(Owner, property_.owner_id)
        incomplete = Lease(
            unit_id=unit.id,
            tenant_id=tenant.id,
            owner_id=owner.id,
            start_date=date(2024, 1, 1),
            is_active=True,
        )
        session.add(incomplete)
        session.commit()

        invoices = InvoiceService.generate_monthly(session, "2024-06")

        assert len(invoices) == 1
        assert invoices[0].lease_id == sample_lease.id

    def test_existing_draft_invoice_blocks_duplicate(self, session, sample_lease):
        _add_rent_and_tax(session, sample_lease, Decimal("850.00"))
        _create_invoice(session, sample_lease, Decimal("850.00"), status="draft")

        invoices = InvoiceService.generate_monthly(session, "2024-06")

        assert invoices == []


class TestExpenseSummaryIncome:
    def test_draft_and_cancelled_invoices_not_counted(self, session, sample_lease):
        from app.models.property import Property
        from app.models.unit import Unit
        from app.services.expense_service import ExpenseService

        unit = session.get(Unit, sample_lease.unit_id)
        property_id = unit.property_id

        _create_invoice(
            session, sample_lease, Decimal("1000.00"), period="2024-06", status="draft"
        )
        summary = ExpenseService.summary(session, property_id, 2024)
        assert summary["total_income"] == Decimal("0")

        invoice = session.exec(select(Invoice)).first()
        invoice.status = "issued"
        session.add(invoice)
        session.commit()

        summary = ExpenseService.summary(session, property_id, 2024)
        assert summary["total_income"] == Decimal("1000.00")
        assert session.get(Property, property_id) is not None


class TestSpaFallback:
    def test_deep_link_serves_index_and_api_still_wins(self, client, tmp_path, monkeypatch):
        import app.main as main

        index = tmp_path / "index.html"
        index.write_text("<!doctype html><title>SPA</title>", encoding="utf-8")
        monkeypatch.setattr(main, "FRONTEND_DIR", tmp_path)

        resp = client.get("/owners")
        assert resp.status_code == 200
        assert "SPA" in resp.text

        resp = client.get("/api/owners", headers=HEADERS)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestPaymentApiLifecycle:
    def test_delete_payment_recomputes_status_via_api(self, client: TestClient, refs):
        lease = client.post(
            "/api/leases",
            json={**refs, "start_date": "2024-01-01"},
            headers=HEADERS,
        ).json()
        client.post(
            f"/api/leases/{lease['id']}/rent-conditions",
            json={"start_date": "2024-01-01", "monthly_rent": "850.00"},
            headers=HEADERS,
        )
        client.put(
            f"/api/leases/{lease['id']}/tax-profile",
            json={"vat_exempt": True, "withholding_applies": False},
            headers=HEADERS,
        )
        client.post(
            "/api/invoices/generate", json={"period": "2024-06"}, headers=HEADERS
        )
        invoice = client.get("/api/invoices", headers=HEADERS).json()[0]
        assert invoice["status"] == "issued"

        payment = client.post(
            "/api/payments",
            json={
                "invoice_id": invoice["id"],
                "amount": "850.00",
                "payment_date": "2024-07-01",
            },
            headers=HEADERS,
        ).json()
        invoice = client.get(f"/api/invoices/{invoice['id']}", headers=HEADERS).json()
        assert invoice["status"] == "paid"

        resp = client.delete(f"/api/payments/{payment['id']}", headers=HEADERS)
        assert resp.status_code == 200

        invoice = client.get(f"/api/invoices/{invoice['id']}", headers=HEADERS).json()
        assert invoice["status"] == "issued"

    def test_invalid_period_returns_422(self, client: TestClient):
        resp = client.post(
            "/api/invoices/generate", json={"period": "garbage"}, headers=HEADERS
        )
        assert resp.status_code == 422

    def test_overpayment_returns_400(self, client: TestClient, refs):
        lease = client.post(
            "/api/leases",
            json={**refs, "start_date": "2024-01-01"},
            headers=HEADERS,
        ).json()
        client.post(
            f"/api/leases/{lease['id']}/rent-conditions",
            json={"start_date": "2024-01-01", "monthly_rent": "850.00"},
            headers=HEADERS,
        )
        client.put(
            f"/api/leases/{lease['id']}/tax-profile",
            json={"vat_exempt": True, "withholding_applies": False},
            headers=HEADERS,
        )
        client.post(
            "/api/invoices/generate", json={"period": "2024-06"}, headers=HEADERS
        )
        invoice = client.get("/api/invoices", headers=HEADERS).json()[0]

        resp = client.post(
            "/api/payments",
            json={
                "invoice_id": invoice["id"],
                "amount": "900.00",
                "payment_date": "2024-07-01",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 400
