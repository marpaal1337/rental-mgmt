from datetime import date
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, func, select

from app.models.invoice import Invoice


class InvoiceNumberingError(Exception):
    """Raised when an invoice number cannot be assigned."""


class InvoiceNumberingService:
    """Asigna números correlativos por serie y ejercicio, sin huecos."""

    DEFAULT_SERIES = "A"
    RECTIFICATION_SERIES = "R"
    MAX_ATTEMPTS = 3

    @staticmethod
    def format_number(series: str, fiscal_year: int, sequence: int) -> str:
        return f"{series}-{fiscal_year}-{sequence:04d}"

    @classmethod
    def assign_number(
        cls,
        session: Session,
        invoice: Invoice,
        *,
        series: Optional[str] = None,
    ) -> str:
        if invoice.number:
            return invoice.number

        target_series = series or invoice.series or cls.DEFAULT_SERIES
        fiscal_year = (invoice.issue_date or date.today()).year

        for _ in range(cls.MAX_ATTEMPTS):
            sequence = cls._next_sequence(session, target_series, fiscal_year)
            invoice.series = target_series
            invoice.fiscal_year = fiscal_year
            invoice.sequence = sequence
            invoice.number = cls.format_number(target_series, fiscal_year, sequence)
            try:
                with session.begin_nested():
                    session.add(invoice)
                    session.flush()
                return invoice.number
            except IntegrityError:
                continue

        raise InvoiceNumberingError(
            f"Could not assign invoice number for series {target_series}/{fiscal_year}"
        )

    @staticmethod
    def _next_sequence(session: Session, series: str, fiscal_year: int) -> int:
        current = session.exec(
            select(func.max(Invoice.sequence)).where(
                Invoice.series == series,
                Invoice.fiscal_year == fiscal_year,
            )
        ).one()
        return (current or 0) + 1
