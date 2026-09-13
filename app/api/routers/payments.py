from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.api.deps import verify_api_key
from app.api.schemas import PaymentCreate, PaymentUpdate
from app.database import get_session
from app.models.payment import Payment
from app.services.payment_service import (
    PaymentError,
    PaymentNotFoundError,
    PaymentService,
)

router = APIRouter(
    prefix="/payments",
    tags=["payments"],
    dependencies=[Depends(verify_api_key)],
)


@router.get("")
def list_payments(session: Session = Depends(get_session)):
    return session.exec(select(Payment).where(Payment.deleted_at.is_(None))).all()


@router.post("", status_code=201)
def register_payment(
    body: PaymentCreate,
    session: Session = Depends(get_session),
):
    try:
        payment = PaymentService.register(
            session,
            body.invoice_id,
            body.amount,
            body.payment_date,
            body.method,
            body.notes,
        )
        session.commit()
        session.refresh(payment)
        return payment
    except PaymentError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{payment_id}")
def update_payment(
    payment_id: int,
    body: PaymentUpdate,
    session: Session = Depends(get_session),
):
    try:
        payment = PaymentService.update(
            session, payment_id, **body.model_dump(exclude_unset=True)
        )
        session.commit()
        session.refresh(payment)
        return payment
    except PaymentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PaymentError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{payment_id}")
def delete_payment(payment_id: int, session: Session = Depends(get_session)):
    try:
        PaymentService.delete(session, payment_id)
        session.commit()
        return {"detail": "Payment deleted"}
    except PaymentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
