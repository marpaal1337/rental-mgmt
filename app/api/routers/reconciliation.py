import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlmodel import Session

from app.api.deps import verify_api_key
from app.database import get_session
from app.models.bank import BankMovement
from app.services.bank_adapter import INGBankAdapter
from app.services.reconciliation_service import ReconciliationError, ReconciliationService

router = APIRouter(
    prefix="/reconciliation",
    tags=["reconciliation"],
    dependencies=[Depends(verify_api_key)],
)


@router.post("/import", status_code=201)
def import_csv(file: UploadFile, session: Session = Depends(get_session)):
    content = file.file.read()
    suffix = Path(file.filename or "import.csv").suffix or ".csv"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    try:
        adapter = INGBankAdapter()
        movements = ReconciliationService.import_csv(session, tmp_path, adapter)
        session.commit()
        for m in movements:
            session.refresh(m)
        return movements
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@router.post("/{movement_id}/propose")
def propose_matches(
    movement_id: int,
    session: Session = Depends(get_session),
):
    try:
        recs = ReconciliationService.propose_matches(session, movement_id)
        session.commit()
        return recs
    except ReconciliationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/confirm/{reconciliation_id}")
def confirm_match(
    reconciliation_id: int,
    session: Session = Depends(get_session),
):
    try:
        rec = ReconciliationService.confirm_match(session, reconciliation_id)
        session.commit()
        session.refresh(rec)
        return rec
    except ReconciliationError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/unmatched")
def list_unmatched(session: Session = Depends(get_session)):
    return ReconciliationService.list_unmatched(session)


@router.get("/proposed")
def list_proposed(session: Session = Depends(get_session)):
    return ReconciliationService.list_proposed(session)


@router.get("/movements")
def list_movements(session: Session = Depends(get_session)):
    from sqlmodel import select

    return session.exec(select(BankMovement).where(BankMovement.deleted_at.is_(None))).all()
