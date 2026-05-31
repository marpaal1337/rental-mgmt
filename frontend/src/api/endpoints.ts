import type {
  BankMovement,
  DashboardStats,
  Deposit,
  DepositUpdatePayload,
  Expense,
  ExpenseCreatePayload,
  ExpenseSummary,
  ExpenseUpdatePayload,
  IndexUpdate,
  Invoice,
  InvoiceGeneratePayload,
  Lease,
  LeaseCreatePayload,
  LeaseUpdatePayload,
  Owner,
  OwnerCreatePayload,
  OwnerUpdatePayload,
  Payment,
  PaymentCreatePayload,
  PaymentUpdatePayload,
  Property,
  PropertyCreatePayload,
  PropertyUpdatePayload,
  Reconciliation,
  RentCondition,
  RentConditionCreatePayload,
  TaxProfile,
  TaxProfileUpdatePayload,
  Tenant,
  TenantCreatePayload,
  TenantUpdatePayload,
  Unit,
  UnitCreatePayload,
  UnitUpdatePayload,
} from '../types'
import client from './client'

export async function fetchStats(): Promise<DashboardStats> {
  const { data } = await client.get('/stats')
  return data
}

export async function fetchLeases(): Promise<Lease[]> {
  const { data } = await client.get('/leases')
  return data
}

export async function fetchLease(id: number): Promise<Lease> {
  const { data } = await client.get(`/leases/${id}`)
  return data
}

export async function createLease(payload: LeaseCreatePayload): Promise<Lease> {
  const { data } = await client.post('/leases', payload)
  return data
}

export async function updateLease(id: number, payload: LeaseUpdatePayload): Promise<Lease> {
  const { data } = await client.put(`/leases/${id}`, payload)
  return data
}

export async function fetchLeaseRent(leaseId: number, date?: string): Promise<{ lease_id: number; rent: string; date: string }> {
  const params: Record<string, string> = {}
  if (date) params.date = date
  const { data } = await client.get(`/leases/${leaseId}/rent`, { params })
  return data
}

export async function applyIndex(
  leaseId: number,
  payload: { index_rate: string; application_date: string; index_name?: string; notes?: string | null }
): Promise<{ rent_condition: { id: number; monthly_rent: string }; index_update: { id: number; index_rate: string } }> {
  const { data } = await client.post(`/leases/${leaseId}/apply-index`, payload)
  return data
}

export async function fetchRentConditions(leaseId: number): Promise<RentCondition[]> {
  const { data } = await client.get(`/leases/${leaseId}/rent-conditions`)
  return data
}

export async function createRentCondition(leaseId: number, payload: RentConditionCreatePayload): Promise<RentCondition> {
  const { data } = await client.post(`/leases/${leaseId}/rent-conditions`, payload)
  return data
}

export async function fetchTaxProfile(leaseId: number): Promise<TaxProfile> {
  const { data } = await client.get(`/leases/${leaseId}/tax-profile`)
  return data
}

export async function upsertTaxProfile(leaseId: number, payload: TaxProfileUpdatePayload): Promise<TaxProfile> {
  const { data } = await client.put(`/leases/${leaseId}/tax-profile`, payload)
  return data
}

export async function fetchDeposit(leaseId: number): Promise<Deposit> {
  const { data } = await client.get(`/leases/${leaseId}/deposit`)
  return data
}

export async function upsertDeposit(leaseId: number, payload: DepositUpdatePayload): Promise<Deposit> {
  const { data } = await client.put(`/leases/${leaseId}/deposit`, payload)
  return data
}

export async function fetchIndexUpdates(leaseId: number): Promise<IndexUpdate[]> {
  const { data } = await client.get(`/leases/${leaseId}/index-updates`)
  return data
}

export async function fetchInvoices(): Promise<Invoice[]> {
  const { data } = await client.get('/invoices')
  return data
}

export async function fetchInvoice(id: number): Promise<Invoice> {
  const { data } = await client.get(`/invoices/${id}`)
  return data
}

export async function generateInvoices(payload: InvoiceGeneratePayload): Promise<Invoice[]> {
  const { data } = await client.post('/invoices/generate', payload)
  return data
}

export async function downloadInvoicePdf(id: number): Promise<void> {
  const res = await client.get(`/invoices/${id}/pdf`, { responseType: 'blob' })
  const blob = new Blob([res.data], { type: 'application/pdf' })
  const url = URL.createObjectURL(blob)
  window.open(url, '_blank')
  setTimeout(() => URL.revokeObjectURL(url), 60_000)
}

