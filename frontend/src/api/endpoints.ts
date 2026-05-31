import type {
  DashboardStats,
  Expense,
  ExpenseCreatePayload,
  ExpenseUpdatePayload,
  Invoice,
  InvoiceGeneratePayload,
  Lease,
  LeaseCreatePayload,
  LeaseUpdatePayload,
  Owner,
  Payment,
  PaymentCreatePayload,
  PaymentUpdatePayload,
  Property,
  Tenant,
  Unit,
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

export async function createLease(payload: LeaseCreatePayload): Promise<Lease> {
  const { data } = await client.post('/leases', payload)
  return data
}

export async function updateLease(id: number, payload: LeaseUpdatePayload): Promise<Lease> {
  const { data } = await client.put(`/leases/${id}`, payload)
  return data
}

export async function fetchInvoices(): Promise<Invoice[]> {
  const { data } = await client.get('/invoices')
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

export async function fetchOwners(): Promise<Owner[]> {
  const { data } = await client.get('/owners')
  return data
}

export async function fetchTenants(): Promise<Tenant[]> {
  const { data } = await client.get('/tenants')
  return data
}

export async function fetchProperties(): Promise<Property[]> {
  const { data } = await client.get('/properties')
  return data
}

export async function fetchUnits(): Promise<Unit[]> {
  const { data } = await client.get('/units')
  return data
}
