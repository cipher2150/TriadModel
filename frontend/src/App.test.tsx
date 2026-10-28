import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { CalculationResult, ModelPayload, SavedModel } from './api/types'
import App from './App'
import { formatAmount } from './lib/numbers'
import edited from './test/fixtures/edited-result.json'
import stressed from './test/fixtures/stressed-result.json'
import { baseResult, errorBody, installFakeApi, payload } from './test/fakeApi'

const ID = '11111111-2222-4333-8444-555555555555'
const editedResult = edited as unknown as CalculationResult
const stressedResult = stressed as unknown as CalculationResult

const revenue2025 = (result: CalculationResult) => formatAmount(result.scenarios.base.years[0].income_statement.revenue)

const saved = (version: number, model: ModelPayload = payload): SavedModel => ({
  id: ID,
  version,
  created_at: '2026-01-01T00:00:00+00:00',
  updated_at: '2026-01-01T00:00:00+00:00',
  model,
  result: baseResult,
})

afterEach(() => vi.unstubAllGlobals())

describe('loading', () => {
  it('shows the demo company, labelled as demo data, with all checks passing', async () => {
    installFakeApi()
    render(<App />)
    expect(await screen.findByText('Demo data')).toBeInTheDocument()
    expect(screen.getByText(/Demo Co \(illustrative data\)/)).toBeInTheDocument()
    expect(screen.getByText('All checks pass.')).toBeInTheDocument()
    expect(screen.getAllByRole('tab', { name: /base|upside|downside/i })).toHaveLength(3)
  })

  it('shows an error with a fallback when the server cannot be reached', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('network down')))
    render(<App />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Could not reach the server')
    expect(screen.getByRole('button', { name: /load the demo/i })).toBeInTheDocument()
  })

  it('loads a saved model from the link and is view-only without a token', async () => {
    window.location.hash = `#/m/${ID}`
    installFakeApi((call) => (call.url === `/api/models/${ID}` ? { body: saved(3) } : undefined))
    render(<App />)
    expect(await screen.findByText('Saved · view only')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /save changes/i })).toBeDisabled()
  })
})

describe('editing assumptions', () => {
  it('sends the edited assumption as a fraction and shows the recalculated statements', async () => {
    const api = installFakeApi((call) => {
      const body = call.body as ModelPayload | undefined
      if (call.url.startsWith('/api/calculate') && body?.scenarios.base[0].revenue_growth === '0.2') {
        return { body: editedResult }
      }
      return undefined
    })
    const user = userEvent.setup()
    render(<App />)
    await screen.findByText('Demo data')

    const cell = screen.getByLabelText('Revenue growth, 2025 (percent)')
    await user.clear(cell)
    await user.type(cell, '20')

    await waitFor(() =>
      expect(screen.getByLabelText(new RegExp(`Revenue 2025: ${revenue2025(editedResult)}\\.`))).toBeInTheDocument(),
    )
    const sent = api.calculateCalls().at(-1)?.body as ModelPayload
    expect(sent.scenarios.base[0].revenue_growth).toBe('0.2')
    expect(sent.scenarios.upside).toEqual(payload.scenarios.upside)
    expect(screen.getByText('Not saved')).toBeInTheDocument()
  })

  it('pauses calculation and marks the cell when the input is not a number', async () => {
    const api = installFakeApi()
    const user = userEvent.setup()
    render(<App />)
    await screen.findByText('Demo data')
    const callsBefore = api.calculateCalls().length

    const cell = screen.getByLabelText('Revenue growth, 2025 (percent)')
    await user.clear(cell)
    await user.type(cell, 'abc')

    expect(cell).toHaveAttribute('aria-invalid', 'true')
    expect(screen.getByRole('alert')).toHaveTextContent('Calculation is paused')
    await new Promise((resolve) => setTimeout(resolve, 400))
    expect(api.calculateCalls().length).toBe(callsBefore)
  })

  it('shows server validation problems with their location instead of hiding them', async () => {
    installFakeApi((call) => {
      const body = call.body as ModelPayload | undefined
      if (call.url.startsWith('/api/calculate') && body?.scenarios.base[0].tax_rate === '1.5') {
        return {
          status: 422,
          body: errorBody('VALIDATION_ERROR', 'Request validation failed', [
            { location: 'body.scenarios.base.0.tax_rate', message: 'Input should be less than or equal to 1' },
          ]),
        }
      }
      return undefined
    })
    const user = userEvent.setup()
    render(<App />)
    await screen.findByText('Demo data')
    const cell = screen.getByLabelText('Tax rate, 2025 (percent)')
    await user.clear(cell)
    await user.type(cell, '150')
    expect(
      await screen.findByText(/scenarios\.base\.0\.tax_rate: Input should be less than or equal to 1/),
    ).toBeInTheDocument()
  })
})

