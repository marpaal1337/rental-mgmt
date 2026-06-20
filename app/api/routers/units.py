from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.api.deps import verify_api_key
from app.api.schemas import UnitCreate, UnitUpdate
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


@router.get("/{unit_id}")
def get_unit(unit_id: int, session: Session = Depends(get_session)):
    unit = session.get(Unit, unit_id)
    if unit is None or unit.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Unit not found")
    return unit


@router.post("", status_code=201)
def create_unit(body: UnitCreate, session: Session = Depends(get_session)):
    unit = Unit(**body.model_dump())
    session.add(unit)
    session.commit()
    session.refresh(unit)
    return unit


@router.put("/{unit_id}")
def update_unit(unit_id: int, body: UnitUpdate, session: Session = Depends(get_session)):
    unit = session.get(Unit, unit_id)
    if unit is None or unit.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Unit not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(unit, field, value)
    unit.updated_at = datetime.now(UTC)
    session.add(unit)
    session.commit()
    session.refresh(unit)
    return unit


@router.delete("/{unit_id}")
def delete_unit(unit_id: int, session: Session = Depends(get_session)):
    unit = session.get(Unit, unit_id)
    if unit is None or unit.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Unit not found")
    unit.deleted_at = datetime.now(UTC)
    session.commit()
    return {"detail": "Unit deleted"}
