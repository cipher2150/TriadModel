import { useCallback, useEffect, useRef, useState } from 'react'
import { api, ApiError } from '../api/client'
import type { CalculationResult, ModelPayload, ScenarioName, YearAssumptions } from '../api/types'
import { forgetToken, hashForModel, modelIdFromHash, readToken, storeToken } from '../lib/tokens'

export const RECALC_DELAY_MS = 250
export const SLOW_SERVER_MS = 3000

export interface SavedState {
  id: string
  version: number
  /** Null when this browser holds no write token: the model is view-only here. */
  token: string | null
}

export type Notice = { kind: 'info' | 'error'; text: string; details?: string[] } | null

export function toNotice(error: unknown): Notice {
  if (error instanceof ApiError) {
    return { kind: 'error', text: error.message, details: error.details.map((d) => `${d.location}: ${d.message}`) }
  }
  return { kind: 'error', text: 'Something went wrong. Please try again.' }
}

export function useModel() {
  const [payload, setPayload] = useState<ModelPayload | null>(null)
  const [result, setResult] = useState<CalculationResult | null>(null)
  const [scenario, setScenario] = useState<ScenarioName>('base')
  const [saved, setSaved] = useState<SavedState | null>(null)
  const [dirty, setDirty] = useState(false)
  const [calculating, setCalculating] = useState(false)
  const [slow, setSlow] = useState(false)
  const [notice, setNotice] = useState<Notice>(null)
  const [invalidCells, setInvalidCells] = useState<Set<string>>(new Set())
  const latestRequest = useRef(0)

  const adopt = useCallback((model: ModelPayload, calc: CalculationResult, state: SavedState | null) => {
    setPayload(model)
    setResult(calc)
    setSaved(state)
    setDirty(false)
    setInvalidCells(new Set())
    setNotice(null)
  }, [])

  const loadDemo = useCallback(async () => {
    try {
      const model = await api.demo()
      const calc = await api.calculate(model)
      adopt(model, calc, null)
      if (window.location.hash) history.replaceState(null, '', window.location.pathname)
    } catch (error) {
      setNotice(toNotice(error))
    }
  }, [adopt])

  const loadSaved = useCallback(
    async (id: string) => {
      try {
        const record = await api.load(id)
        adopt(record.model, record.result, { id, version: record.version, token: readToken(id) })
      } catch (error) {
        setNotice(toNotice(error))
      }
    },
    [adopt],
  )

  useEffect(() => {
    const id = modelIdFromHash(window.location.hash)
    let cancelled = false
    const bootstrap = async () => {
      try {
        const record = id ? await api.load(id) : null
        const model = record ? record.model : await api.demo()
        const calc = record ? record.result : await api.calculate(model)
        if (!cancelled) adopt(model, calc, id && record ? { id, version: record.version, token: readToken(id) } : null)
      } catch (error) {
        if (!cancelled) setNotice(toNotice(error))
      }
    }
    void bootstrap()
    return () => {
      cancelled = true
    }
  }, [adopt])

  // Debounced recalculation. Responses that arrive out of order are discarded.
  useEffect(() => {
    if (!payload || !dirty || invalidCells.size > 0) return
    const request = ++latestRequest.current
    const controller = new AbortController()
    const slowTimer = setTimeout(() => setSlow(true), SLOW_SERVER_MS)
    const timer = setTimeout(async () => {
      setCalculating(true)
      try {
        const calc = await api.calculate(payload, controller.signal)
        if (request === latestRequest.current) {
          setResult(calc)
          setNotice((current) => (current?.kind === 'error' ? null : current))
        }
      } catch (error) {
        if (error instanceof DOMException && error.name === 'AbortError') return
        if (request === latestRequest.current) setNotice(toNotice(error))
      } finally {
        clearTimeout(slowTimer)
        if (request === latestRequest.current) {
          setCalculating(false)
          setSlow(false)
        }
      }
    }, RECALC_DELAY_MS)
    return () => {
      clearTimeout(timer)
      clearTimeout(slowTimer)
      controller.abort()
    }
  }, [payload, dirty, invalidCells])

  const editAssumption = useCallback(
    (name: ScenarioName, yearIndex: number, field: keyof YearAssumptions, value: string) => {
      setPayload((current) => {
        if (!current) return current
        const rows = current.scenarios[name].map((row, index) =>
          index === yearIndex ? { ...row, [field]: value } : row,
        )
        return { ...current, scenarios: { ...current.scenarios, [name]: rows } }
      })
      setDirty(true)
    },
    [],
  )

  const markCellValidity = useCallback((cell: string, valid: boolean) => {
    setInvalidCells((current) => {
      if (valid === !current.has(cell)) return current
      const next = new Set(current)
      if (valid) next.delete(cell)
      else next.add(cell)
      return next
    })
  }, [])

  const importModel = useCallback(
    async (model: ModelPayload) => {
      try {
        adopt(model, await api.calculate(model), null)
        if (window.location.hash) history.replaceState(null, '', window.location.pathname)
        setDirty(true)
        setNotice({ kind: 'info', text: 'Model imported. It is not saved yet.' })
      } catch (error) {
        setNotice(toNotice(error))
      }
    },
    [adopt],
  )

  const save = useCallback(async () => {
    if (!payload) return
    try {
      if (!saved) {
        const created = await api.create(payload)
        const kept = storeToken(created.id, created.write_token)
        history.replaceState(null, '', hashForModel(created.id))
        adopt(created.model, created.result, { id: created.id, version: created.version, token: created.write_token })
        setNotice({
          kind: 'info',
          text: kept
            ? 'Saved. Anyone with this page’s link can view it; only this browser can edit it.'
            : 'Saved, but this browser could not store the edit token, so you will not be able to edit it later.',
        })
      } else if (saved.token) {
        const updated = await api.update(saved.id, saved.token, saved.version, payload)
        adopt(updated.model, updated.result, { ...saved, version: updated.version })
        setNotice({ kind: 'info', text: 'Changes saved.' })
      }
    } catch (error) {
      if (error instanceof ApiError && error.status === 403 && saved) forgetToken(saved.id)
      setNotice(toNotice(error))
    }
  }, [payload, saved, adopt])

  return {
    payload,
    result,
    scenario,
    setScenario,
    saved,
    dirty,
    calculating,
    slow,
    notice,
    dismissNotice: () => setNotice(null),
    invalidCells,
    editAssumption,
    markCellValidity,
    importModel,
    save,
    reloadSaved: () => (saved ? loadSaved(saved.id) : loadDemo()),
    loadDemo,
  }
}
