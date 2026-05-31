from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.api.deps import verify_api_key
from app.api.schemas import ExpenseCreate
from app.database import get_session
from app.models.expense import EXPENSE_CATEGORIES
from app.services.expense_service import ExpenseError, ExpenseService

router = APIRouter(
    prefix="/expenses",
    tags=["expenses"],
    dependencies=[Depends(verify_api_key)],
)


@router.get("")
def list_expenses(
    property_id: int = Query(...),
    year: Optional[int] = Query(None),
    session: Session = Depends(get_session),
):
    try:
        return ExpenseService.list_by_property(session, property_id, year)
    except ExpenseError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("", status_code=201)
def register_expense(
    body: ExpenseCreate,
    session: Session = Depends(get_session),
):
    try:
        expense = ExpenseService.register(
            session,
            body.property_id,
            body.category,
            body.amount,
            body.expense_date,
            body.lease_id,
            body.deductible,
            body.supplier,
            body.invoice_number,
            body.notes,
        )
        return expense
    except ExpenseError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/categories")
def list_categories():
    return {"categories": EXPENSE_CATEGORIES}


@router.get("/summary")
def expense_summary(
    property_id: int = Query(...),
    year: int = Query(...),
    session: Session = Depends(get_session),
):
    try:
        return ExpenseService.summary(session, property_id, year)
    except ExpenseError as e:
        raise HTTPException(status_code=404, detail=str(e))
