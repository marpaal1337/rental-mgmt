from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.api.deps import verify_api_key
from app.database import get_session
from app.models.unit import Unit

router = APIRouter(
    prefix="/units",
    tags=["units"],
    dependencies=[Depends(verify_api_key)],
)


@router.get("")
def list_units(session: Session = Depends(get_session)):
    return session.exec(select(Unit).where(Unit.deleted_at.is_(None))).all()
