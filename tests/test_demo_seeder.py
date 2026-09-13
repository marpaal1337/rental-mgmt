from datetime import date

from sqlmodel import Session, SQLModel, func, select

import app.models.event_log  # noqa: F401  (register table for create_all)
from app.database import create_db_engine
from app.jobs.daily_overdue import detect_overdue_invoices
from app.models.bank import Reconciliation
from app.models.expense import Expense
from app.models.invoice import Invoice
from app.models.lease import Deposit, TaxProfile
from app.models.owner import Owner
from app.models.property import Property
from app.seeder import seed_database, seed_demo_dataset


def _fresh_session() -> Session:
    engine = create_db_engine("sqlite://", echo=False)
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_demo_dataset_creates_full_dataset(session: Session) -> None:
    summary = seed_demo_dataset(session, years=1)

    assert summary["owners"] == 5
    assert summary["properties"] == 8
    assert summary["units"] == 12
    assert summary["tenants"] == 11
    assert summary["leases"] == 13
    assert summary["tax_profiles"] == 12
    assert summary["deposits"] == 13
    assert summary["invoices"] > 100
    assert summary["payments"] > 80
    assert summary["expenses"] > 20
    assert summary["bank_movements"] > 10
    assert summary["reconciliations"] > 5


def test_demo_dataset_uses_dates_relative_to_today(session: Session) -> None:
    seed_demo_dataset(session, years=1)

    today = date.today()
    current_period = f"{today.year}-{today.month:02d}"
    current_invoices = session.exec(
        select(func.count()).select_from(Invoice).where(Invoice.period == current_period)
    ).one()

    assert current_invoices > 0
    assert len(detect_overdue_invoices(session)) >= 1


def test_demo_dataset_assigns_legal_correlative_numbers(session: Session) -> None:
    seed_demo_dataset(session, years=1)

    invoices = session.exec(select(Invoice)).all()
    assert invoices
    assert all(inv.number for inv in invoices)

    sequences: dict[tuple[str, int], list[int]] = {}
    for invoice in invoices:
        sequences.setdefault((invoice.series, invoice.fiscal_year), []).append(invoice.sequence)

    for seqs in sequences.values():
        assert sorted(seqs) == list(range(1, len(seqs) + 1))


def test_demo_dataset_includes_edge_cases(session: Session) -> None:
    seed_demo_dataset(session, years=1)

    tax_profiles = session.exec(select(func.count()).select_from(TaxProfile)).one()
    assert tax_profiles == 12

    returned_deposit = session.exec(select(Deposit).where(Deposit.return_date.is_not(None))).first()
    assert returned_deposit is not None

    deleted_expense = session.exec(select(Expense).where(Expense.deleted_at.is_not(None))).first()
    assert deleted_expense is not None

    confirmed = session.exec(
        select(Reconciliation).where(Reconciliation.confirmed_at.is_not(None))
    ).first()
    assert confirmed is not None

    rectifications = session.exec(
        select(Invoice).where(Invoice.corrected_invoice_id.is_not(None))
    ).all()
    assert rectifications
    assert all(invoice.total < 0 for invoice in rectifications)


def test_demo_dataset_is_idempotent_without_clean(session: Session) -> None:
    first = seed_demo_dataset(session, years=1)
    assert first

    second = seed_demo_dataset(session, years=1)

    assert second == {}
    owners = session.exec(select(func.count()).select_from(Owner)).one()
    assert owners == 5


def test_demo_dataset_clean_replaces_previous_data(session: Session) -> None:
    seed_database(session)

    summary = seed_demo_dataset(session, clean=True, years=1)

    assert summary["owners"] == 5
    assert summary["properties"] == 8
    basic_property = session.exec(select(Property).where(Property.name == "Piso Centro")).first()
    assert basic_property is None

    reseeded = seed_demo_dataset(session, clean=True, years=1, seed=1)
    assert reseeded["owners"] == 5
    assert reseeded["invoices"] == summary["invoices"]


def test_demo_dataset_is_deterministic() -> None:
    with _fresh_session() as first, _fresh_session() as second:
        seed_demo_dataset(first, years=1, seed=7)
        seed_demo_dataset(second, years=1, seed=7)

        numbers_first = [
            inv.number for inv in first.exec(select(Invoice).order_by(Invoice.id)).all()
        ]
        numbers_second = [
            inv.number for inv in second.exec(select(Invoice).order_by(Invoice.id)).all()
        ]

    assert numbers_first
    assert numbers_first == numbers_second
