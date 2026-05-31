from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from sqlmodel import Session, func, select

from app.database import engine as _engine
from app.models.event_log import EventLog
from app.models.invoice import Invoice
from app.models.payment import Payment


def detect_overdue_invoices(
    session: Optional[Session] = None,
) -> list[dict]:
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)

    own_session = session is None
    if session is None:
        session = Session(_engine)

    try:
        invoices = session.exec(
            select(Invoice).where(
                Invoice.deleted_at.is_(None),
                Invoice.status.in_(["draft", "partial"]),
                Invoice.issue_date <= thirty_days_ago,
            )
        ).all()

        overdue: list[dict] = []
        for inv in invoices:
            result = session.exec(
                select(func.coalesce(func.sum(Payment.amount), Decimal("0"))).where(
                    Payment.invoice_id == inv.id
                )
            ).one()
            paid = result if result is not None else Decimal("0")

            overdue.append(
                {
                    "invoice_id": inv.id,
                    "lease_id": inv.lease_id,
                    "period": inv.period,
                    "total": str(inv.total),
                    "paid": str(paid),
                    "days_overdue": (today - inv.issue_date).days,
                }
            )

        if overdue:
            log = EventLog(
                event_type="overdue_detection",
                description=f"Detected {len(overdue)} overdue invoices",
                details=f"count={len(overdue)}, date={today.isoformat()}",
                level="warning",
            )
            session.add(log)
            session.commit()

        return overdue
    finally:
        if own_session:
            session.close()
