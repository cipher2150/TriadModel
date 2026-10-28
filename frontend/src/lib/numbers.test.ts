import { describe, expect, it } from 'vitest'
import { formatAmount, fractionToPercentText, isNumeric, percentTextToFraction } from './numbers'

describe('percent conversion', () => {
  it('removes binary float noise', () => {
    expect(fractionToPercentText('0.07')).toBe('7')
    expect(percentTextToFraction('7')).toBe('0.07')
    expect(percentTextToFraction('8.25')).toBe('0.0825')
  })
  it('round-trips typical drivers', () => {
    for (const fraction of ['0.08', '0.6', '0.21', '0.025', '-0.05', '0']) {
      expect(percentTextToFraction(fractionToPercentText(fraction))).toBe(String(Number(fraction)))
    }
  })
  it('never produces negative zero', () => {
    expect(percentTextToFraction('-0')).toBe('0')
  })
})

describe('isNumeric', () => {
  it.each(['1', '-1', '0.5', '.5', '5.', ' 7 '])('accepts %s', (text) => expect(isNumeric(text)).toBe(true))
  it.each(['', '-', '.', 'abc', '1e5', '1,000', 'NaN', 'Infinity', '--1'])('rejects %s', (text) =>
    expect(isNumeric(text)).toBe(false),
  )
})

describe('formatAmount', () => {
  it('uses separators and parentheses for negatives', () => {
    expect(formatAmount('1234567.4')).toBe('1,234,567')
    expect(formatAmount('-322.8')).toBe('(323)')
  })
  it('does not show negative zero', () => {
    expect(formatAmount('-0.2')).toBe('0')
  })
  it('shows a dash for non-numbers', () => {
    expect(formatAmount('abc')).toBe('–')
  })
})
