import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _get_bundle_root() -> Path:
    """Where bundled files live (alembic, frontend, app code)."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def _get_data_root() -> Path:
    """Where persistent data lives (database, backups)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BUNDLE_ROOT = _get_bundle_root()
DATA_ROOT = _get_data_root()


def _resolve_path(value: str) -> str:
    if value.startswith("sqlite:///"):
        db_path = value[len("sqlite:///"):]
        if not Path(db_path).is_absolute():
            db_path = str(DATA_ROOT / db_path)
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path}"
    return value


DATABASE_URL: str = _resolve_path(
    os.getenv("DATABASE_URL", f"sqlite:///{DATA_ROOT / 'data/db/rental.db'}")
)
BACKUP_DIR: str = os.getenv(
    "BACKUP_DIR",
    str(DATA_ROOT / "data/backups"),
)
if not os.path.isabs(BACKUP_DIR):
    BACKUP_DIR = str(DATA_ROOT / BACKUP_DIR)

INVOICES_DIR: Path = Path(
    os.getenv("INVOICES_DIR", str(DATA_ROOT / "data/invoices"))
)
if not INVOICES_DIR.is_absolute():
    INVOICES_DIR = DATA_ROOT / INVOICES_DIR

API_KEY: str = os.getenv("API_KEY", "dev-key-123")
ENABLE_SCHEDULER: bool = os.getenv("ENABLE_SCHEDULER", "1") != "0"
INVOICE_PAYMENT_TERMS_DAYS: int = int(os.getenv("INVOICE_PAYMENT_TERMS_DAYS", "30"))