export async function fetchPayments(): Promise<Payment[]> {
  const { data } = await client.get('/payments')
  return data
}

export async function createPayment(payload: PaymentCreatePayload): Promise<Payment> {
  const { data } = await client.post('/payments', payload)
  return data
}

export async function updatePayment(id: number, payload: PaymentUpdatePayload): Promise<Payment> {
  const { data } = await client.put(`/payments/${id}`, payload)
  return data
}

export async function fetchExpenses(
  propertyId: number,
  year?: number
): Promise<Expense[]> {
  const params: Record<string, string> = { property_id: String(propertyId) }
  if (year) params.year = String(year)
  const { data } = await client.get('/expenses', { params })
  return data
}

export async function createExpense(payload: ExpenseCreatePayload): Promise<Expense> {
  const { data } = await client.post('/expenses', payload)
  return data
}

export async function updateExpense(id: number, payload: ExpenseUpdatePayload): Promise<Expense> {
  const { data } = await client.put(`/expenses/${id}`, payload)
  return data
}

export async function fetchExpenseCategories(): Promise<string[]> {
  const { data } = await client.get('/expenses/categories')
  return data.categories
}

export async function fetchExpenseSummary(propertyId: number, year: number): Promise<ExpenseSummary> {
  const { data } = await client.get('/expenses/summary', { params: { property_id: String(propertyId), year: String(year) } })
  return data
}

export async function fetchOwners(): Promise<Owner[]> {
  const { data } = await client.get('/owners')
  return data
}

export async function fetchOwner(id: number): Promise<Owner> {
  const { data } = await client.get(`/owners/${id}`)
  return data
}

export async function createOwner(payload: OwnerCreatePayload): Promise<Owner> {
  const { data } = await client.post('/owners', payload)
  return data
}

export async function updateOwner(id: number, payload: OwnerUpdatePayload): Promise<Owner> {
  const { data } = await client.put(`/owners/${id}`, payload)
  return data
}

export async function fetchProperties(): Promise<Property[]> {
  const { data } = await client.get('/properties')
  return data
}

export async function fetchProperty(id: number): Promise<Property> {
  const { data } = await client.get(`/properties/${id}`)
  return data
}

export async function createProperty(payload: PropertyCreatePayload): Promise<Property> {
  const { data } = await client.post('/properties', payload)
  return data
}

export async function updateProperty(id: number, payload: PropertyUpdatePayload): Promise<Property> {
  const { data } = await client.put(`/properties/${id}`, payload)
  return data
}

export async function fetchUnits(): Promise<Unit[]> {
  const { data } = await client.get('/units')
  return data
}

export async function fetchUnit(id: number): Promise<Unit> {
  const { data } = await client.get(`/units/${id}`)
  return data
}

export async function createUnit(payload: UnitCreatePayload): Promise<Unit> {
  const { data } = await client.post('/units', payload)
  return data
}

export async function updateUnit(id: number, payload: UnitUpdatePayload): Promise<Unit> {
  const { data } = await client.put(`/units/${id}`, payload)
  return data
}

export async function fetchTenants(): Promise<Tenant[]> {
  const { data } = await client.get('/tenants')
  return data
}

export async function fetchTenant(id: number): Promise<Tenant> {
  const { data } = await client.get(`/tenants/${id}`)
  return data
}

export async function createTenant(payload: TenantCreatePayload): Promise<Tenant> {
  const { data } = await client.post('/tenants', payload)
  return data
}

export async function updateTenant(id: number, payload: TenantUpdatePayload): Promise<Tenant> {
  const { data } = await client.put(`/tenants/${id}`, payload)
  return data
}

export async function importBankCsv(file: File): Promise<BankMovement[]> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await client.post('/reconciliation/import', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function proposeMatches(movementId: number): Promise<Reconciliation[]> {
  const { data } = await client.post(`/reconciliation/${movementId}/propose`)
  return data
}

export async function confirmMatch(reconciliationId: number): Promise<Reconciliation> {
  const { data } = await client.post(`/reconciliation/confirm/${reconciliationId}`)
  return data
}

export async function fetchUnmatchedMovements(): Promise<BankMovement[]> {
  const { data } = await client.get('/reconciliation/unmatched')
  return data
}

export async function fetchProposedMovements(): Promise<BankMovement[]> {
  const { data } = await client.get('/reconciliation/proposed')
  return data
}

export async function fetchAllMovements(): Promise<BankMovement[]> {
  const { data } = await client.get('/reconciliation/movements')
  return data
}
