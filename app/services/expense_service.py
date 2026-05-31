from datetime import date
from decimal import Decimal
from typing import Optional

from sqlmodel import Session, select

from app.models.expense import EXPENSE_CATEGORIES, Expense
from app.models.invoice import Invoice
from app.models.lease import Lease
from app.models.property import Property
from app.models.unit import Unit


class ExpenseError(Exception):
    """Raised when expense operations fail."""


class ExpenseService:
    CATEGORIES = EXPENSE_CATEGORIES

    @staticmethod
    def register(
        session: Session,
        property_id: int,
        category: str,
        amount: Decimal,
        expense_date: date,
        lease_id: Optional[int] = None,
        deductible: bool = True,
        supplier: Optional[str] = None,
        invoice_number: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Expense:
        if session.get(Property, property_id) is None:
            raise ExpenseError(f"Property {property_id} not found")

        if category not in EXPENSE_CATEGORIES:
            raise ExpenseError(
                f"Invalid category '{category}'. Valid: {', '.join(EXPENSE_CATEGORIES)}"
            )

        if amount <= Decimal("0"):
            raise ExpenseError("Amount must be positive")

        if lease_id is not None and session.get(Lease, lease_id) is None:
            raise ExpenseError(f"Lease {lease_id} not found")

        expense = Expense(
            property_id=property_id,
            lease_id=lease_id,
            category=category,
            amount=amount,
            expense_date=expense_date,
            deductible=deductible,
            supplier=supplier,
            invoice_number=invoice_number,
            notes=notes,
        )
        session.add(expense)
        session.commit()
        return expense

    @staticmethod
    def list_by_property(
        session: Session,
        property_id: int,
        year: Optional[int] = None,
    ) -> list[Expense]:
        if session.get(Property, property_id) is None:
            raise ExpenseError(f"Property {property_id} not found")

        query = select(Expense).where(
            Expense.property_id == property_id,
            Expense.deleted_at.is_(None),
        )
        if year is not None:
            query = query.where(
                Expense.expense_date >= date(year, 1, 1),
                Expense.expense_date <= date(year, 12, 31),
            )
        query = query.order_by(Expense.expense_date.desc())
        return list(session.exec(query).all())

    @staticmethod
    def summary(
        session: Session,
        property_id: int,
        year: int,
    ) -> dict:
        if session.get(Property, property_id) is None:
            raise ExpenseError(f"Property {property_id} not found")

        expenses = ExpenseService.list_by_property(session, property_id, year)

        total_expenses = sum((e.amount for e in expenses), Decimal("0"))
        deductible_expenses = sum(
            (e.amount for e in expenses if e.deductible), Decimal("0")
        )
        by_category: dict[str, Decimal] = {}
        for e in expenses:
            by_category[e.category] = (
                by_category.get(e.category, Decimal("0")) + e.amount
            )

        units = session.exec(
            select(Unit).where(
                Unit.property_id == property_id,
                Unit.deleted_at.is_(None),
            )
        ).all()
        unit_ids = [u.id for u in units]

        leases = session.exec(
            select(Lease).where(
                Lease.unit_id.in_(unit_ids),
                Lease.deleted_at.is_(None),
            )
        ).all()
        lease_ids = [lea.id for lea in leases]

        total_income = Decimal("0")
        if lease_ids:
            invoices = session.exec(
                select(Invoice).where(
                    Invoice.lease_id.in_(lease_ids),
                    Invoice.deleted_at.is_(None),
                    Invoice.period >= f"{year}-01",
                    Invoice.period <= f"{year}-12",
                )
            ).all()
            total_income = sum((inv.total for inv in invoices), Decimal("0"))

        return {
            "property_id": property_id,
            "year": year,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "deductible_expenses": deductible_expenses,
            "non_deductible_expenses": total_expenses - deductible_expenses,
            "net_profitability": total_income - total_expenses,
            "by_category": by_category,
        }
