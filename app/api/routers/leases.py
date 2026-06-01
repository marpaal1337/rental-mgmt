from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.api.deps import verify_api_key
from app.api.schemas import (
    DepositUpdate,
    IndexApplyRequest,
    LeaseCreate,
    LeaseUpdate,
    RentConditionCreate,
    TaxProfileUpdate,
)
from app.database import get_session
from app.models.lease import Deposit, IndexUpdate, Lease, RentCondition, TaxProfile
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
        session.commit()
        session.refresh(cond)
        session.refresh(update)
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


def _get_lease_or_404(session: Session, lease_id: int) -> Lease:
    lease = session.get(Lease, lease_id)
    if lease is None or lease.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Lease not found")
    return lease


@router.get("/{lease_id}/rent-conditions")
def list_rent_conditions(lease_id: int, session: Session = Depends(get_session)):
    _get_lease_or_404(session, lease_id)
    return session.exec(
        select(RentCondition).where(
            RentCondition.lease_id == lease_id,
            RentCondition.deleted_at.is_(None),
        ).order_by(RentCondition.start_date.desc())
    ).all()


@router.post("/{lease_id}/rent-conditions", status_code=201)
def create_rent_condition(
    lease_id: int,
    body: RentConditionCreate,
    session: Session = Depends(get_session),
):
    _get_lease_or_404(session, lease_id)
    cond = RentCondition(lease_id=lease_id, **body.model_dump())
    session.add(cond)
    session.commit()
    session.refresh(cond)
    return cond


@router.get("/{lease_id}/tax-profile")
def get_tax_profile(lease_id: int, session: Session = Depends(get_session)):
    _get_lease_or_404(session, lease_id)
    profile = session.exec(
        select(TaxProfile).where(
            TaxProfile.lease_id == lease_id,
            TaxProfile.deleted_at.is_(None),
        )
    ).first()
    if profile is None:
        raise HTTPException(status_code=404, detail="Tax profile not found")
    return profile


@router.put("/{lease_id}/tax-profile")
def upsert_tax_profile(
    lease_id: int,
    body: TaxProfileUpdate,
    session: Session = Depends(get_session),
):
    _get_lease_or_404(session, lease_id)
    profile = session.exec(
        select(TaxProfile).where(
            TaxProfile.lease_id == lease_id,
            TaxProfile.deleted_at.is_(None),
        )
    ).first()
    if profile is None:
        profile = TaxProfile(lease_id=lease_id)
        session.add(profile)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    session.commit()
    session.refresh(profile)
    return profile


@router.get("/{lease_id}/deposit")
def get_deposit(lease_id: int, session: Session = Depends(get_session)):
    _get_lease_or_404(session, lease_id)
    deposit = session.exec(
        select(Deposit).where(
            Deposit.lease_id == lease_id,
            Deposit.deleted_at.is_(None),
        )
    ).first()
    if deposit is None:
        raise HTTPException(status_code=404, detail="Deposit not found")
    return deposit


@router.put("/{lease_id}/deposit")
def upsert_deposit(
    lease_id: int,
    body: DepositUpdate,
    session: Session = Depends(get_session),
):
    _get_lease_or_404(session, lease_id)
    deposit = session.exec(
        select(Deposit).where(
            Deposit.lease_id == lease_id,
            Deposit.deleted_at.is_(None),
        )
    ).first()
    if deposit is None:
        deposit = Deposit(lease_id=lease_id, amount=Decimal("0"), deposit_date=date.today(), agency="")
        session.add(deposit)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(deposit, field, value)
    session.commit()
    session.refresh(deposit)
    return deposit


@router.get("/{lease_id}/index-updates")
def list_index_updates(lease_id: int, session: Session = Depends(get_session)):
    _get_lease_or_404(session, lease_id)
    return session.exec(
        select(IndexUpdate).where(
            IndexUpdate.lease_id == lease_id,
            IndexUpdate.deleted_at.is_(None),
        ).order_by(IndexUpdate.application_date.desc())
    ).all()
