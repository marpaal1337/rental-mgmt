import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _resolve_path(value: str, default_rel: str) -> str:
    if value.startswith("sqlite:///"):
        db_path = value[len("sqlite:///"):]
        if not Path(db_path).is_absolute():
            db_path = str(PROJECT_ROOT / db_path)
        return f"sqlite:///{db_path}"
    return value


DATABASE_URL: str = _resolve_path(
    os.getenv("DATABASE_URL", f"sqlite:///{PROJECT_ROOT / 'data/db/rental.db'}"),
    "data/db/rental.db",
)
BACKUP_DIR: str = os.getenv(
    "BACKUP_DIR",
    str(PROJECT_ROOT / "data/backups"),
)
if not os.path.isabs(BACKUP_DIR):
    BACKUP_DIR = str(PROJECT_ROOT / BACKUP_DIR)

SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
API_KEY: str = os.getenv("API_KEY", "dev-key-123")
