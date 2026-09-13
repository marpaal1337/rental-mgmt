from datetime import UTC, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.api.deps import verify_api_key
from app.api.schemas import ExpenseCreate, ExpenseUpdate
from app.database import get_session
from app.models.expense import EXPENSE_CATEGORIES
from app.models.expense import Expense as ExpenseModel
from app.services.expense_service import ExpenseError, ExpenseService

router = APIRouter(
    prefix="/expenses",
    tags=["expenses"],
    dependencies=[Depends(verify_api_key)],
)


@router.get("")
def list_expenses(
    property_id: Optional[int] = Query(None),
    year: Optional[int] = Query(None),
    session: Session = Depends(get_session),
):
    try:
        return ExpenseService.list_expenses(session, property_id, year)
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
            body.vat_rate,
        )
        session.commit()
        session.refresh(expense)
        return expense
    except ExpenseError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{expense_id}")
def update_expense(
    expense_id: int,
    body: ExpenseUpdate,
    session: Session = Depends(get_session),
):
    try:
        expense = ExpenseService.update(
            session, expense_id, **body.model_dump(exclude_unset=True)
        )
        session.commit()
        session.refresh(expense)
        return expense
    except ExpenseError as e:
        detail = str(e)
        status_code = 404 if "not found" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail)


@router.delete("/{expense_id}")
def delete_expense(expense_id: int, session: Session = Depends(get_session)):
    expense = session.get(ExpenseModel, expense_id)
    if expense is None or expense.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Expense not found")
    expense.deleted_at = datetime.now(UTC)
    session.commit()
    return {"detail": "Expense deleted"}


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
