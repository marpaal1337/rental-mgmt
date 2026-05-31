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


class LeaseUpdate(BaseModel):
    unit_id: Optional[int] = None
    tenant_id: Optional[int] = None
    owner_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class ExpenseUpdate(BaseModel):
    property_id: Optional[int] = None
    category: Optional[str] = None
    amount: Optional[Decimal] = None
    expense_date: Optional[date] = None
    lease_id: Optional[int] = None
    deductible: Optional[bool] = None
    supplier: Optional[str] = None
    invoice_number: Optional[str] = None
    notes: Optional[str] = None


class PaymentUpdate(BaseModel):
    amount: Optional[Decimal] = None
    payment_date: Optional[date] = None
    method: Optional[str] = None
    notes: Optional[str] = None


class OwnerCreate(BaseModel):
    name: str
    document_type: str
    document_number: str
    email: str
    phone: str
    address: Optional[str] = None


class OwnerUpdate(BaseModel):
    name: Optional[str] = None
    document_type: Optional[str] = None
    document_number: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class PropertyCreate(BaseModel):
    name: str
    address: str
    city: str
    province: str
    zip_code: str
    cadastral_ref: Optional[str] = None
    owner_id: int


class PropertyUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    zip_code: Optional[str] = None
    cadastral_ref: Optional[str] = None
    owner_id: Optional[int] = None


class UnitCreate(BaseModel):
    property_id: int
    name: str
    unit_type: str
    area_m2: Optional[float] = None
    is_active: bool = True


class UnitUpdate(BaseModel):
    property_id: Optional[int] = None
    name: Optional[str] = None
    unit_type: Optional[str] = None
    area_m2: Optional[float] = None
    is_active: Optional[bool] = None


class TenantCreate(BaseModel):
    name: str
    document_type: str
    document_number: str
    email: str
    phone: str


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    document_type: Optional[str] = None
    document_number: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class RentConditionCreate(BaseModel):
    start_date: date
    monthly_rent: Decimal
    notes: Optional[str] = None


class TaxProfileUpdate(BaseModel):
    vat_rate: Optional[Decimal] = None
    irpf_rate: Optional[Decimal] = None
    vat_exempt: Optional[bool] = None
    withholding_applies: Optional[bool] = None


class DepositCreate(BaseModel):
    amount: Decimal
    deposit_date: date
    agency: str
    return_date: Optional[date] = None


class DepositUpdate(BaseModel):
    amount: Optional[Decimal] = None
    deposit_date: Optional[date] = None
    agency: Optional[str] = None
    return_date: Optional[date] = None


class RentQueryParams(BaseModel):
    date: Optional[date] = None
