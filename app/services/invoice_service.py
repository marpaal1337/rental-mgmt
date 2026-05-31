from datetime import date
from decimal import Decimal
from typing import List

from sqlmodel import Session, select

from app.models.invoice import Invoice, InvoiceLine
from app.models.lease import Lease, TaxProfile
from app.services.lease_service import LeaseService


class InvoiceGenerationError(Exception):
    """Raised when invoice generation fails."""


class InvoiceService:
    @staticmethod
    def generate_monthly(session: Session, period: str) -> List[Invoice]:
        year_str, month_str = period.split("-")
        year = int(year_str)
        month = int(month_str)
        target_date = date(year, month, 1)

        active_leases = session.exec(
            select(Lease).where(
                Lease.is_active,
                Lease.deleted_at.is_(None),
            )
        ).all()

        invoices: List[Invoice] = []
        for lease in active_leases:
            existing = session.exec(
                select(Invoice).where(
                    Invoice.lease_id == lease.id,
                    Invoice.period == period,
                    Invoice.deleted_at.is_(None),
                )
            ).first()
            if existing is not None:
                continue

            rent = LeaseService.get_active_rent(session, lease.id, target_date)

            tax_profile = session.exec(
                select(TaxProfile).where(
                    TaxProfile.lease_id == lease.id,
                    TaxProfile.deleted_at.is_(None),
                )
            ).first()
            if tax_profile is None:
                raise InvoiceGenerationError(f"Lease {lease.id} has no TaxProfile")

            vat_amount = Decimal("0")
            irpf_withholding = Decimal("0")

            if not tax_profile.vat_exempt:
                vat_amount = (rent * tax_profile.vat_rate / Decimal("100")).quantize(
                    Decimal("0.01")
                )

            if tax_profile.withholding_applies:
                irpf_withholding = (rent * tax_profile.irpf_rate / Decimal("100")).quantize(
                    Decimal("0.01")
                )

            total = rent + vat_amount - irpf_withholding

            invoice = Invoice(
                period=period,
                lease_id=lease.id,
                issue_date=date.today(),
                status="draft",
                total_base=rent,
                total_vat=vat_amount,
                total_irpf_withholding=irpf_withholding,
                total=total,
            )
            session.add(invoice)
            session.flush()

            unit_name = lease.unit.name if lease.unit else f"Lease #{lease.id}"
            line = InvoiceLine(
                invoice_id=invoice.id,
                concept=f"Alquiler {period} - {unit_name}",
                base_amount=rent,
                vat_rate=tax_profile.vat_rate,
                vat_amount=vat_amount,
                irpf_rate=tax_profile.irpf_rate,
                irpf_withholding=irpf_withholding,
            )
            session.add(line)

            invoices.append(invoice)

        session.commit()
        return invoices
