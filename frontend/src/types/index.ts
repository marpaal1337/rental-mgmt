export interface Owner {
  id: number
  name: string
  document_type: string
  document_number: string
  email: string
  phone: string
  address: string | null
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
  status: string
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
}

export interface InvoiceGeneratePayload {
  period: string
}
