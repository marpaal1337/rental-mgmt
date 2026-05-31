from datetime import date
from decimal import Decimal
from pathlib import Path

from sqlmodel import Session

from app.models.invoice import Invoice, InvoiceLine
from app.models.lease import RentCondition, TaxProfile
from app.services.pdf_service import PDFService


class TestRenderInvoice:
    def test_pdf_generated_for_vivienda(self, session: Session, sample_lease, tmp_path: Path):
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
            concept="Alquiler 2024-06 - Test Unit",
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
        assert path.suffix == ".pdf"
        assert "2024" in str(path)
        assert "06" in str(path)
        assert path.stat().st_size > 1000

    def test_pdf_generated_for_local(self, session: Session, sample_lease, tmp_path: Path):
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
        session.flush()

        inv = Invoice(
            period="2024-06",
            lease_id=sample_lease.id,
            issue_date=date(2024, 6, 1),
            status="draft",
            total_base=Decimal("1500.00"),
            total_vat=Decimal("315.00"),
            total_irpf_withholding=Decimal("285.00"),
            total=Decimal("1530.00"),
        )
        session.add(inv)
        session.flush()

        line = InvoiceLine(
            invoice_id=inv.id,
            concept="Alquiler 2024-06 - Test Unit",
            base_amount=Decimal("1500.00"),
            vat_rate=Decimal("21.00"),
            vat_amount=Decimal("315.00"),
            irpf_rate=Decimal("19.00"),
            irpf_withholding=Decimal("285.00"),
        )
        session.add(line)
        session.commit()

        path = PDFService.render_invoice(session, inv.id)

        assert path.exists()
        assert path.stat().st_size > 1000

    def test_invoice_not_found_raises(self, session: Session):
        from pytest import raises

        from app.services.pdf_service import PDFGenerationError

        with raises(PDFGenerationError):
            PDFService.render_invoice(session, 999)
