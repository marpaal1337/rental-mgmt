export interface Owner {
  id: number
  name: string
  document_type: string
  document_number: string
  email: string
  phone: string
  address: string | null
  iban: string | null
}

export interface Property {
  id: number
  name: string
  address: string
  city: string
  province: string
  zip_code: string
  cadastral_ref: string | null
  owner_id: number
}

export interface Unit {
  id: number
  property_id: number
  name: string
  unit_type: string
  area_m2: number | null
  is_active: boolean
}

export interface Tenant {
  id: number
  name: string
  document_type: string
  document_number: string
  email: string
  phone: string
  address: string | null
}

export interface Lease {
  id: number
  unit_id: number
  tenant_id: number
  owner_id: number
  start_date: string
  end_date: string | null
  is_active: boolean
  notes: string | null
  tenant_name?: string
  owner_name?: string
  unit_name?: string
  tenant?: Tenant
  owner?: Owner
  unit?: Unit
}

export interface InvoiceLine {
  id: number
  invoice_id: number
  concept: string
  base_amount: string
  vat_rate: string
  vat_amount: string
  irpf_rate: string
  irpf_withholding: string
}

export interface Invoice {
  id: number
  period: string
  lease_id: number
  issue_date: string
  due_date: string | null
  status: string
  series: string
  sequence: number | null
  number: string | null
  fiscal_year: number | null
  corrected_invoice_id: number | null
  rectification_reason: string | null
  total_base: string
  total_vat: string
  total_irpf_withholding: string
  total: string
  notes: string | null
  lines?: InvoiceLine[]
  lease?: Lease
}

export interface Payment {
  id: number
  invoice_id: number
  amount: string
  payment_date: string
  method: string
  notes: string | null
  invoice?: Invoice
}

export interface Expense {
  id: number
  property_id: number
  lease_id: number | null
  category: string
  amount: string
  vat_rate: string
  vat_amount: string
  expense_date: string
  deductible: boolean
  supplier: string | null
  invoice_number: string | null
  notes: string | null
}

export interface DashboardStats {
  active_leases: number
  month_invoices: number
  month_payments: number
  year_expenses: number
}

export interface LeaseCreatePayload {
  unit_id: number
  tenant_id: number
  owner_id: number
  start_date: string
  end_date?: string | null
  notes?: string | null
}

export interface LeaseUpdatePayload {
  unit_id?: number
  tenant_id?: number
  owner_id?: number
  start_date?: string
  end_date?: string | null
  is_active?: boolean
  notes?: string | null
}

export interface PaymentCreatePayload {
  invoice_id: number
  amount: string
  payment_date: string
  method: string
  notes?: string | null
}

export interface PaymentUpdatePayload {
  amount?: string
  payment_date?: string
  method?: string
  notes?: string | null
}

export interface ExpenseCreatePayload {
  property_id: number
  category: string
  amount: string
  expense_date: string
  lease_id?: number | null
  deductible?: boolean
  supplier?: string | null
  invoice_number?: string | null
  notes?: string | null
  vat_rate?: string | null
}

export interface ExpenseUpdatePayload {
  property_id?: number
  category?: string
  amount?: string
  expense_date?: string
  lease_id?: number | null
  deductible?: boolean
  supplier?: string | null
  invoice_number?: string | null
  notes?: string | null
  vat_rate?: string | null
}

export interface InvoiceGeneratePayload {
  period: string
}

export interface InvoiceRectifyPayload {
  reason: string
}

export interface OwnerCreatePayload {
  name: string
  document_type: string
  document_number: string
  email: string
  phone: string
  address?: string | null
  iban?: string | null
}

export interface OwnerUpdatePayload {
  name?: string
  document_type?: string
  document_number?: string
  email?: string
  phone?: string
  address?: string | null
  iban?: string | null
}

export interface PropertyCreatePayload {
  name: string
  address: string
  city: string
  province: string
  zip_code: string
  cadastral_ref?: string | null
  owner_id: number
}

export interface PropertyUpdatePayload {
  name?: string
  address?: string
  city?: string
  province?: string
  zip_code?: string
  cadastral_ref?: string | null
  owner_id?: number
}

export interface UnitCreatePayload {
  property_id: number
  name: string
  unit_type: string
  area_m2?: number | null
  is_active?: boolean
}

export interface UnitUpdatePayload {
  property_id?: number
  name?: string
  unit_type?: string
  area_m2?: number | null
  is_active?: boolean
}

export interface TenantCreatePayload {
  name: string
  document_type: string
  document_number: string
  email: string
  phone: string
  address?: string | null
}

export interface TenantUpdatePayload {
  name?: string
  document_type?: string
  document_number?: string
  email?: string
  phone?: string
  address?: string | null
}

export interface RentCondition {
  id: number
  lease_id: number
  start_date: string
  monthly_rent: string
  notes: string | null
}

export interface RentConditionCreatePayload {
  start_date: string
  monthly_rent: string
  notes?: string | null
}

export interface TaxProfile {
  id: number
  lease_id: number
  vat_rate: string
  irpf_rate: string
  vat_exempt: boolean
  withholding_applies: boolean
}

export interface TaxProfileUpdatePayload {
  vat_rate?: string
  irpf_rate?: string
  vat_exempt?: boolean
  withholding_applies?: boolean
}

export interface Deposit {
  id: number
  lease_id: number
  amount: string
  deposit_date: string
  agency: string
  return_date: string | null
}

export interface DepositUpdatePayload {
  amount?: string
  deposit_date?: string
  agency?: string
  return_date?: string | null
}

export interface IndexUpdate {
  id: number
  lease_id: number
  application_date: string
  previous_rent: string
  new_rent: string
  index_rate: string
  index_name: string
  notes: string | null
}

export interface BankMovement {
  id: number
  entry_date: string
  value_date: string | null
  amount: string
  concept: string
  iban_origin: string | null
  reference: string | null
  status: string
}

export interface Reconciliation {
  id: number
  bank_movement_id: number
  payment_id: number
  score: string
  confirmed_at: string | null
  notes: string | null
  bank_movement?: BankMovement
  payment?: Payment
}

export interface ExpenseSummary {
  property_id: number
  year: number
  total_income: string
  total_expenses: string
  deductible_expenses: string
  non_deductible_expenses: string
  net_profitability: string
  by_category: Record<string, string>
}

export interface FiscalVatRow {
  vat_rate: string
  base: string
  vat: string
}

export interface FiscalVatReport {
  year: number
  quarter: number
  label: string
  date_from: string
  date_to: string
  criteria: string
  output: FiscalVatRow[]
  exempt: { base: string }
  input: FiscalVatRow[]
  totals: {
    output_base: string
    output_vat: string
    exempt_base: string
    input_base: string
    input_vat: string
    vat_due: string
  }
}

export interface FiscalWithholdingRow {
  recipient_name: string
  recipient_document_type: string | null
  recipient_document_number: string | null
  invoice_count: number
  base: string
  withholding: string
}

export interface FiscalWithholdingsReport {
  year: number
  criteria: string
  rows: FiscalWithholdingRow[]
  totals: {
    base: string
    withholding: string
  }
}

export interface FiscalIncomeRow {
  property_id: number
  property_name: string
  owner_id: number
  owner_name: string
  invoice_count: number
  gross_income: string
  deductible_expenses: string
  non_deductible_expenses: string
  net_income: string
  by_category: Record<string, string>
}

export interface FiscalIncomeReport {
  year: number
  criteria: string
  rows: FiscalIncomeRow[]
  totals: {
    gross_income: string
    deductible_expenses: string
    non_deductible_expenses: string
    net_income: string
  }
}
