import type { ScenarioName, YearAssumptions } from '../api/types'
import { ASSUMPTION_GROUPS } from '../lib/statements'
import { NumberCell } from './NumberCell'

interface Props {
  scenario: ScenarioName
  rows: YearAssumptions[]
  firstYear: number
  readOnly: boolean
  onEdit: (yearIndex: number, field: keyof YearAssumptions, value: string) => void
  onValidity: (cellId: string, valid: boolean) => void
  hasInvalid: boolean
}

export function AssumptionsPanel({ scenario, rows, firstYear, readOnly, onEdit, onValidity, hasInvalid }: Props) {
  return (
    <section aria-labelledby="assumptions-title" className="panel">
      <h2 id="assumptions-title">Assumptions — {scenario}</h2>
      <p className="hint">
        Percentages are entered as percent (8 = 8%). Edits recalculate all three statements.
        {readOnly && ' This model is view-only in this browser, so edits are not saved.'}
      </p>
      {hasInvalid && (
        <p role="alert" className="inline-error">
          Some values are not numbers. Calculation is paused until they are fixed.
        </p>
      )}
      <div className="table-scroll">
        <table>
          <caption className="sr-only">Forecast assumptions by year for the {scenario} scenario</caption>
          <thead>
            <tr>
              <th scope="col">Driver</th>
              {rows.map((_, index) => (
                <th scope="col" key={index} className="num">
                  {firstYear + index}
                </th>
              ))}
            </tr>
          </thead>
          {ASSUMPTION_GROUPS.map((group) => (
            <tbody key={group.title}>
              <tr className="group-row">
                <th scope="colgroup" colSpan={rows.length + 1}>
                  {group.title}
                </th>
              </tr>
              {group.rows.map((def) => (
                <tr key={def.key}>
                  <th scope="row">{def.label}</th>
                  {rows.map((row, index) => {
                    const cellId = `${scenario}.${index}.${def.key}`
                    return (
                      <td key={cellId} className="num">
                        <NumberCell
                          def={def}
                          year={firstYear + index}
                          value={row[def.key as keyof YearAssumptions]}
                          cellId={cellId}
                          onCommit={(value) => onEdit(index, def.key as keyof YearAssumptions, value)}
                          onValidity={onValidity}
                        />
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          ))}
        </table>
      </div>
    </section>
  )
}
