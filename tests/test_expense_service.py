from datetime import date
from decimal import Decimal

from sqlmodel import Session

from app.models.invoice import Invoice, InvoiceLine
from app.models.lease import Lease, RentCondition
from app.models.property import Property
from app.services.expense_service import ExpenseError, ExpenseService


class TestRegister:
    def test_register_valid_expense(self, session: Session, sample_lease: Lease):
        prop = session.get(Property, sample_lease.unit.property_id)
        expense = ExpenseService.register(
            session,
            prop.id,
            "community",
            Decimal("85.50"),
            date(2024, 6, 1),
        )

        assert expense.property_id == prop.id
        assert expense.category == "community"
        assert expense.amount == Decimal("85.50")
        assert expense.expense_date == date(2024, 6, 1)
        assert expense.deductible is True

    def test_register_with_lease(self, session: Session, sample_lease: Lease):
        prop = session.get(Property, sample_lease.unit.property_id)
        expense = ExpenseService.register(
            session,
            prop.id,
            "repairs",
            Decimal("200.00"),
            date(2024, 6, 15),
            lease_id=sample_lease.id,
            deductible=False,
            supplier="Ferretería S.L.",
            invoice_number="F2024-001",
            notes="Reparación grifo cocina",
        )

        assert expense.lease_id == sample_lease.id
        assert expense.deductible is False
        assert expense.supplier == "Ferretería S.L."
        assert expense.invoice_number == "F2024-001"
        assert expense.notes == "Reparación grifo cocina"

    def test_property_not_found_raises(self, session: Session):
        from pytest import raises

        with raises(ExpenseError, match="Property 999 not found"):
            ExpenseService.register(
                session,
                999,
                "community",
                Decimal("100"),
                date(2024, 1, 1),
            )

    def test_invalid_category_raises(self, session: Session, sample_lease: Lease):
        from pytest import raises

        prop = session.get(Property, sample_lease.unit.property_id)
        with raises(ExpenseError, match="Invalid category"):
            ExpenseService.register(
                session,
                prop.id,
                "inventado",
                Decimal("100"),
                date(2024, 1, 1),
            )

    def test_zero_amount_raises(self, session: Session, sample_lease: Lease):
        from pytest import raises

        prop = session.get(Property, sample_lease.unit.property_id)
        with raises(ExpenseError, match="Amount must be positive"):
            ExpenseService.register(
                session,
                prop.id,
                "community",
                Decimal("0"),
                date(2024, 1, 1),
            )

    def test_lease_not_found_raises(self, session: Session, sample_lease: Lease):
        from pytest import raises

        prop = session.get(Property, sample_lease.unit.property_id)
        with raises(ExpenseError, match="Lease 999 not found"):
            ExpenseService.register(
                session,
                prop.id,
                "community",
                Decimal("100"),
                date(2024, 1, 1),
                lease_id=999,
            )


class TestListByProperty:
    def test_list_by_property(self, session: Session, sample_lease: Lease):
        prop = session.get(Property, sample_lease.unit.property_id)
        ExpenseService.register(session, prop.id, "community", Decimal("85"), date(2024, 6, 1))
        ExpenseService.register(session, prop.id, "insurance", Decimal("30"), date(2024, 6, 1))

        expenses = ExpenseService.list_by_property(session, prop.id)
        assert len(expenses) == 2

    def test_list_by_property_and_year(self, session: Session, sample_lease: Lease):
        prop = session.get(Property, sample_lease.unit.property_id)
        ExpenseService.register(session, prop.id, "community", Decimal("85"), date(2024, 6, 1))
        ExpenseService.register(session, prop.id, "community", Decimal("90"), date(2025, 1, 1))

        expenses_2024 = ExpenseService.list_by_property(session, prop.id, year=2024)
        assert len(expenses_2024) == 1

        expenses_all = ExpenseService.list_by_property(session, prop.id)
        assert len(expenses_all) == 2

    def test_property_not_found_raises(self, session: Session):
        from pytest import raises

        with raises(ExpenseError, match="Property 999 not found"):
            ExpenseService.list_by_property(session, 999)


class TestSummary:
    def test_summary_no_income_no_expenses(self, session: Session, sample_lease: Lease):
        prop = session.get(Property, sample_lease.unit.property_id)
        result = ExpenseService.summary(session, prop.id, 2024)

        assert result["property_id"] == prop.id
        assert result["year"] == 2024
        assert result["total_income"] == Decimal("0")
        assert result["total_expenses"] == Decimal("0")
        assert result["net_profitability"] == Decimal("0")

    def test_summary_with_expenses(self, session: Session, sample_lease: Lease):
        prop = session.get(Property, sample_lease.unit.property_id)
        ExpenseService.register(
            session,
            prop.id,
            "community",
            Decimal("85"),
            date(2024, 6, 1),
        )
        ExpenseService.register(
            session,
            prop.id,
            "insurance",
            Decimal("30"),
            date(2024, 6, 1),
            deductible=False,
        )

        result = ExpenseService.summary(session, prop.id, 2024)

        assert result["total_expenses"] == Decimal("115")
        assert result["deductible_expenses"] == Decimal("85")
        assert result["non_deductible_expenses"] == Decimal("30")
        assert result["by_category"]["community"] == Decimal("85")
        assert result["by_category"]["insurance"] == Decimal("30")

    def test_summary_with_income(self, session: Session, sample_lease: Lease):
        prop = session.get(Property, sample_lease.unit.property_id)
        rc = RentCondition(
            lease_id=sample_lease.id,
            start_date=date(2024, 1, 1),
            monthly_rent=Decimal("1000"),
        )
        session.add(rc)
        session.flush()

        inv = Invoice(
            period="2024-06",
            lease_id=sample_lease.id,
            issue_date=date(2024, 6, 1),
            status="paid",
            total_base=Decimal("1000"),
            total_vat=Decimal("0"),
            total_irpf_withholding=Decimal("0"),
            total=Decimal("1000"),
        )
        session.add(inv)
        session.flush()

        line = InvoiceLine(
            invoice_id=inv.id,
            concept="Alquiler 2024-06",
            base_amount=Decimal("1000"),
            vat_rate=Decimal("0"),
            vat_amount=Decimal("0"),
            irpf_rate=Decimal("0"),
            irpf_withholding=Decimal("0"),
        )
        session.add(line)
        session.commit()

        ExpenseService.register(
            session,
            prop.id,
            "community",
            Decimal("85"),
            date(2024, 6, 1),
        )

        result = ExpenseService.summary(session, prop.id, 2024)

        assert result["total_income"] == Decimal("1000")
        assert result["total_expenses"] == Decimal("85")
        assert result["net_profitability"] == Decimal("915")

    def test_summary_property_not_found_raises(self, session: Session):
        from pytest import raises

        with raises(ExpenseError, match="Property 999 not found"):
            ExpenseService.summary(session, 999, 2024)
