import { vi } from 'vitest'
import demoPayload from './fixtures/demo-payload.json'
import demoResult from './fixtures/demo-result.json'
import type { CalculationResult, ModelPayload } from '../api/types'

export const payload = demoPayload as unknown as ModelPayload
export const baseResult = demoResult as unknown as CalculationResult

export interface RecordedCall {
  method: string
  url: string
  headers: Record<string, string>
  body: unknown
}

type Handler = (call: RecordedCall) => { status?: number; body?: unknown } | undefined

export const jsonResponse = (body: unknown, status = 200): Response =>
  new Response(status === 204 ? null : JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json' },
  })

export const errorBody = (code: string, message: string, details: unknown[] = []) => ({
  error: { code, message, details },
})

/** Installs a fake `fetch`. Unhandled routes get the default happy-path demo responses. */
export function installFakeApi(handler: Handler = () => undefined) {
  const calls: RecordedCall[] = []
  const fake = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const call: RecordedCall = {
      method: init?.method ?? 'GET',
      url: String(input),
      headers: (init?.headers ?? {}) as Record<string, string>,
      body: typeof init?.body === 'string' ? JSON.parse(init.body) : undefined,
    }
    calls.push(call)
    const override = handler(call)
    if (override) return jsonResponse(override.body, override.status ?? 200)
    if (call.url === '/api/demo') return jsonResponse(payload)
    if (call.url.startsWith('/api/calculate')) return jsonResponse(baseResult)
    return jsonResponse(errorBody('NOT_FOUND', 'No such route in fake API'), 404)
  })
  vi.stubGlobal('fetch', fake)
  return { calls, calculateCalls: () => calls.filter((c) => c.url.startsWith('/api/calculate')) }
}
