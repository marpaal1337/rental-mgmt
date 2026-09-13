import sqlite3
from pathlib import Path

from alembic.config import Config

from alembic import command

ROOT = Path(__file__).resolve().parent.parent


def _alembic_config(db_path: Path) -> Config:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return config


def test_upgrade_from_zero_creates_full_schema(tmp_path, monkeypatch):
    db_path = tmp_path / "migration.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    command.upgrade(_alembic_config(db_path), "head")

    connection = sqlite3.connect(db_path)
    tables = {
        row[0]
        for row in connection.execute(
            "select name from sqlite_master where type='table'"
        )
    }
    assert {
        "owner",
        "property",
        "unit",
        "tenant",
        "lease",
        "rent_condition",
        "tax_profile",
        "deposit",
        "index_update",
        "invoice",
        "invoice_line",
        "payment",
        "expense",
        "bank_movement",
        "reconciliation",
        "event_log",
    } <= tables

    indexes = {
        row[0]
        for row in connection.execute(
            "select name from sqlite_master where type='index' and name not like 'sqlite_%'"
        )
    }
    assert "uq_invoice_lease_period_active" in indexes
    assert "ix_invoice_lease_id" in indexes
    assert "ix_lease_tenant_id" in indexes

    reconciliation_ddl = connection.execute(
        "select sql from sqlite_master where name='reconciliation'"
    ).fetchone()[0]
    assert "UNIQUE (BANK_MOVEMENT_ID)" not in reconciliation_ddl.upper()

    connection.close()


def test_downgrade_and_upgrade_cycle(tmp_path, monkeypatch):
    db_path = tmp_path / "cycle.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    config = _alembic_config(db_path)

    command.upgrade(config, "head")
    command.downgrade(config, "-1")
    command.upgrade(config, "head")

    connection = sqlite3.connect(db_path)
    version = connection.execute("select version_num from alembic_version").fetchone()[0]
    assert version
    connection.close()


def test_backfill_numbers_and_snapshots_legacy_invoices(tmp_path, monkeypatch):
    db_path = tmp_path / "backfill.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    config = _alembic_config(db_path)
    command.upgrade(config, "b7d1c9e2a4f0")

    connection = sqlite3.connect(db_path)
    now = "2024-01-01 00:00:00"
    connection.execute(
        "INSERT INTO owner (id, name, document_type, document_number, email, phone, "
        "address, created_at, updated_at) VALUES "
        "(1, 'Legacy Owner', 'DNI', '11111111A', 'o@t.com', '600', 'Calle Emisor', ?, ?)",
        (now, now),
    )
    connection.execute(
        "INSERT INTO tenant (id, name, document_type, document_number, email, phone, "
        "created_at, updated_at) VALUES "
        "(1, 'Legacy Tenant', 'DNI', '22222222B', 't@t.com', '611', ?, ?)",
        (now, now),
    )
    connection.execute(
        "INSERT INTO property (id, name, address, city, province, zip_code, owner_id, "
        "created_at, updated_at) VALUES "
        "(1, 'P', 'Calle 1', 'Madrid', 'Madrid', '28001', 1, ?, ?)",
        (now, now),
    )
    connection.execute(
        "INSERT INTO unit (id, property_id, name, unit_type, is_active, created_at, updated_at) "
        "VALUES (1, 1, 'U', 'vivienda', 1, ?, ?)",
        (now, now),
    )
    connection.execute(
        "INSERT INTO lease (id, unit_id, tenant_id, owner_id, start_date, is_active, "
        "created_at, updated_at) VALUES (1, 1, 1, 1, '2024-01-01', 1, ?, ?)",
        (now, now),
    )
    for invoice_id, period, issue_date in [
        (1, "2024-01", "2024-01-01"),
        (2, "2024-02", "2024-02-01"),
        (3, "2025-01", "2025-01-01"),
    ]:
        connection.execute(
            "INSERT INTO invoice (id, period, lease_id, issue_date, status, total_base, "
            "total_vat, total_irpf_withholding, total, created_at, updated_at) "
            "VALUES (?, ?, 1, ?, 'issued', 850, 0, 0, 850, ?, ?)",
            (invoice_id, period, issue_date, now, now),
        )
    connection.commit()
    connection.close()

    command.upgrade(config, "head")

    connection = sqlite3.connect(db_path)
    rows = connection.execute(
        "SELECT id, series, fiscal_year, sequence, number, due_date, issuer_name, "
        "recipient_name FROM invoice ORDER BY id"
    ).fetchall()
    assert rows == [
        (1, "A", 2024, 1, "A-2024-0001", "2024-01-31", "Legacy Owner", "Legacy Tenant"),
        (2, "A", 2024, 2, "A-2024-0002", "2024-03-02", "Legacy Owner", "Legacy Tenant"),
        (3, "A", 2025, 1, "A-2025-0001", "2025-01-31", "Legacy Owner", "Legacy Tenant"),
    ]

    tenant_columns = {
        row[1] for row in connection.execute("PRAGMA table_info(tenant)")
    }
    assert "address" in tenant_columns
    owner_columns = {row[1] for row in connection.execute("PRAGMA table_info(owner)")}
    assert "iban" in owner_columns

    period_index_sql = connection.execute(
        "SELECT sql FROM sqlite_master WHERE name = 'uq_invoice_lease_period_active'"
    ).fetchone()[0]
    assert "corrected_invoice_id" in period_index_sql
    number_index_sql = connection.execute(
        "SELECT sql FROM sqlite_master WHERE name = 'uq_invoice_number_active'"
    ).fetchone()[0]
    assert "number" in number_index_sql
    connection.close()
