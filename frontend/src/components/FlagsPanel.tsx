import type { Flag } from '../api/types'
import { formatAmount } from '../lib/numbers'

const LABELS: Record<string, string> = {
  BS_IMBALANCE: 'Balance sheet does not balance',
  CASH_TIE_OUT: 'Cash flow does not tie to cash balance',
  NI_TIE_OUT: 'Net income differs between statements',
  RE_ROLLFORWARD: 'Retained earnings roll-forward broken',
  PPE_ROLLFORWARD: 'PP&E roll-forward broken',
  DEBT_ROLLFORWARD: 'Debt roll-forward broken',
  REVOLVER_LIMIT_EXCEEDED: 'Cash shortfall: revolver limit exceeded',
  NEGATIVE_CASH: 'Negative cash',
  CASH_BELOW_MINIMUM: 'Cash below minimum',
  NEGATIVE_EQUITY: 'Negative equity',
}

export function FlagsPanel({ flags, scenario }: { flags: Flag[]; scenario: string }) {
  const errors = flags.filter((f) => f.severity === 'error').length
  return (
    <section aria-labelledby="flags-title" className="panel">
      <h2 id="flags-title">Checks and flags — {scenario}</h2>
      {flags.length === 0 ? (
        <p className="ok">
          <strong>All checks pass.</strong> Balance sheet balances, cash flow ties to cash, roll-forwards reconcile, and
          no cash shortfall is forecast.
        </p>
      ) : (
        <>
          <p role="status">
            {errors} error{errors === 1 ? '' : 's'}, {flags.length - errors} warning
            {flags.length - errors === 1 ? '' : 's'}.
          </p>
          <ul className="flags">
            {flags.map((flag, index) => (
              <li key={`${flag.code}-${flag.year}-${index}`} className={`flag ${flag.severity}`}>
                <span className="flag-badge">{flag.severity === 'error' ? 'Error' : 'Warning'}</span>
                <strong>{flag.year}</strong>
                <span>
                  {LABELS[flag.code] ?? flag.code}. {flag.message}{' '}
                  <span className="amount">({formatAmount(flag.amount)})</span>
                </span>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  )
}
