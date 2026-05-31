import tempfile
from datetime import date
from decimal import Decimal

from app.services.bank_adapter import GenericBankAdapter, INGBankAdapter


class TestGenericBankAdapter:
    def test_parse_basic_csv(self):
        csv_content = (
            "01/06/2024;Transferencia inquilino;850,00;ES9121000418450200051332;REF001\n"
            "15/06/2024;Pago comunidad;-85,00;;\n"
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            tmp_path = f.name

        adapter = GenericBankAdapter()
        rows = adapter.parse(tmp_path)

        assert len(rows) == 2
        assert rows[0].entry_date == date(2024, 6, 1)
        assert rows[0].concept == "Transferencia inquilino"
        assert rows[0].amount == Decimal("850.00")
        assert rows[0].iban_origin == "ES9121000418450200051332"
        assert rows[0].reference == "REF001"

        assert rows[1].entry_date == date(2024, 6, 15)
        assert rows[1].amount == Decimal("-85.00")

    def test_parse_with_skip_rows(self):
        csv_content = "Header1;Header2;Header3;Header4\n01/06/2024;Concepto;100,00;IBAN001\n"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            tmp_path = f.name

        adapter = GenericBankAdapter(skip_rows=1)
        rows = adapter.parse(tmp_path)

        assert len(rows) == 1
        assert rows[0].amount == Decimal("100.00")

    def test_empty_line_skipped(self):
        csv_content = "01/06/2024;Concepto;100,00;\n\n15/06/2024;Otro;200,00;\n"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            tmp_path = f.name

        adapter = GenericBankAdapter()
        rows = adapter.parse(tmp_path)

        assert len(rows) == 2


class TestINGBankAdapter:
    def test_parse_ing_format(self):
        csv_content = (
            "Fecha;Concepto;Importe;Saldo\n"
            "01/01/2024;INFORMACION;0,00;0,00\n"
            "01/06/2024;INGRESO TRANSFERENCIA;850,00;1500,00\n"
            "15/06/2024;RECIBO COMUNIDAD;-85,00;1415,00\n"
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="latin-1"
        ) as f:
            f.write(csv_content)
            tmp_path = f.name

        adapter = INGBankAdapter()
        rows = adapter.parse(tmp_path)

        assert len(rows) == 2
        assert rows[0].amount == Decimal("850.00")
        assert rows[0].concept == "INGRESO TRANSFERENCIA"
        assert rows[1].amount == Decimal("-85.00")
