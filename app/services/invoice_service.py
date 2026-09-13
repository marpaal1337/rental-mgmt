import logging
import re
from datetime import date, timedelta
from decimal import Decimal
from typing import List

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.config import INVOICE_PAYMENT_TERMS_DAYS
from app.models.invoice import Invoice, InvoiceLine
from app.models.lease import Lease, TaxProfile
from app.services.invoice_numbering_service import InvoiceNumberingService
from app.services.lease_service import LeaseService, NoActiveRentError

logger = logging.getLogger(__name__)

PERIOD_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class InvoiceGenerationError(Exception):
    """Raised when invoice generation fails."""


class InvoiceRectificationError(Exception):
    """Raised when an invoice cannot be rectified."""


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
            .options(
                selectinload(Lease.unit),
                selectinload(Lease.owner),
                selectinload(Lease.tenant),
            )
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
                    Invoice.corrected_invoice_id.is_(None),
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

            issue_date = date.today()
            invoice = Invoice(
                period=period,
                lease_id=lease.id,
                issue_date=issue_date,
                due_date=issue_date + timedelta(days=INVOICE_PAYMENT_TERMS_DAYS),
                status="issued",
                total_base=rent,
                total_vat=vat_amount,
                total_irpf_withholding=irpf_withholding,
                total=total,
            )
            InvoiceService._freeze_party_data(invoice, lease)
            InvoiceNumberingService.assign_number(session, invoice)

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

    @staticmethod
    def rectify(session: Session, invoice_id: int, reason: str) -> Invoice:
        """Crea una factura rectificativa con importes negados y serie propia."""
        original = session.get(Invoice, invoice_id)
        if original is None or original.deleted_at is not None:
            raise InvoiceRectificationError(f"Invoice {invoice_id} not found")
        if original.corrected_invoice_id is not None:
            raise InvoiceRectificationError(
                f"Invoice {invoice_id} is a rectification and cannot be rectified"
            )
        if not reason or not reason.strip():
            raise InvoiceRectificationError("Rectification reason is required")

        existing = session.exec(
            select(Invoice).where(
                Invoice.corrected_invoice_id == invoice_id,
                Invoice.deleted_at.is_(None),
            )
        ).first()
        if existing is not None:
            raise InvoiceRectificationError(
                f"Invoice {invoice_id} is already rectified by {existing.number or existing.id}"
            )

        today = date.today()
        rectification = Invoice(
            period=original.period,
            lease_id=original.lease_id,
            issue_date=today,
            due_date=today,
            status="issued",
            total_base=-original.total_base,
            total_vat=-original.total_vat,
            total_irpf_withholding=-original.total_irpf_withholding,
            total=-original.total,
            corrected_invoice_id=original.id,
            rectification_reason=reason.strip(),
            issuer_name=original.issuer_name,
            issuer_document_type=original.issuer_document_type,
            issuer_document_number=original.issuer_document_number,
            issuer_address=original.issuer_address,
            recipient_name=original.recipient_name,
            recipient_document_type=original.recipient_document_type,
            recipient_document_number=original.recipient_document_number,
            recipient_address=original.recipient_address,
        )
        InvoiceNumberingService.assign_number(
            session,
            rectification,
            series=InvoiceNumberingService.RECTIFICATION_SERIES,
        )

        reference = original.number or f"Invoice #{original.id}"
        for line in original.lines:
            session.add(
                InvoiceLine(
                    invoice_id=rectification.id,
                    concept=f"Rectificación {reference}: {line.concept}",
                    base_amount=-line.base_amount,
                    vat_rate=line.vat_rate,
                    vat_amount=-line.vat_amount,
                    irpf_rate=line.irpf_rate,
                    irpf_withholding=-line.irpf_withholding,
                )
            )

        session.flush()
        return rectification

    @staticmethod
    def _freeze_party_data(invoice: Invoice, lease: Lease) -> None:
        owner = lease.owner
        if owner is not None:
            invoice.issuer_name = owner.name
            invoice.issuer_document_type = owner.document_type
            invoice.issuer_document_number = owner.document_number
            invoice.issuer_address = owner.address

        tenant = lease.tenant
        if tenant is not None:
            invoice.recipient_name = tenant.name
            invoice.recipient_document_type = tenant.document_type
            invoice.recipient_document_number = tenant.document_number
            invoice.recipient_address = tenant.address
