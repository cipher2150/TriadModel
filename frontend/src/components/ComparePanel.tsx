import { SCENARIOS, type CalculationResult } from '../api/types'
import { formatAmount } from '../lib/numbers'

export function ComparePanel({ result }: { result: CalculationResult }) {
  const lastYear = result.scenarios.base.years[result.scenarios.base.years.length - 1]?.year
  const rows: { label: string; value: (name: (typeof SCENARIOS)[number]) => string }[] = [
    { label: `Revenue ${lastYear}`, value: (n) => formatAmount(last(result, n).income_statement.revenue ?? '') },
    { label: `Net income ${lastYear}`, value: (n) => formatAmount(last(result, n).income_statement.net_income ?? '') },
    { label: `Ending cash ${lastYear}`, value: (n) => formatAmount(last(result, n).balance_sheet.cash ?? '') },
    {
      label: 'Peak revolver balance',
      value: (n) =>
        formatAmount(String(Math.max(0, ...result.scenarios[n].years.map((y) => Number(y.balance_sheet.revolver))))),
    },
    {
      label: `Total debt ${lastYear}`,
      value: (n) => {
        const bs = last(result, n).balance_sheet
        return formatAmount(String(Number(bs.revolver) + Number(bs.term_loan)))
      },
    },
    {
      label: 'Errors / warnings',
      value: (n) => {
        const flags = result.scenarios[n].flags
        const errors = flags.filter((f) => f.severity === 'error').length
        return `${errors} / ${flags.length - errors}`
      },
    },
  ]
  return (
    <section aria-labelledby="compare-title" className="panel">
      <h2 id="compare-title">Scenario comparison</h2>
      <div className="table-scroll">
        <table>
          <caption className="sr-only">Key outputs for each scenario</caption>
          <thead>
            <tr>
              <th scope="col">Measure</th>
              {SCENARIOS.map((name) => (
                <th scope="col" key={name} className="num cap">
                  {name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.label}>
                <th scope="row">{row.label}</th>
                {SCENARIOS.map((name) => (
                  <td key={name} className="num">
                    {row.value(name)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function last(result: CalculationResult, name: (typeof SCENARIOS)[number]) {
  const years = result.scenarios[name].years
  return years[years.length - 1]
}
