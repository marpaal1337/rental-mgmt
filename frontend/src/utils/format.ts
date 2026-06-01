export function fmtMoney(value: string | number): string {
  return `${parseFloat(String(value)).toFixed(2)} €`
}

export function fmtPercent(value: string | number): string {
  return `${(parseFloat(String(value)) * 100).toFixed(2)}%`
}

export function fmtPercentDirect(value: string | number): string {
  return `${parseFloat(String(value)).toFixed(2)}%`
}

export function fmtEmpty(value: string | null | undefined): string {
  return value ?? '-'
}
