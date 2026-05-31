from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.api.deps import verify_api_key
from app.database import get_session
from app.models.property import Property

router = APIRouter(
    prefix="/properties",
    tags=["properties"],
    dependencies=[Depends(verify_api_key)],
)


@router.get("")
def list_properties(session: Session = Depends(get_session)):
    return session.exec(select(Property).where(Property.deleted_at.is_(None))).all()
