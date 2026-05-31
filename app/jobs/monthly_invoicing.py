from datetime import date
from typing import Optional

from sqlmodel import Session

from app.database import engine as _engine
from app.models.event_log import EventLog
from app.models.invoice import Invoice
from app.services.invoice_service import InvoiceGenerationError, InvoiceService


def generate_monthly_invoices(
    period: Optional[str] = None,
    session: Optional[Session] = None,
) -> list[Invoice]:
    if period is None:
        today = date.today()
        period = f"{today.year}-{today.month:02d}"

    own_session = session is None
    if session is None:
        session = Session(_engine)

    try:
        invoices = InvoiceService.generate_monthly(session, period)
        log = EventLog(
            event_type="invoice_generation",
            description=f"Generated {len(invoices)} invoices for {period}",
            details=f"period={period}, count={len(invoices)}",
            level="info",
        )
        session.add(log)
        session.commit()
        return invoices
    except InvoiceGenerationError as e:
        log = EventLog(
            event_type="invoice_generation",
            description=f"Failed to generate invoices for {period}",
            details=str(e),
            level="error",
        )
        session.add(log)
        session.commit()
        raise
    finally:
        if own_session:
            session.close()
