from datetime import date
from decimal import Decimal
from typing import Optional

from sqlmodel import Session, func, select

from app.models.invoice import Invoice
from app.models.payment import Payment


class PaymentError(Exception):
    """Raised when payment registration fails."""


class PaymentService:
    @staticmethod
    def register(
        session: Session,
        invoice_id: int,
        amount: Decimal,
        payment_date: date,
        method: str = "transferencia",
        notes: Optional[str] = None,
    ) -> Payment:
        invoice = session.get(Invoice, invoice_id)
        if invoice is None or invoice.deleted_at is not None:
            raise PaymentError(f"Invoice {invoice_id} not found")

        if amount <= Decimal("0"):
            raise PaymentError("Amount must be positive")

        payment = Payment(
            invoice_id=invoice_id,
            amount=amount,
            payment_date=payment_date,
            method=method,
            notes=notes,
        )
        session.add(payment)
        session.flush()

        PaymentService._update_invoice_status(session, invoice)

        session.commit()
        return payment

    @staticmethod
    def _update_invoice_status(session: Session, invoice: Invoice) -> None:
        result = session.exec(
            select(func.sum(Payment.amount)).where(
                Payment.invoice_id == invoice.id,
                Payment.deleted_at.is_(None),
            )
        ).one()

        paid = result if result is not None else Decimal("0")

        if paid >= invoice.total:
            invoice.status = "paid"
        elif paid > Decimal("0"):
            invoice.status = "partial"
        else:
            invoice.status = "draft"

        session.add(invoice)
