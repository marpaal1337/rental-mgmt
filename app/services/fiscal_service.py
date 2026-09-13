from datetime import date
from decimal import Decimal
from typing import Any

from sqlmodel import Session, func, select

from app.models.expense import Expense
from app.models.invoice import Invoice, InvoiceLine
from app.models.lease import Lease
from app.models.owner import Owner
from app.models.property import Property
from app.models.unit import Unit

CENT = Decimal("0.01")
INVOICE_STATUSES = ("issued", "partial", "paid")
VAT_CRITERIA = (
    "IVA devengado por fecha de expedición de factura; "
    "IVA soportado por fecha del gasto"
)
WITHHOLDING_CRITERIA = "Retenciones por fecha de expedición de factura"
INCOME_CRITERIA = "Ingresos por fecha de expedición de factura; gastos por fecha del gasto"


class FiscalError(Exception):
    """Raised when fiscal report arguments are invalid."""


def _to_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _fmt(value: Any) -> str:
    return f"{_to_decimal(value).quantize(CENT):.2f}"


def _quarter_bounds(year: int, quarter: int) -> tuple[date, date]:
    first_month = (quarter - 1) * 3 + 1
    start = date(year, first_month, 1)
    if quarter == 4:
        end = date(year, 12, 31)
    else:
        end = date.fromordinal(date(year, first_month + 3, 1).toordinal() - 1)
    return start, end


