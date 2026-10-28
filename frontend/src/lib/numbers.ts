/** Conversions between stored decimal strings and what users type. Kept free of React for testing. */

const PLAIN_NUMBER = /^-?(\d+\.?\d*|\.\d+)$/

export function isNumeric(text: string): boolean {
  return PLAIN_NUMBER.test(text.trim())
}

/** Round to 6 decimal places and drop trailing zeros, removing binary-float noise (0.07*100). */
function clean(value: number): string {
  const rounded = Number(value.toFixed(6))
  return Object.is(rounded, -0) ? '0' : String(rounded)
}

export const fractionToPercentText = (fraction: string): string => clean(Number(fraction) * 100)

export const percentTextToFraction = (percent: string): string => clean(Number(percent) / 100)

const WHOLE = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0, minimumFractionDigits: 0 })

/** Accounting style: thousands separators, negatives in parentheses. */
export function formatAmount(value: string): string {
  const n = Number(value)
  if (!Number.isFinite(n)) return '–'
  const text = WHOLE.format(Math.abs(n))
  return n < 0 && text !== '0' ? `(${text})` : text
}
