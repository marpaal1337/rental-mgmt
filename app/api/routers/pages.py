from datetime import date

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import selectinload
from sqlmodel import Session, func, select

from app.database import engine
from app.models.expense import Expense
from app.models.invoice import Invoice
from app.models.lease import Lease
from app.models.payment import Payment

router = APIRouter(prefix="/app")
templates = Jinja2Templates(directory="app/templates")


def get_session() -> Session:
    return Session(engine)


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    today = date.today()
    with get_session() as session:
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

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "stats": {
                "leases": leases,
                "invoices": invoices,
                "payments": payments,
                "expenses": expenses,
            }
        },
    )


@router.get("/leases", response_class=HTMLResponse)
def list_leases(request: Request):
    with get_session() as session:
        leases = session.exec(
            select(Lease)
            .options(
                selectinload(Lease.tenant),
                selectinload(Lease.owner),
                selectinload(Lease.unit),
            )
            .where(Lease.is_active, Lease.deleted_at.is_(None))
        ).all()
    return templates.TemplateResponse(request, "leases.html", {"leases": leases})


@router.get("/invoices", response_class=HTMLResponse)
def list_invoices(request: Request):
    today = date.today()
    with get_session() as session:
        invoices = session.exec(
            select(Invoice).where(
                Invoice.period == f"{today.year}-{today.month:02d}",
                Invoice.deleted_at.is_(None),
            )
        ).all()
    return templates.TemplateResponse(request, "invoices.html", {"invoices": invoices})


@router.get("/payments", response_class=HTMLResponse)
def list_payments(request: Request):
    today = date.today()
    with get_session() as session:
        payments = session.exec(
            select(Payment).where(
                func.strftime("%Y-%m", Payment.payment_date) == f"{today.year}-{today.month:02d}",
                Payment.deleted_at.is_(None),
            )
        ).all()
    return templates.TemplateResponse(request, "payments.html", {"payments": payments})


@router.get("/expenses", response_class=HTMLResponse)
def list_expenses(request: Request):
    today = date.today()
    with get_session() as session:
        expenses = session.exec(
            select(Expense).where(
                Expense.deleted_at.is_(None),
                Expense.expense_date >= date(today.year, 1, 1),
                Expense.expense_date <= date(today.year, 12, 31),
            )
        ).all()
    return templates.TemplateResponse(request, "expenses.html", {"expenses": expenses})
