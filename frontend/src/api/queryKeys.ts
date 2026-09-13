export const queryKeys = {
  stats: ['stats'] as const,
  owners: ['owners'] as const,
  tenants: ['tenants'] as const,
  properties: ['properties'] as const,
  units: ['units'] as const,
  leases: ['leases'] as const,
  lease: (id: number) => ['leases', id] as const,
  rentConditions: (leaseId: number) => ['leases', leaseId, 'rent-conditions'] as const,
  indexUpdates: (leaseId: number) => ['leases', leaseId, 'index-updates'] as const,
  taxProfile: (leaseId: number) => ['leases', leaseId, 'tax-profile'] as const,
  deposit: (leaseId: number) => ['leases', leaseId, 'deposit'] as const,
  invoices: ['invoices'] as const,
  invoice: (id: number) => ['invoices', id] as const,
  payments: ['payments'] as const,
  expenses: (propertyId?: number, year?: number) =>
    ['expenses', propertyId ?? 'all', year ?? 'all'] as const,
  expenseSummary: (propertyId: number, year: number) =>
    ['expenses', 'summary', propertyId, year] as const,
  unmatchedMovements: ['reconciliation', 'unmatched'] as const,
  allMovements: ['reconciliation', 'movements'] as const,
}
