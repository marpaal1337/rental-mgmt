from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.api.deps import verify_api_key
from app.api.schemas import PaymentCreate
from app.database import get_session
from app.models.payment import Payment
from app.services.payment_service import PaymentError, PaymentService

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
        return payment
    except PaymentError as e:
        raise HTTPException(status_code=400, detail=str(e))
