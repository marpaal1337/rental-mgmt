from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlmodel import Session

from app.models.invoice import Invoice, InvoiceLine
from app.models.lease import Lease
from app.models.owner import Owner
from app.models.property import Property
from app.services.expense_service import ExpenseService
from app.services.fiscal_service import FiscalError, FiscalService


def make_invoice(
    session: Session,
    lease: Lease,
    issue_date: date,
    base: Decimal,
    vat: Decimal = Decimal("0"),
    vat_rate: Decimal = Decimal("0"),
    withholding: Decimal = Decimal("0"),
    status: str = "issued",
    recipient_name: str = "Test Tenant",
    recipient_document_number: str = "22222222B",
) -> Invoice:
    invoice = Invoice(
        period=issue_date.strftime("%Y-%m"),
        lease_id=lease.id,
        issue_date=issue_date,
        status=status,
        total_base=base,
        total_vat=vat,
        total_irpf_withholding=withholding,
        total=base + vat - withholding,
        recipient_name=recipient_name,
        recipient_document_type="NIF",
        recipient_document_number=recipient_document_number,
    )
    session.add(invoice)
    session.flush()
    session.add(
        InvoiceLine(
            invoice_id=invoice.id,
            concept="Alquiler",
            base_amount=base,
            vat_rate=vat_rate,
            vat_amount=vat,
            irpf_rate=Decimal("0"),
            irpf_withholding=withholding,
        )
    )
    session.flush()
    return invoice


class TestVatReport:
    def test_empty_report(self, session: Session):
        report = FiscalService.vat_report(session, 2024, 1)

        assert report["label"] == "1T 2024"
        assert report["date_from"] == "2024-01-01"
        assert report["date_to"] == "2024-03-31"
        assert report["output"] == []
        assert report["input"] == []
        assert report["exempt"]["base"] == "0.00"
        assert report["totals"]["vat_due"] == "0.00"

    def test_output_grouped_by_rate_and_exempt(
        self, session: Session, sample_lease: Lease
    ):
        make_invoice(
            session, sample_lease, date(2024, 1, 15), Decimal("1000"),
            Decimal("210"), Decimal("21"),
        )
        make_invoice(
            session, sample_lease, date(2024, 3, 15), Decimal("500"),
            Decimal("105"), Decimal("21"),
        )
        make_invoice(
            session, sample_lease, date(2024, 2, 1), Decimal("800"),
            Decimal("0"), Decimal("0"),
        )

        report = FiscalService.vat_report(session, 2024, 1)

        assert report["output"] == [
            {"vat_rate": "21.00", "base": "1500.00", "vat": "315.00"}
        ]
        assert report["exempt"]["base"] == "800.00"
        assert report["totals"]["output_base"] == "1500.00"
        assert report["totals"]["output_vat"] == "315.00"
        assert report["totals"]["vat_due"] == "315.00"

    def test_filters_by_quarter_status_and_soft_delete(
        self, session: Session, sample_lease: Lease
    ):
        make_invoice(
            session, sample_lease, date(2024, 4, 1), Decimal("1000"),
            Decimal("210"), Decimal("21"),
        )
        make_invoice(
            session, sample_lease, date(2024, 2, 1), Decimal("200"),
            Decimal("42"), Decimal("21"), status="draft",
        )
        deleted = make_invoice(
            session, sample_lease, date(2024, 3, 2), Decimal("300"),
            Decimal("63"), Decimal("21"),
        )
        deleted.deleted_at = datetime.now(UTC)
        session.flush()

        report = FiscalService.vat_report(session, 2024, 1)

        assert report["output"] == []
        assert report["totals"]["output_vat"] == "0.00"

    def test_rectification_nets_negative(self, session: Session, sample_lease: Lease):
        make_invoice(
            session, sample_lease, date(2024, 1, 15), Decimal("1000"),
            Decimal("210"), Decimal("21"),
        )
        make_invoice(
            session, sample_lease, date(2024, 2, 15), Decimal("-1000"),
            Decimal("-210"), Decimal("21"),
        )

        report = FiscalService.vat_report(session, 2024, 1)

        assert report["output"] == []
        assert report["exempt"]["base"] == "0.00"
        assert report["totals"]["vat_due"] == "0.00"

    def test_input_vat_from_deductible_expenses(
        self, session: Session, sample_lease: Lease
    ):
        prop = session.get(Property, sample_lease.unit.property_id)
        ExpenseService.register(
            session, prop.id, "supplies", Decimal("121.00"), date(2024, 2, 1),
            vat_rate=Decimal("21"),
        )
        ExpenseService.register(
            session, prop.id, "repairs", Decimal("110.00"), date(2024, 2, 2),
            vat_rate=Decimal("10"),
        )
        ExpenseService.register(
            session, prop.id, "insurance", Decimal("121.00"), date(2024, 2, 3),
            deductible=False, vat_rate=Decimal("21"),
        )
        ExpenseService.register(
            session, prop.id, "community", Decimal("121.00"), date(2024, 5, 1),
            vat_rate=Decimal("21"),
        )
        ExpenseService.register(
            session, prop.id, "other", Decimal("50.00"), date(2024, 2, 4),
        )

        report = FiscalService.vat_report(session, 2024, 1)

        assert report["input"] == [
            {"vat_rate": "10.00", "base": "100.00", "vat": "10.00"},
            {"vat_rate": "21.00", "base": "100.00", "vat": "21.00"},
        ]
        assert report["totals"]["input_vat"] == "31.00"
        assert report["totals"]["vat_due"] == "-31.00"

    def test_invalid_year_and_quarter(self, session: Session):
        with pytest.raises(FiscalError):
            FiscalService.vat_report(session, 1999, 1)
        with pytest.raises(FiscalError):
            FiscalService.vat_report(session, 2024, 5)


