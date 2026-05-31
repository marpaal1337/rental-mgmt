from typing import Optional

from sqlmodel import Session

from app.database import engine as _engine
from app.models.event_log import EventLog
from app.services.backup_service import BackupService


def daily_backup(session: Optional[Session] = None) -> dict:
    own_session = session is None
    if session is None:
        session = Session(_engine)

    try:
        path = BackupService.run_backup()
        cleaned = BackupService.clean_old_backups()

        log = EventLog(
            event_type="daily_backup",
            description=f"Backup created: {path.name}",
            details=f"path={path.name}, cleaned={cleaned}",
            level="info",
        )
        session.add(log)
        session.commit()

        return {"path": str(path), "cleaned": cleaned}
    finally:
        if own_session:
            session.close()
