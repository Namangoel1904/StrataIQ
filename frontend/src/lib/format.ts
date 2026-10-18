export function inr(val: number | string | undefined | null): string {
  if (val === undefined || val === null || val === '') return '₹0'
  const num = typeof val === 'string' ? parseFloat(val) : val
  if (isNaN(num)) return '₹0'
  return `₹${num.toLocaleString('en-IN')}`
}

export function inrCompact(val: number | string | undefined | null): string {
  if (val === undefined || val === null || val === '') return '–'
  const num = typeof val === 'string' ? parseFloat(val) : val
  if (isNaN(num)) return '–'
  const abs = Math.abs(num)
  if (abs >= 10000000) {
    const cr = num / 10000000
    return `₹${cr % 1 === 0 ? cr.toFixed(0) : cr.toFixed(2)} Cr`
  }
  if (abs >= 100000) {
    const l = num / 100000
    return `₹${l % 1 === 0 ? l.toFixed(0) : l.toFixed(1)}L`
  }
  if (abs >= 1000) {
    const k = num / 1000
    return `₹${k % 1 === 0 ? k.toFixed(0) : k.toFixed(1)}k`
  }
  return `₹${num.toLocaleString('en-IN')}`
}

export function humanize(str: string | undefined | null): string {
  if (!str) return ''
  return str
    .replace(/[_-]+/g, ' ')
    .trim()
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

export function prettyDocName(filename: string | undefined | null): string {
  if (!filename) return ''
  // E.g. "05_Q3_Q4_Insurance_Premium_Cost_Impact_Ledger.csv" -> "Q3-Q4 Insurance Premium Cost Impact Ledger"
  const base = filename.replace(/\.[^/.]+$/, '')
  return base
    .replace(/^\d+[\s_-]*/, '')
    .replace(/_/g, ' ')
    .replace(/Transcript /g, 'Transcript: ')
    .trim()
}

export function firstName(fullName: string | undefined | null): string {
  if (!fullName) return ''
  return fullName.trim().split(/\s+/)[0]
}

export function greeting(): string {
  const hr = new Date().getHours()
  if (hr < 12) return 'Good morning'
  if (hr < 17) return 'Good afternoon'
  return 'Good evening'
}
