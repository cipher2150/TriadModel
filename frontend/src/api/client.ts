import type { CalculationResult, CreatedModel, ErrorDetail, ModelPayload, SavedModel } from './types'

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly details: ErrorDetail[]

  constructor(status: number, code: string, message: string, details: ErrorDetail[] = []) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(path, init)
  } catch (cause) {
    if (cause instanceof DOMException && cause.name === 'AbortError') throw cause
    throw new ApiError(0, 'NETWORK', 'Could not reach the server. Check your connection and retry.')
  }
  if (response.status === 204) return undefined as T
  const body: unknown = await response.json().catch(() => null)
  if (!response.ok) {
    const envelope = (body as { error?: { code?: string; message?: string; details?: ErrorDetail[] } } | null)?.error
    throw new ApiError(
      response.status,
      envelope?.code ?? 'HTTP_ERROR',
      envelope?.message ?? `Request failed (${response.status})`,
      envelope?.details ?? [],
    )
  }
  return body as T
}

const json = (method: string, body: unknown, headers: Record<string, string> = {}): RequestInit => ({
  method,
  headers: { 'content-type': 'application/json', ...headers },
  body: JSON.stringify(body),
})

export const api = {
  demo: () => request<ModelPayload>('/api/demo'),
  calculate: (payload: ModelPayload, signal?: AbortSignal) =>
    request<CalculationResult>('/api/calculate?include_trace=true', { ...json('POST', payload), signal }),
  create: (payload: ModelPayload) => request<CreatedModel>('/api/models', json('POST', payload)),
  load: (id: string) => request<SavedModel>(`/api/models/${encodeURIComponent(id)}`),
  update: (id: string, token: string, version: number, model: ModelPayload) =>
    request<SavedModel>(
      `/api/models/${encodeURIComponent(id)}`,
      json('PUT', { version, model }, { 'X-Write-Token': token }),
    ),
  csvUrl: (id: string, scenario: string) =>
    `/api/models/${encodeURIComponent(id)}/export?format=csv&scenario=${scenario}`,
}