describe('flags', () => {
  it('names a cash shortfall and its year in text, not only colour', async () => {
    installFakeApi((call) =>
      call.url.startsWith('/api/calculate') && call.body ? { body: stressedResult } : undefined,
    )
    const user = userEvent.setup()
    render(<App />)
    await screen.findByText('Demo data')
    await user.type(screen.getByLabelText('Revenue growth, 2025 (percent)'), '1')

    const flags = await screen.findByRole('list', {}, { timeout: 2000 })
    expect(within(flags).getAllByText('Error').length).toBeGreaterThan(0)
    expect(within(flags).getAllByText(/Cash shortfall: revolver limit exceeded/).length).toBeGreaterThan(0)
    expect(screen.queryByText('All checks pass.')).not.toBeInTheDocument()
    expect(screen.getAllByText(/flagged/).length).toBeGreaterThan(0)
  })
})

describe('scenarios and tracing', () => {
  it('switches the assumptions panel to the chosen scenario', async () => {
    installFakeApi()
    const user = userEvent.setup()
    render(<App />)
    await screen.findByText('Demo data')
    await user.click(screen.getByRole('tab', { name: /^downside$/i }))
    expect(screen.getByRole('heading', { name: /Assumptions — downside/ })).toBeInTheDocument()
    const growth = screen.getByLabelText('Revenue growth, 2025 (percent)') as HTMLInputElement
    expect(growth.value).toBe('2') // 8% base - 6pp downside
  })

  it('explains a forecast figure with its formula and inputs', async () => {
    installFakeApi()
    const user = userEvent.setup()
    render(<App />)
    await screen.findByText('Demo data')
    await user.click(screen.getByLabelText(new RegExp(`^Revenue 2025: ${revenue2025(baseResult)}\\.`)))
    const panel = screen.getByRole('region', { name: /how a number was calculated/i })
    expect(within(panel).getByText('revenue@1')).toBeInTheDocument()
    expect(within(panel).getByText(/revenue@0 × \(1 \+ 0\.08\)/)).toBeInTheDocument()
  })

  it('shows all scenarios side by side', async () => {
    installFakeApi()
    render(<App />)
    await screen.findByText('Demo data')
    const table = screen.getByRole('table', { name: /key outputs for each scenario/i })
    expect(
      within(table)
        .getAllByRole('columnheader')
        .map((h) => h.textContent),
    ).toEqual(['Measure', 'base', 'upside', 'downside'])
  })
})

describe('saving', () => {
  it('creates the model, keeps the write token in this browser and sets a shareable link', async () => {
    installFakeApi((call) =>
      call.method === 'POST' && call.url === '/api/models'
        ? { status: 201, body: { ...saved(1), write_token: 'secret-token' } }
        : undefined,
    )
    const user = userEvent.setup()
    render(<App />)
    await screen.findByText('Demo data')
    await user.click(screen.getByRole('button', { name: 'Save model' }))
    expect(await screen.findByText('Saved · v1')).toBeInTheDocument()
    expect(localStorage.getItem(`triadmodel.token.${ID}`)).toBe('secret-token')
    expect(window.location.hash).toBe(`#/m/${ID}`)
    expect(screen.getByRole('status')).toHaveTextContent('only this browser can edit')
    expect(screen.getByRole('link', { name: 'Download CSV' })).toHaveAttribute(
      'href',
      expect.stringContaining(`/api/models/${ID}/export?format=csv`),
    )
  })

  it('updates with the write token and the version it was based on', async () => {
    localStorage.setItem(`triadmodel.token.${ID}`, 'secret-token')
    window.location.hash = `#/m/${ID}`
    const api = installFakeApi((call) => {
      if (call.url === `/api/models/${ID}` && call.method === 'GET') return { body: saved(4) }
      if (call.method === 'PUT') return { body: saved(5) }
      return undefined
    })
    const user = userEvent.setup()
    render(<App />)
    await screen.findByText('Saved · v4')
    await user.type(screen.getByLabelText('Revenue growth, 2025 (percent)'), '1')
    await user.click(await screen.findByRole('button', { name: 'Save changes' }))
    await screen.findByText('Saved · v5')

    const put = api.calls.find((c) => c.method === 'PUT')
    if (!put) throw new Error('expected a PUT request')
    expect(put.headers['X-Write-Token']).toBe('secret-token')
    expect((put.body as { version: number }).version).toBe(4)
  })

  it('offers to reload when someone else saved first', async () => {
    localStorage.setItem(`triadmodel.token.${ID}`, 'secret-token')
    window.location.hash = `#/m/${ID}`
    installFakeApi((call) => {
      if (call.url === `/api/models/${ID}` && call.method === 'GET') return { body: saved(2) }
      if (call.method === 'PUT') {
        return {
          status: 409,
          body: errorBody(
            'VERSION_CONFLICT',
            'The model was changed by someone else; reload it and reapply your edits',
          ),
        }
      }
      return undefined
    })
    const user = userEvent.setup()
    render(<App />)
    await screen.findByText('Saved · v2')
    await user.type(screen.getByLabelText('Revenue growth, 2025 (percent)'), '1')
    await user.click(await screen.findByRole('button', { name: 'Save changes' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('changed by someone else')
    expect(screen.getByRole('button', { name: 'Reload latest' })).toBeInTheDocument()
  })
})
