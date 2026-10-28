import { useState } from 'react'
import { fractionToPercentText, isNumeric, percentTextToFraction } from '../lib/numbers'
import type { AssumptionDef } from '../lib/statements'

interface Props {
  def: AssumptionDef
  year: number
  value: string
  cellId: string
  onCommit: (value: string) => void
  onValidity: (cellId: string, valid: boolean) => void
}

/** A numeric input that keeps what the user is typing as a draft so partial input such as
 *  "8." or "-" is not rewritten. Only valid numbers are committed to the model. */
export function NumberCell({ def, year, value, cellId, onCommit, onValidity }: Props) {
  const [draft, setDraft] = useState<string | null>(null)
  const percent = def.kind === 'percent'
  const shown = draft ?? (percent ? fractionToPercentText(value) : value)
  const valid = draft === null || isNumeric(draft)

  const change = (text: string) => {
    setDraft(text)
    const ok = isNumeric(text)
    onValidity(cellId, ok)
    if (ok) onCommit(percent ? percentTextToFraction(text) : String(Number(text)))
  }

  return (
    <input
      className="cell-input"
      inputMode="decimal"
      value={shown}
      aria-label={`${def.label}, ${year}${percent ? ' (percent)' : def.kind === 'days' ? ' (days)' : ''}`}
      aria-invalid={!valid}
      onChange={(event) => change(event.target.value)}
      onBlur={() => {
        if (draft !== null && !isNumeric(draft)) onValidity(cellId, true)
        setDraft(null)
      }}
    />
  )
}
