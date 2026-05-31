from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.api.deps import verify_api_key
from app.database import get_session
from app.models.owner import Owner

router = APIRouter(
    prefix="/owners",
    tags=["owners"],
    dependencies=[Depends(verify_api_key)],
)


@router.get("")
def list_owners(session: Session = Depends(get_session)):
    return session.exec(select(Owner).where(Owner.deleted_at.is_(None))).all()
