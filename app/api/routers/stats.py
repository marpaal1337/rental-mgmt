from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlmodel import Session, select

from app.api.deps import verify_api_key
from app.database import get_session
from app.models.expense import Expense
from app.models.invoice import Invoice
from app.models.lease import Lease
from app.models.payment import Payment

router = APIRouter(
    prefix="/stats",
    tags=["stats"],
    dependencies=[Depends(verify_api_key)],
)


@router.get("")
def get_stats(session: Session = Depends(get_session)):
    today = date.today()

    leases = len(
        session.exec(select(Lease).where(Lease.is_active, Lease.deleted_at.is_(None))).all()
    )

    invoices = len(
        session.exec(
            select(Invoice).where(
                Invoice.period == f"{today.year}-{today.month:02d}",
                Invoice.deleted_at.is_(None),
            )
        ).all()
    )

    payments = len(
        session.exec(
            select(Payment).where(
                func.strftime("%Y-%m", Payment.payment_date)
                == f"{today.year}-{today.month:02d}",
                Payment.deleted_at.is_(None),
            )
        ).all()
    )

    expenses = len(
        session.exec(
            select(Expense).where(
                Expense.deleted_at.is_(None),
                Expense.expense_date >= date(today.year, 1, 1),
                Expense.expense_date <= date(today.year, 12, 31),
            )
        ).all()
    )

    return {
        "active_leases": leases,
        "month_invoices": invoices,
        "month_payments": payments,
        "year_expenses": expenses,
    }
