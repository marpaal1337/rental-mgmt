from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class LeaseCreate(BaseModel):
    unit_id: int
    tenant_id: int
    owner_id: int
    start_date: date
    end_date: Optional[date] = None
    notes: Optional[str] = None


class InvoiceGenerateRequest(BaseModel):
    period: str


class PaymentCreate(BaseModel):
    invoice_id: int
    amount: Decimal
    payment_date: date
    method: str = "transferencia"
    notes: Optional[str] = None


class ExpenseCreate(BaseModel):
    property_id: int
    category: str
    amount: Decimal
    expense_date: date
    lease_id: Optional[int] = None
    deductible: bool = True
    supplier: Optional[str] = None
    invoice_number: Optional[str] = None
    notes: Optional[str] = None


class ExpenseSummaryParams(BaseModel):
    property_id: int
    year: int


class IndexApplyRequest(BaseModel):
    index_rate: Decimal
    application_date: date
    index_name: str = "IPC"
    notes: Optional[str] = None


class RentQueryParams(BaseModel):
    date: Optional[date] = None
