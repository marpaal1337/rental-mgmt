import logging
import re
from datetime import date
from decimal import Decimal
from typing import List

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.models.invoice import Invoice, InvoiceLine
from app.models.lease import Lease, TaxProfile
from app.services.lease_service import LeaseService, NoActiveRentError

logger = logging.getLogger(__name__)

PERIOD_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class InvoiceGenerationError(Exception):
    """Raised when invoice generation fails."""


class InvoiceService:
    @staticmethod
    def validate_period(period: str) -> date:
        if not isinstance(period, str) or not PERIOD_PATTERN.match(period):
            raise InvoiceGenerationError(
                f"Invalid period '{period}'. Expected format YYYY-MM"
            )
        year, month = (int(part) for part in period.split("-"))
        return date(year, month, 1)

    @staticmethod
    def generate_monthly(session: Session, period: str) -> List[Invoice]:
        target_date = InvoiceService.validate_period(period)

        active_leases = session.exec(
            select(Lease)
            .options(selectinload(Lease.unit))
            .where(
                Lease.is_active,
                Lease.deleted_at.is_(None),
            )
        ).all()

        existing_lease_ids = set(
            session.exec(
                select(Invoice.lease_id).where(
                    Invoice.period == period,
                    Invoice.deleted_at.is_(None),
                )
            ).all()
        )
        tax_profiles = {
            tp.lease_id: tp
            for tp in session.exec(
                select(TaxProfile).where(TaxProfile.deleted_at.is_(None))
            ).all()
        }

        invoices: List[Invoice] = []
        skipped: list[str] = []
        for lease in active_leases:
            if lease.id in existing_lease_ids:
                continue

            tax_profile = tax_profiles.get(lease.id)
            if tax_profile is None:
                skipped.append(f"lease {lease.id}: no TaxProfile")
                continue

            try:
                rent = LeaseService.get_active_rent(session, lease.id, target_date)
            except NoActiveRentError:
                skipped.append(f"lease {lease.id}: no active rent condition")
                continue

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
                status="issued",
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

        if skipped:
            logger.warning(
                "Skipped %d leases for period %s: %s",
                len(skipped),
                period,
                "; ".join(skipped),
            )

        return invoices
