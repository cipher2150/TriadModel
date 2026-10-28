import { useRef } from 'react'
import { api } from '../api/client'
import type { ModelPayload, ScenarioName } from '../api/types'
import { SCENARIOS } from '../api/types'
import type { SavedState } from '../state/useModel'

export const MAX_IMPORT_BYTES = 1_000_000

interface Props {
  scenario: ScenarioName
  onScenario: (name: ScenarioName) => void
  saved: SavedState | null
  dirty: boolean
  payload: ModelPayload
  onSave: () => void
  onImport: (model: ModelPayload) => void
  onImportError: (message: string) => void
  onReset: () => void
  onCopied: (ok: boolean) => void
}

export function Toolbar(props: Props) {
  const { scenario, onScenario, saved, dirty, payload, onSave, onImport, onImportError, onReset, onCopied } = props
  const fileInput = useRef<HTMLInputElement>(null)
  const canSave = !saved || (saved.token !== null && dirty)

  const readFile = async (file: File) => {
    if (file.size > MAX_IMPORT_BYTES) return onImportError('That file is too large (limit 1 MB).')
    try {
      const parsed: unknown = JSON.parse(await file.text())
      if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) throw new Error('not an object')
      onImport(parsed as ModelPayload)
    } catch {
      onImportError('That file is not valid JSON for a TriadModel export.')
    }
  }

  const download = () => {
    const url = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' }))
    const link = document.createElement('a')
    link.href = url
    link.download = 'triadmodel.json'
    link.click()
    URL.revokeObjectURL(url)
  }

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href)
      onCopied(true)
    } catch {
      onCopied(false)
    }
  }

  return (
    <div className="toolbar">
      <div role="tablist" aria-label="Scenario" className="tabs scenario-tabs">
        {SCENARIOS.map((name) => (
          <button
            key={name}
            role="tab"
            aria-selected={scenario === name}
            onClick={() => onScenario(name)}
            className="cap"
          >
            {name}
          </button>
        ))}
      </div>
      <div className="actions">
        <button onClick={onSave} disabled={!canSave}>
          {saved ? 'Save changes' : 'Save model'}
        </button>
        {saved && <button onClick={copyLink}>Copy link</button>}
        {saved && (
          <a className="button" href={api.csvUrl(saved.id, scenario)} download>
            Download CSV
          </a>
        )}
        <button onClick={download}>Export JSON</button>
        <button onClick={() => fileInput.current?.click()}>Import JSON</button>
        <input
          ref={fileInput}
          type="file"
          accept="application/json,.json"
          hidden
          aria-label="Import model JSON file"
          onChange={(event) => {
            const file = event.target.files?.[0]
            if (file) void readFile(file)
            event.target.value = ''
          }}
        />
        <button onClick={onReset}>{saved ? 'Reload saved' : 'Reset to demo'}</button>
      </div>
    </div>
  )
}
