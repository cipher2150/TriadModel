import type { TraceEntry } from '../api/types'

export function TracePanel({
  nodeKey,
  entry,
  onClose,
}: {
  nodeKey: string | null
  entry: TraceEntry | undefined
  onClose: () => void
}) {
  return (
    <section aria-labelledby="trace-title" className="panel" aria-live="polite">
      <h2 id="trace-title">How a number was calculated</h2>
      {!nodeKey || !entry ? (
        <p className="hint">Select a forecast figure in the statements above to see its formula and inputs.</p>
      ) : (
        <>
          <p>
            <code>{nodeKey}</code> = <strong>{entry.value}</strong>
          </p>
          <p>
            Formula: <code>{entry.formula}</code>
          </p>
          {Object.keys(entry.inputs).length === 0 ? (
            <p className="hint">This is a starting balance taken from the last historical year.</p>
          ) : (
            <table>
              <caption className="sr-only">Inputs used</caption>
              <thead>
                <tr>
                  <th scope="col">Input</th>
                  <th scope="col" className="num">
                    Value
                  </th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(entry.inputs).map(([name, value]) => (
                  <tr key={name}>
                    <th scope="row">
                      <code>{name}</code>
                    </th>
                    <td className="num">{value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <button onClick={onClose}>Clear</button>
        </>
      )}
    </section>
  )
}
