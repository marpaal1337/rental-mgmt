from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any, Optional

from sqlmodel import Session, func, select

from app.models.invoice import Invoice
from app.models.payment import Payment


class PaymentError(Exception):
    """Raised when payment registration fails."""


class PaymentNotFoundError(PaymentError):
    """Raised when the payment does not exist or was deleted."""


class PaymentService:
    @staticmethod
    def _paid_total(
        session: Session,
        invoice_id: int,
        *,
        exclude_payment_id: int | None = None,
    ) -> Decimal:
        query = select(func.coalesce(func.sum(Payment.amount), Decimal("0"))).where(
            Payment.invoice_id == invoice_id,
            Payment.deleted_at.is_(None),
        )
        if exclude_payment_id is not None:
            query = query.where(Payment.id != exclude_payment_id)
        result = session.exec(query).one()
        return result if result is not None else Decimal("0")

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

        if invoice.status == "cancelled":
            raise PaymentError(f"Invoice {invoice_id} is cancelled")

        if invoice.total <= Decimal("0"):
            raise PaymentError(f"Invoice {invoice_id} has no payable amount")

        paid_before = PaymentService._paid_total(session, invoice_id)
        if paid_before + amount > invoice.total:
            outstanding = invoice.total - paid_before
            raise PaymentError(
                f"Payment of {amount} exceeds outstanding balance {outstanding} "
                f"of invoice {invoice_id}"
            )

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

        return payment

    @staticmethod
    def update(session: Session, payment_id: int, **fields: Any) -> Payment:
        payment = session.get(Payment, payment_id)
        if payment is None or payment.deleted_at is not None:
            raise PaymentNotFoundError(f"Payment {payment_id} not found")

        invoice = session.get(Invoice, payment.invoice_id)
        if invoice is None or invoice.deleted_at is not None:
            raise PaymentError(f"Invoice {payment.invoice_id} not found")

        amount = fields.get("amount")
        if amount is not None:
            if amount <= Decimal("0"):
                raise PaymentError("Amount must be positive")
            paid_others = PaymentService._paid_total(
                session, invoice.id, exclude_payment_id=payment.id
            )
            if paid_others + amount > invoice.total:
                outstanding = invoice.total - paid_others
                raise PaymentError(
                    f"Payment of {amount} exceeds outstanding balance {outstanding} "
                    f"of invoice {invoice.id}"
                )

        for field, value in fields.items():
            setattr(payment, field, value)
        payment.updated_at = datetime.now(UTC)
        session.add(payment)
        session.flush()

        PaymentService._update_invoice_status(session, invoice)
        return payment

    @staticmethod
    def delete(session: Session, payment_id: int) -> None:
        payment = session.get(Payment, payment_id)
        if payment is None or payment.deleted_at is not None:
            raise PaymentNotFoundError(f"Payment {payment_id} not found")

        payment.deleted_at = datetime.now(UTC)
        payment.updated_at = datetime.now(UTC)
        session.add(payment)
        session.flush()

        invoice = session.get(Invoice, payment.invoice_id)
        if invoice is not None and invoice.deleted_at is None:
            PaymentService._update_invoice_status(session, invoice)

    @staticmethod
    def _update_invoice_status(session: Session, invoice: Invoice) -> None:
        if invoice.status == "cancelled":
            return

        if invoice.total <= Decimal("0"):
            if invoice.status in ("partial", "paid"):
                invoice.status = "issued"
                invoice.updated_at = datetime.now(UTC)
                session.add(invoice)
            return

        paid = PaymentService._paid_total(session, invoice.id)

        if paid >= invoice.total:
            invoice.status = "paid"
        elif paid > Decimal("0"):
            invoice.status = "partial"
        elif invoice.status in ("partial", "paid"):
            invoice.status = "issued"

        invoice.updated_at = datetime.now(UTC)
        session.add(invoice)
