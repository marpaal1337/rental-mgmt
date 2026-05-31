from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.api.deps import verify_api_key
from app.database import get_session
from app.models.tenant import Tenant

router = APIRouter(
    prefix="/tenants",
    tags=["tenants"],
    dependencies=[Depends(verify_api_key)],
)


@router.get("")
def list_tenants(session: Session = Depends(get_session)):
    return session.exec(select(Tenant).where(Tenant.deleted_at.is_(None))).all()
