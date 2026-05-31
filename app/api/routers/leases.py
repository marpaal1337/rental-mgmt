from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.api.deps import verify_api_key
from app.api.schemas import IndexApplyRequest, LeaseCreate, LeaseUpdate
from app.database import get_session
from app.models.lease import Lease
from app.services.index_update_service import IndexUpdateService
from app.services.lease_service import LeaseService, NoActiveRentError

router = APIRouter(
    prefix="/leases",
    tags=["leases"],
    dependencies=[Depends(verify_api_key)],
)


@router.get("")
def list_leases(session: Session = Depends(get_session)):
    return session.exec(
        select(Lease)
        .options(
            selectinload(Lease.tenant),
            selectinload(Lease.owner),
            selectinload(Lease.unit),
        )
        .where(Lease.deleted_at.is_(None))
    ).all()


@router.get("/{lease_id}")
def get_lease(lease_id: int, session: Session = Depends(get_session)):
    lease = session.get(Lease, lease_id)
    if lease is None or lease.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Lease not found")
    return lease


@router.post("", status_code=201)
def create_lease(
    body: LeaseCreate,
    session: Session = Depends(get_session),
):
    lease = Lease(**body.model_dump())
    session.add(lease)
    session.commit()
    session.refresh(lease)
    return lease


@router.put("/{lease_id}")
def update_lease(
    lease_id: int,
    body: LeaseUpdate,
    session: Session = Depends(get_session),
):
    lease = session.get(Lease, lease_id)
    if lease is None or lease.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Lease not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(lease, field, value)
    session.add(lease)
    session.commit()
    session.refresh(lease)
    return lease


@router.get("/{lease_id}/rent")
def get_active_rent(
    lease_id: int,
    target_date: Optional[date] = Query(None, alias="date"),
    session: Session = Depends(get_session),
):
    try:
        rent = LeaseService.get_active_rent(session, lease_id, target_date)
        return {
            "lease_id": lease_id,
            "rent": str(rent),
            "date": str(target_date or date.today()),
        }
    except NoActiveRentError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{lease_id}/apply-index")
def apply_index(
    lease_id: int,
    body: IndexApplyRequest,
    session: Session = Depends(get_session),
):
    try:
        cond, update = IndexUpdateService.apply_index(
            session,
            lease_id,
            body.index_rate,
            body.application_date,
            body.index_name,
            body.notes,
        )
        return {
            "rent_condition": {
                "id": cond.id,
                "monthly_rent": str(cond.monthly_rent),
            },
            "index_update": {
                "id": update.id,
                "index_rate": str(update.index_rate),
            },
        }
    except NoActiveRentError as e:
        raise HTTPException(status_code=404, detail=str(e))
