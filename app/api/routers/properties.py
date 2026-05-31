from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.api.deps import verify_api_key
from app.api.schemas import PropertyCreate, PropertyUpdate
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


@router.get("/{property_id}")
def get_property(property_id: int, session: Session = Depends(get_session)):
    prop = session.get(Property, property_id)
    if prop is None or prop.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop


@router.post("", status_code=201)
def create_property(body: PropertyCreate, session: Session = Depends(get_session)):
    prop = Property(**body.model_dump())
    session.add(prop)
    session.commit()
    session.refresh(prop)
    return prop


@router.put("/{property_id}")
def update_property(property_id: int, body: PropertyUpdate, session: Session = Depends(get_session)):
    prop = session.get(Property, property_id)
    if prop is None or prop.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Property not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(prop, field, value)
    session.add(prop)
    session.commit()
    session.refresh(prop)
    return prop
