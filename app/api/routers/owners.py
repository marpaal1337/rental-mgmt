from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.api.deps import verify_api_key
from app.api.schemas import OwnerCreate, OwnerUpdate
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


@router.get("/{owner_id}")
def get_owner(owner_id: int, session: Session = Depends(get_session)):
    owner = session.get(Owner, owner_id)
    if owner is None or owner.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Owner not found")
    return owner


@router.post("", status_code=201)
def create_owner(body: OwnerCreate, session: Session = Depends(get_session)):
    owner = Owner(**body.model_dump())
    session.add(owner)
    session.commit()
    session.refresh(owner)
    return owner


@router.put("/{owner_id}")
def update_owner(owner_id: int, body: OwnerUpdate, session: Session = Depends(get_session)):
    owner = session.get(Owner, owner_id)
    if owner is None or owner.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Owner not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(owner, field, value)
    session.add(owner)
    session.commit()
    session.refresh(owner)
    return owner
