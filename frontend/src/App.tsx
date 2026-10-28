import { useState } from 'react'
import { AssumptionsPanel } from './components/AssumptionsPanel'
import { ComparePanel } from './components/ComparePanel'
import { FlagsPanel } from './components/FlagsPanel'
import { StatementsTable } from './components/StatementsTable'
import { Toolbar } from './components/Toolbar'
import { TracePanel } from './components/TracePanel'
import { useModel } from './state/useModel'

export default function App() {
  const model = useModel()
  const [traceNode, setTraceNode] = useState<string | null>(null)
  const [flash, setFlash] = useState<string | null>(null)
  const { payload, result, scenario, saved, notice } = model

  if (!payload || !result) {
    return (
      <main className="shell">
        <h1>TriadModel</h1>
        {notice ? (
          <div role="alert" className="notice error">
            <p>{notice.text}</p>
            <button onClick={() => void model.loadDemo()}>Load the demo company instead</button>
          </div>
        ) : (
          <p role="status">Loading… the server may take up to a minute to wake if it has been idle.</p>
        )}
      </main>
    )
  }

  const forecast = result.scenarios[scenario]
  const firstForecastYear = forecast.years[0]?.year ?? 0
  const readOnly = saved !== null && saved.token === null
  const message = flash ?? notice?.text

  return (
    <main className="shell">
      <header>
        <h1>TriadModel</h1>
        <p className="subtitle">
          {payload.company_name}
          {payload.is_demo && <span className="badge">Demo data</span>}
          {saved && (
            <span className="badge neutral">{readOnly ? 'Saved · view only' : `Saved · v${saved.version}`}</span>
          )}
          {model.dirty && <span className="badge neutral">{saved ? 'Unsaved changes' : 'Not saved'}</span>}
        </p>
      </header>

      <Toolbar
        scenario={scenario}
        onScenario={model.setScenario}
        saved={saved}
        dirty={model.dirty}
        payload={payload}
        onSave={() => void model.save()}
        onImport={(imported) => void model.importModel(imported)}
        onImportError={(text) => setFlash(text)}
        onReset={() => void model.reloadSaved()}
        onCopied={(ok) => setFlash(ok ? 'Link copied.' : 'Could not copy automatically; copy the address bar instead.')}
      />

      <div aria-live="polite" className="status-line">
        {model.calculating && (
          <span>{model.slow ? 'Waking the server, this can take a minute…' : 'Recalculating…'}</span>
        )}
      </div>

      {message && (
        <div
          role={notice?.kind === 'error' ? 'alert' : 'status'}
          className={`notice ${flash ? 'info' : (notice?.kind ?? 'info')}`}
        >
          <p>{message}</p>
          {!flash && notice?.details && notice.details.length > 0 && (
            <ul>
              {notice.details.slice(0, 5).map((detail) => (
                <li key={detail}>{detail}</li>
              ))}
            </ul>
          )}
          {notice?.text.includes('changed by someone else') && (
            <button onClick={() => void model.reloadSaved()}>Reload latest</button>
          )}
          <button
            onClick={() => {
              setFlash(null)
              model.dismissNotice()
            }}
          >
            Dismiss
          </button>
        </div>
      )}

      <div className="workspace">
        <div className="results">
          <FlagsPanel flags={forecast.flags} scenario={scenario} />
          <StatementsTable
            historicals={result.historicals}
            forecast={forecast}
            selectedNode={traceNode}
            onTrace={setTraceNode}
          />
          <TracePanel
            nodeKey={traceNode}
            entry={traceNode ? forecast.trace?.[traceNode] : undefined}
            onClose={() => setTraceNode(null)}
          />
          <ComparePanel result={result} />
        </div>
        <div className="drivers">
          <AssumptionsPanel
            scenario={scenario}
            rows={payload.scenarios[scenario]}
            firstYear={firstForecastYear}
            readOnly={readOnly}
            hasInvalid={model.invalidCells.size > 0}
            onEdit={(yearIndex, field, value) => model.editAssumption(scenario, yearIndex, field, value)}
            onValidity={model.markCellValidity}
          />
        </div>
      </div>
      <footer>
        <p>
          Figures in thousands of the reporting currency. Interest is calculated on opening balances; tax losses are not
          carried forward. Historical figures are shown as supplied.
        </p>
      </footer>
    </main>
  )
}
