from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import Session, func, select

from app.models.expense import EXPENSE_CATEGORIES, Expense
from app.models.invoice import Invoice
from app.models.lease import Lease
from app.models.property import Property
from app.models.unit import Unit

INCOME_STATUSES = ("issued", "partial", "paid")
CENT = Decimal("0.01")


class ExpenseError(Exception):
    """Raised when expense operations fail."""


class ExpenseService:
    CATEGORIES = EXPENSE_CATEGORIES

    @staticmethod
    def _validate_property(session: Session, property_id: int) -> None:
        prop = session.get(Property, property_id)
        if prop is None or prop.deleted_at is not None:
            raise ExpenseError(f"Property {property_id} not found")

    @staticmethod
    def _validate_lease(session: Session, lease_id: int) -> None:
        lea = session.get(Lease, lease_id)
        if lea is None or lea.deleted_at is not None:
            raise ExpenseError(f"Lease {lease_id} not found")

    @staticmethod
    def _compute_vat_amount(amount: Decimal, vat_rate: Optional[Decimal]) -> Decimal:
        """Calcula la cuota de IVA incluida en un importe total."""
        rate = vat_rate if vat_rate is not None else Decimal("0")
        if rate < 0 or rate > Decimal("100"):
            raise ExpenseError("VAT rate must be between 0 and 100")
        if rate == 0:
            return Decimal("0")
        return (amount * rate / (Decimal("100") + rate)).quantize(CENT)

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
        vat_rate: Optional[Decimal] = None,
    ) -> Expense:
        ExpenseService._validate_property(session, property_id)

        if category not in EXPENSE_CATEGORIES:
            raise ExpenseError(
                f"Invalid category '{category}'. Valid: {', '.join(EXPENSE_CATEGORIES)}"
            )

        if amount <= Decimal("0"):
            raise ExpenseError("Amount must be positive")

        if lease_id is not None:
            ExpenseService._validate_lease(session, lease_id)

        vat_amount = ExpenseService._compute_vat_amount(amount, vat_rate)

        expense = Expense(
            property_id=property_id,
            lease_id=lease_id,
            category=category,
            amount=amount,
            vat_rate=vat_rate if vat_rate is not None else Decimal("0"),
            vat_amount=vat_amount,
            expense_date=expense_date,
            deductible=deductible,
            supplier=supplier,
            invoice_number=invoice_number,
            notes=notes,
        )
        session.add(expense)
        session.flush()
        return expense

    @staticmethod
    def update(session: Session, expense_id: int, **changes) -> Expense:
        expense = session.get(Expense, expense_id)
        if expense is None or expense.deleted_at is not None:
            raise ExpenseError(f"Expense {expense_id} not found")

        if "property_id" in changes:
            ExpenseService._validate_property(session, changes["property_id"])
        if changes.get("lease_id") is not None:
            ExpenseService._validate_lease(session, changes["lease_id"])

        category = changes.get("category", expense.category)
        if category not in EXPENSE_CATEGORIES:
            raise ExpenseError(
                f"Invalid category '{category}'. Valid: {', '.join(EXPENSE_CATEGORIES)}"
            )

        amount = changes.get("amount", expense.amount)
        if amount <= Decimal("0"):
            raise ExpenseError("Amount must be positive")

        vat_rate = changes.get("vat_rate", expense.vat_rate)
        if "amount" in changes or "vat_rate" in changes:
            changes["vat_amount"] = ExpenseService._compute_vat_amount(amount, vat_rate)

        for field, value in changes.items():
            setattr(expense, field, value)
        expense.updated_at = datetime.now(UTC)
        session.add(expense)
        session.flush()
        return expense

    @staticmethod
    def list_expenses(
        session: Session,
        property_id: Optional[int] = None,
        year: Optional[int] = None,
    ) -> list[Expense]:
        query = select(Expense).where(Expense.deleted_at.is_(None))
        if property_id is not None:
            prop = session.get(Property, property_id)
            if prop is None or prop.deleted_at is not None:
                raise ExpenseError(f"Property {property_id} not found")
            query = query.where(Expense.property_id == property_id)
        if year is not None:
            query = query.where(
                Expense.expense_date >= date(year, 1, 1),
                Expense.expense_date <= date(year, 12, 31),
            )
        query = query.order_by(Expense.expense_date.desc())
        return list(session.exec(query).all())

    @staticmethod
    def list_by_property(
        session: Session,
        property_id: int,
        year: Optional[int] = None,
    ) -> list[Expense]:
        return ExpenseService.list_expenses(session, property_id, year)

    @staticmethod
    def summary(
        session: Session,
        property_id: int,
        year: int,
    ) -> dict:
        prop = session.get(Property, property_id)
        if prop is None or prop.deleted_at is not None:
            raise ExpenseError(f"Property {property_id} not found")

        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)

        by_category_rows = session.exec(
            select(
                Expense.category,
                func.coalesce(func.sum(Expense.amount), Decimal("0")),
            )
            .where(
                Expense.property_id == property_id,
                Expense.deleted_at.is_(None),
                Expense.expense_date >= year_start,
                Expense.expense_date <= year_end,
            )
            .group_by(Expense.category)
        ).all()
        by_category: dict[str, Decimal] = {
            category: amount for category, amount in by_category_rows
        }
        total_expenses = sum(by_category.values(), Decimal("0"))

        deductible_expenses = session.exec(
            select(func.coalesce(func.sum(Expense.amount), Decimal("0"))).where(
                Expense.property_id == property_id,
                Expense.deleted_at.is_(None),
                Expense.deductible.is_(True),
                Expense.expense_date >= year_start,
                Expense.expense_date <= year_end,
            )
        ).one()

        total_income = session.exec(
            select(func.coalesce(func.sum(Invoice.total), Decimal("0")))
            .join(Lease, Invoice.lease_id == Lease.id)
            .join(Unit, Lease.unit_id == Unit.id)
            .where(
                Unit.property_id == property_id,
                Unit.deleted_at.is_(None),
                Lease.deleted_at.is_(None),
                Invoice.deleted_at.is_(None),
                Invoice.status.in_(INCOME_STATUSES),
                Invoice.period >= f"{year}-01",
                Invoice.period <= f"{year}-12",
            )
        ).one()

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