class FiscalService:
    @staticmethod
    def validate_year(year: int) -> int:
        if year < 2000 or year > 2100:
            raise FiscalError("Year must be between 2000 and 2100")
        return year

    @staticmethod
    def validate_quarter(quarter: int) -> int:
        if quarter < 1 or quarter > 4:
            raise FiscalError("Quarter must be between 1 and 4")
        return quarter

    @staticmethod
    def vat_report(session: Session, year: int, quarter: int) -> dict:
        """Informe trimestral de IVA (modelo 303)."""
        year = FiscalService.validate_year(year)
        quarter = FiscalService.validate_quarter(quarter)
        start, end = _quarter_bounds(year, quarter)

        output_rows = session.exec(
            select(
                InvoiceLine.vat_rate,
                func.coalesce(func.sum(InvoiceLine.base_amount), Decimal("0")),
                func.coalesce(func.sum(InvoiceLine.vat_amount), Decimal("0")),
            )
            .join(Invoice, InvoiceLine.invoice_id == Invoice.id)
            .where(
                Invoice.deleted_at.is_(None),
                Invoice.status.in_(INVOICE_STATUSES),
                Invoice.issue_date >= start,
                Invoice.issue_date <= end,
            )
            .group_by(InvoiceLine.vat_rate)
            .order_by(InvoiceLine.vat_rate)
        ).all()

        output: list[dict] = []
        exempt_base = Decimal("0")
        output_base = Decimal("0")
        output_vat = Decimal("0")
        for rate, base, vat in output_rows:
            base_d = _to_decimal(base)
            vat_d = _to_decimal(vat)
            if vat_d == 0:
                exempt_base += base_d
                continue
            output_base += base_d
            output_vat += vat_d
            output.append(
                {"vat_rate": _fmt(rate), "base": _fmt(base_d), "vat": _fmt(vat_d)}
            )

        input_rows = session.exec(
            select(
                Expense.vat_rate,
                func.coalesce(
                    func.sum(Expense.amount - Expense.vat_amount), Decimal("0")
                ),
                func.coalesce(func.sum(Expense.vat_amount), Decimal("0")),
            )
            .where(
                Expense.deleted_at.is_(None),
                Expense.deductible.is_(True),
                Expense.vat_amount > 0,
                Expense.expense_date >= start,
                Expense.expense_date <= end,
            )
            .group_by(Expense.vat_rate)
            .order_by(Expense.vat_rate)
        ).all()

        input_lines: list[dict] = []
        input_base = Decimal("0")
        input_vat = Decimal("0")
        for rate, base, vat in input_rows:
            base_d = _to_decimal(base)
            vat_d = _to_decimal(vat)
            input_base += base_d
            input_vat += vat_d
            input_lines.append(
                {"vat_rate": _fmt(rate), "base": _fmt(base_d), "vat": _fmt(vat_d)}
            )

        return {
            "year": year,
            "quarter": quarter,
            "label": f"{quarter}T {year}",
            "date_from": start.isoformat(),
            "date_to": end.isoformat(),
            "criteria": VAT_CRITERIA,
            "output": output,
            "exempt": {"base": _fmt(exempt_base)},
            "input": input_lines,
            "totals": {
                "output_base": _fmt(output_base),
                "output_vat": _fmt(output_vat),
                "exempt_base": _fmt(exempt_base),
                "input_base": _fmt(input_base),
                "input_vat": _fmt(input_vat),
                "vat_due": _fmt(output_vat - input_vat),
            },
        }

    @staticmethod
    def withholdings_report(session: Session, year: int) -> dict:
        """Resumen anual de retenciones de IRPF soportadas (modelo 190)."""
        year = FiscalService.validate_year(year)
        start, end = date(year, 1, 1), date(year, 12, 31)

        rows = session.exec(
            select(
                Invoice.recipient_name,
                Invoice.recipient_document_type,
                Invoice.recipient_document_number,
                func.count(Invoice.id),
                func.coalesce(func.sum(Invoice.total_base), Decimal("0")),
                func.coalesce(
                    func.sum(Invoice.total_irpf_withholding), Decimal("0")
                ),
            )
            .where(
                Invoice.deleted_at.is_(None),
                Invoice.status.in_(INVOICE_STATUSES),
                Invoice.issue_date >= start,
                Invoice.issue_date <= end,
                Invoice.total_irpf_withholding != 0,
            )
            .group_by(
                Invoice.recipient_name,
                Invoice.recipient_document_type,
                Invoice.recipient_document_number,
            )
            .order_by(Invoice.recipient_name)
        ).all()

        result_rows: list[dict] = []
        total_base = Decimal("0")
        total_withholding = Decimal("0")
        for name, doc_type, doc_number, count, base, withholding in rows:
            base_d = _to_decimal(base)
            withholding_d = _to_decimal(withholding)
            total_base += base_d
            total_withholding += withholding_d
            result_rows.append(
                {
                    "recipient_name": name or "No identificado",
                    "recipient_document_type": doc_type,
                    "recipient_document_number": doc_number,
                    "invoice_count": count,
                    "base": _fmt(base_d),
                    "withholding": _fmt(withholding_d),
                }
            )

        return {
            "year": year,
            "criteria": WITHHOLDING_CRITERIA,
            "rows": result_rows,
            "totals": {
                "base": _fmt(total_base),
                "withholding": _fmt(total_withholding),
            },
        }

    @staticmethod
    def income_report(session: Session, year: int) -> dict:
        """Rendimiento anual del capital inmobiliario por propiedad (modelo 100)."""
        year = FiscalService.validate_year(year)
        start, end = date(year, 1, 1), date(year, 12, 31)

        property_rows = session.exec(
            select(Property.id, Property.name, Owner.id, Owner.name)
            .join(Owner, Property.owner_id == Owner.id)
            .where(Property.deleted_at.is_(None))
            .order_by(Property.name)
        ).all()

        rows: dict[int, dict] = {
            pid: {
                "property_id": pid,
                "property_name": pname,
                "owner_id": oid,
                "owner_name": oname,
                "invoice_count": 0,
                "gross_income": Decimal("0"),
                "deductible_expenses": Decimal("0"),
                "non_deductible_expenses": Decimal("0"),
                "by_category": {},
            }
            for pid, pname, oid, oname in property_rows
        }

        income_rows = session.exec(
            select(
                Property.id,
                func.count(Invoice.id),
                func.coalesce(func.sum(Invoice.total_base), Decimal("0")),
            )
            .select_from(Invoice)
            .join(Lease, Invoice.lease_id == Lease.id)
            .join(Unit, Lease.unit_id == Unit.id)
            .join(Property, Unit.property_id == Property.id)
            .where(
                Invoice.deleted_at.is_(None),
                Invoice.status.in_(INVOICE_STATUSES),
                Invoice.issue_date >= start,
                Invoice.issue_date <= end,
            )
            .group_by(Property.id)
        ).all()
        for pid, count, base in income_rows:
            row = rows.get(pid)
            if row is None:
                continue
            row["invoice_count"] += count
            row["gross_income"] += _to_decimal(base)

        deductible_rows = session.exec(
            select(Property.id, Expense.category, func.sum(Expense.amount))
            .select_from(Expense)
            .join(Property, Expense.property_id == Property.id)
            .where(
                Expense.deleted_at.is_(None),
                Expense.deductible.is_(True),
                Expense.expense_date >= start,
                Expense.expense_date <= end,
            )
            .group_by(Property.id, Expense.category)
        ).all()
        for pid, category, amount in deductible_rows:
            row = rows.get(pid)
            if row is None:
                continue
            amount_d = _to_decimal(amount)
            row["deductible_expenses"] += amount_d
            row["by_category"][category] = row["by_category"].get(
                category, Decimal("0")
            ) + amount_d

        non_deductible_rows = session.exec(
            select(Property.id, func.sum(Expense.amount))
            .select_from(Expense)
            .join(Property, Expense.property_id == Property.id)
            .where(
                Expense.deleted_at.is_(None),
                Expense.deductible.is_(False),
                Expense.expense_date >= start,
                Expense.expense_date <= end,
            )
            .group_by(Property.id)
        ).all()
        for pid, amount in non_deductible_rows:
            row = rows.get(pid)
            if row is None:
                continue
            row["non_deductible_expenses"] += _to_decimal(amount)

        result_rows: list[dict] = []
        totals = {
            "gross_income": Decimal("0"),
            "deductible_expenses": Decimal("0"),
            "non_deductible_expenses": Decimal("0"),
            "net_income": Decimal("0"),
        }
        for row in rows.values():
            has_activity = (
                row["invoice_count"] > 0
                or row["deductible_expenses"] > 0
                or row["non_deductible_expenses"] > 0
            )
            if not has_activity:
                continue
            net = row["gross_income"] - row["deductible_expenses"]
            totals["gross_income"] += row["gross_income"]
            totals["deductible_expenses"] += row["deductible_expenses"]
            totals["non_deductible_expenses"] += row["non_deductible_expenses"]
            totals["net_income"] += net
            result_rows.append(
                {
                    "property_id": row["property_id"],
                    "property_name": row["property_name"],
                    "owner_id": row["owner_id"],
                    "owner_name": row["owner_name"],
                    "invoice_count": row["invoice_count"],
                    "gross_income": _fmt(row["gross_income"]),
                    "deductible_expenses": _fmt(row["deductible_expenses"]),
                    "non_deductible_expenses": _fmt(row["non_deductible_expenses"]),
                    "net_income": _fmt(net),
                    "by_category": {
                        category: _fmt(amount)
                        for category, amount in sorted(row["by_category"].items())
                    },
                }
            )

        result_rows.sort(key=lambda item: item["property_name"])

        return {
            "year": year,
            "criteria": INCOME_CRITERIA,
            "rows": result_rows,
            "totals": {
                "gross_income": _fmt(totals["gross_income"]),
                "deductible_expenses": _fmt(totals["deductible_expenses"]),
                "non_deductible_expenses": _fmt(totals["non_deductible_expenses"]),
                "net_income": _fmt(totals["net_income"]),
            },
        }