class TestWithholdingsReport:
    def test_empty_report(self, session: Session):
        report = FiscalService.withholdings_report(session, 2024)

        assert report["year"] == 2024
        assert report["rows"] == []
        assert report["totals"]["withholding"] == "0.00"

    def test_groups_by_recipient(self, session: Session, sample_lease: Lease):
        make_invoice(
            session, sample_lease, date(2024, 1, 15), Decimal("1000"),
            Decimal("0"), withholding=Decimal("190"),
            recipient_name="Ana", recipient_document_number="11111111A",
        )
        make_invoice(
            session, sample_lease, date(2024, 2, 15), Decimal("1000"),
            Decimal("0"), withholding=Decimal("190"),
            recipient_name="Ana", recipient_document_number="11111111A",
        )
        make_invoice(
            session, sample_lease, date(2024, 3, 15), Decimal("500"),
            Decimal("0"), withholding=Decimal("95"),
            recipient_name="Bruno", recipient_document_number="22222222B",
        )
        make_invoice(
            session, sample_lease, date(2024, 4, 15), Decimal("1000"),
            Decimal("0"), withholding=Decimal("0"),
            recipient_name="Carlos", recipient_document_number="33333333C",
        )
        make_invoice(
            session, sample_lease, date(2025, 1, 15), Decimal("1000"),
            Decimal("0"), withholding=Decimal("190"),
            recipient_name="Ana", recipient_document_number="11111111A",
        )

        report = FiscalService.withholdings_report(session, 2024)

        assert len(report["rows"]) == 2
        assert report["rows"][0]["recipient_name"] == "Ana"
        assert report["rows"][0]["invoice_count"] == 2
        assert report["rows"][0]["base"] == "2000.00"
        assert report["rows"][0]["withholding"] == "380.00"
        assert report["rows"][1]["recipient_name"] == "Bruno"
        assert report["totals"]["base"] == "2500.00"
        assert report["totals"]["withholding"] == "475.00"

    def test_invalid_year(self, session: Session):
        with pytest.raises(FiscalError):
            FiscalService.withholdings_report(session, 1999)


class TestIncomeReport:
    def test_empty_report(self, session: Session):
        report = FiscalService.income_report(session, 2024)

        assert report["rows"] == []
        assert report["totals"]["net_income"] == "0.00"

    def test_income_and_expenses_by_property(
        self, session: Session, sample_lease: Lease
    ):
        prop = session.get(Property, sample_lease.unit.property_id)
        make_invoice(
            session, sample_lease, date(2024, 6, 1), Decimal("1000"),
            Decimal("0"), Decimal("0"),
        )
        make_invoice(
            session, sample_lease, date(2024, 7, 1), Decimal("1000"),
            Decimal("0"), Decimal("0"), status="draft",
        )
        ExpenseService.register(
            session, prop.id, "community", Decimal("100.00"), date(2024, 6, 1),
        )
        ExpenseService.register(
            session, prop.id, "community", Decimal("50.00"), date(2024, 7, 1),
        )
        ExpenseService.register(
            session, prop.id, "repairs", Decimal("80.00"), date(2024, 6, 15),
            deductible=False,
        )

        report = FiscalService.income_report(session, 2024)

        assert len(report["rows"]) == 1
        row = report["rows"][0]
        assert row["property_id"] == prop.id
        assert row["invoice_count"] == 1
        assert row["gross_income"] == "1000.00"
        assert row["deductible_expenses"] == "150.00"
        assert row["non_deductible_expenses"] == "80.00"
        assert row["net_income"] == "850.00"
        assert row["by_category"] == {"community": "150.00"}
        assert report["totals"]["gross_income"] == "1000.00"
        assert report["totals"]["net_income"] == "850.00"

    def test_property_without_activity_is_omitted(
        self, session: Session, sample_lease: Lease
    ):
        owner = session.get(Owner, sample_lease.owner_id)
        idle = Property(
            name="Idle Property",
            address="Calle Nada 1",
            city="Madrid",
            province="Madrid",
            zip_code="28001",
            owner_id=owner.id,
        )
        session.add(idle)
        session.flush()

        make_invoice(
            session, sample_lease, date(2024, 6, 1), Decimal("1000"),
            Decimal("0"), Decimal("0"),
        )

        report = FiscalService.income_report(session, 2024)

        assert [row["property_name"] for row in report["rows"]] == [
            "Test Property"
        ]

    def test_invalid_year(self, session: Session):
        with pytest.raises(FiscalError):
            FiscalService.income_report(session, 1999)
