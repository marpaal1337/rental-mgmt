from pathlib import Path

from app.services.backup_service import BackupService


class TestBackupService:
    def test_backup_creates_file(self):
        path = BackupService.run_backup()
        assert Path(path).exists()
        assert Path(path).suffix == ".db"

    def test_clean_old_backups(self, tmp_path: Path):
        import os
        from datetime import UTC, datetime, timedelta

        for days_ago in [1, 5, 10, 15]:
            f = tmp_path / f"rental_{datetime.now(UTC).strftime('%Y%m%d')}_{days_ago}.db"
            f.write_text("test")
            mtime = (datetime.now(UTC) - timedelta(days=days_ago)).timestamp()
            os.utime(str(f), (mtime, mtime))

        from unittest.mock import patch

        with patch("app.services.backup_service.BACKUP_DIR", str(tmp_path)):
            removed = BackupService.clean_old_backups(retention_days=7)

        assert removed == 2
        remaining = list(tmp_path.glob("rental_*.db"))
        assert len(remaining) == 2
