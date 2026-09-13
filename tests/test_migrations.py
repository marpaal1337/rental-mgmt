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
