export const unitTypeLabels: Record<string, string> = {
  vivienda: 'Vivienda',
  local: 'Local',
  garage: 'Garaje',
  trastero: 'Trastero',
}

export const invoiceStatusColors: Record<string, string> = {
  draft: 'default',
  issued: 'blue',
  partial: 'orange',
  paid: 'green',
  cancelled: 'red',
}

export const invoiceStatusLabels: Record<string, string> = {
  draft: 'Borrador',
  issued: 'Emitida',
  partial: 'Parcial',
  paid: 'Pagada',
  cancelled: 'Anulada',
}

export const paymentMethodColors: Record<string, string> = {
  transferencia: 'blue',
  tarjeta: 'cyan',
  efectivo: 'green',
  domiciliacion: 'purple',
}

export const expenseCategoryLabels: Record<string, string> = {
  community: 'Comunidad',
  repairs: 'Reparaciones',
  supplies: 'Suministros',
  taxes: 'Impuestos',
  insurance: 'Seguros',
  admin_fees: 'Gastos gestión',
  other: 'Otros',
}

export const movementStatusColors: Record<string, string> = {
  unmatched: 'orange',
  proposed: 'blue',
  confirmed: 'green',
}

export const movementStatusLabels: Record<string, string> = {
  unmatched: 'Sin procesar',
  proposed: 'Propuesto',
  confirmed: 'Confirmado',
}
