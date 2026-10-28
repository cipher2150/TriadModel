import { useState } from 'react'
import type { Flag, ScenarioResult, StatementsYear } from '../api/types'
import { formatAmount } from '../lib/numbers'
import { STATEMENT_LINES, STATEMENT_TITLES, type StatementKey } from '../lib/statements'

interface Props {
  historicals: StatementsYear[]
  forecast: ScenarioResult
  onTrace: (nodeKey: string) => void
  selectedNode: string | null
}

const KEYS = Object.keys(STATEMENT_TITLES) as StatementKey[]

export function StatementsTable({ historicals, forecast, onTrace, selectedNode }: Props) {
  const [statement, setStatement] = useState<StatementKey>('income_statement')
  const lastHistorical = historicals[historicals.length - 1]?.year ?? 0
  const columns = [
    ...historicals.map((year) => ({ year, forecast: false })),
    ...forecast.years.map((year) => ({ year, forecast: true })),
  ]
  const errorYears = new Set(forecast.flags.filter((f: Flag) => f.severity === 'error').map((f) => f.year))

  return (
    <section aria-labelledby="statements-title" className="panel">
      <h2 id="statements-title">Financial statements</h2>
      <div role="tablist" aria-label="Statement" className="tabs">
        {KEYS.map((key) => (
          <button
            key={key}
            role="tab"
            id={`tab-${key}`}
            aria-selected={statement === key}
            aria-controls="statement-panel"
            onClick={() => setStatement(key)}
          >
            {STATEMENT_TITLES[key]}
          </button>
        ))}
      </div>
      <div id="statement-panel" role="tabpanel" aria-labelledby={`tab-${statement}`} className="table-scroll">
        <table>
          <caption className="sr-only">
            {STATEMENT_TITLES[statement]}; columns after {lastHistorical} are forecast. Select a forecast figure to see
            how it was calculated.
          </caption>
          <thead>
            <tr>
              <th scope="col">Line</th>
              {columns.map(({ year, forecast: isForecast }) => (
                <th scope="col" key={year.year} className={`num${isForecast ? ' forecast' : ''}`}>
                  {year.year}
                  <span className="col-kind">{isForecast ? 'Forecast' : 'Actual'}</span>
                  {isForecast && errorYears.has(year.year) && <span className="col-flag"> ⚠ flagged</span>}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {STATEMENT_LINES[statement].map((line) => (
              <tr key={line.key} className={line.total ? 'total' : undefined}>
                <th scope="row">{line.label}</th>
                {columns.map(({ year, forecast: isForecast }) => {
                  const text = formatAmount(year[statement][line.key] ?? '')
                  const nodeKey = line.node ? `${line.node}@${year.year - lastHistorical}` : null
                  const traceable = isForecast && nodeKey !== null && forecast.trace?.[nodeKey] !== undefined
                  return (
                    <td key={year.year} className={`num${isForecast ? ' forecast' : ''}`}>
                      {traceable ? (
                        <button
                          className="trace-link"
                          aria-pressed={selectedNode === nodeKey}
                          aria-label={`${line.label} ${year.year}: ${text}. Show calculation`}
                          onClick={() => onTrace(nodeKey)}
                        >
                          {text}
                        </button>
                      ) : (
                        text
                      )}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
