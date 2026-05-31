import logging
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.config import BACKUP_DIR, DATABASE_URL

logger = logging.getLogger(__name__)


class BackupService:
    @staticmethod
    def _db_path() -> Path:
        path = DATABASE_URL.replace("sqlite:///", "")
        return Path(path).resolve()

    @staticmethod
    def run_backup() -> Path:
        db_path = BackupService._db_path()
        if not db_path.exists():
            raise FileNotFoundError(f"Database not found at {db_path}")

        backup_dir = Path(BACKUP_DIR)
        backup_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now(UTC)
        backup_name = f"rental_{now.strftime('%Y%m%d_%H%M%S')}.db"
        backup_path = backup_dir / backup_name

        shutil.copy2(str(db_path), str(backup_path))
        logger.info("Backup created: %s", backup_path)
        return backup_path

    @staticmethod
    def clean_old_backups(retention_days: int = 7) -> int:
        backup_dir = Path(BACKUP_DIR)
        if not backup_dir.exists():
            return 0

        cutoff = datetime.now(UTC) - timedelta(days=retention_days)
        removed = 0

        for f in backup_dir.glob("rental_*.db"):
            mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=UTC)
            if mtime < cutoff:
                f.unlink()
                removed += 1

        if removed:
            logger.info("Cleaned %d old backups (retention: %d days)", removed, retention_days)
        return removed
