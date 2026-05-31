from datetime import date
from decimal import Decimal
from typing import Optional


class BankRow:
    """Parsed row from a bank CSV."""

    def __init__(
        self,
        entry_date: date,
        concept: str,
        amount: Decimal,
        value_date: Optional[date] = None,
        iban_origin: Optional[str] = None,
        reference: Optional[str] = None,
        raw: Optional[str] = None,
    ) -> None:
        self.entry_date = entry_date
        self.concept = concept
        self.amount = amount
        self.value_date = value_date
        self.iban_origin = iban_origin
        self.reference = reference
        self.raw = raw


class BaseBankAdapter:
    """Base adapter for bank CSV import."""

    def parse(self, file_path: str) -> list[BankRow]:
        raise NotImplementedError


class GenericBankAdapter(BaseBankAdapter):
    """Adapter for simple CSV with configurable column mapping.

    Expects CSV with header. Default columns:
      0: date (DD/MM/YYYY)
      1: concept
      2: amount (positive for income, negative for expense)
      3: iban_origin (optional)
      4: reference (optional)
    """

    def __init__(
        self,
        delimiter: str = ";",
        date_format: str = "%d/%m/%Y",
        encoding: str = "utf-8",
        skip_rows: int = 0,
        col_date: int = 0,
        col_concept: int = 1,
        col_amount: int = 2,
        col_iban: Optional[int] = 3,
        col_reference: Optional[int] = 4,
    ) -> None:
        self.delimiter = delimiter
        self.date_format = date_format
        self.encoding = encoding
        self.skip_rows = skip_rows
        self.col_date = col_date
        self.col_concept = col_concept
        self.col_amount = col_amount
        self.col_iban = col_iban
        self.col_reference = col_reference

    def parse(self, file_path: str) -> list[BankRow]:
        import csv

        rows: list[BankRow] = []
        with open(file_path, newline="", encoding=self.encoding) as f:
            for _ in range(self.skip_rows):
                next(f)
            reader = csv.reader(f, delimiter=self.delimiter)
            for csv_row in reader:
                if not csv_row or not csv_row[self.col_date].strip():
                    continue
                entry_date = self._parse_date(csv_row[self.col_date])
                concept = csv_row[self.col_concept].strip()
                raw_amount = csv_row[self.col_amount].strip().replace(",", ".")
                amount = Decimal(raw_amount)
                iban = (
                    csv_row[self.col_iban].strip()
                    if self.col_iban is not None and len(csv_row) > self.col_iban
                    else None
                )
                ref = (
                    csv_row[self.col_reference].strip()
                    if self.col_reference is not None and len(csv_row) > self.col_reference
                    else None
                )
                rows.append(
                    BankRow(
                        entry_date=entry_date,
                        concept=concept,
                        amount=amount,
                        iban_origin=iban,
                        reference=ref,
                        raw=";".join(csv_row),
                    )
                )
        return rows

    def _parse_date(self, raw: str) -> date:
        from datetime import datetime as dt

        return dt.strptime(raw.strip(), self.date_format).date()


class INGBankAdapter(GenericBankAdapter):
    """Adapter for ING España CSV export format.

    ING format (semicolon-delimited, skips first 2 rows):
      Fecha;Concepto;Importe;Saldo;...
    """

    def __init__(self) -> None:
        super().__init__(
            delimiter=";",
            date_format="%d/%m/%Y",
            encoding="latin-1",
            skip_rows=2,
            col_date=0,
            col_concept=1,
            col_amount=2,
            col_iban=None,
            col_reference=None,
        )
