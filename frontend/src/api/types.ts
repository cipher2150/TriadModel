/** Mirrors backend/app/schemas. Amounts are decimal strings; never convert to float for storage. */

export const SCENARIOS = ['base', 'upside', 'downside'] as const
export type ScenarioName = (typeof SCENARIOS)[number]

export type Money = string

export interface YearAssumptions {
  revenue_growth: string
  cogs_pct: string
  sga_pct: string
  depreciation_rate: string
  capex_pct: string
  dso: string
  dio: string
  dpo: string
  tax_rate: string
  term_loan_rate: string
  revolver_rate: string
  cash_yield: string
  term_loan_repayment: string
  min_cash: string
  revolver_limit: string
  dividend_payout: string
}

export interface ModelPayload {
  company_name: string
  is_demo: boolean
  /** Historical statements are displayed and sent back unchanged; the UI never edits them. */
  historicals: unknown[]
  scenarios: Record<ScenarioName, YearAssumptions[]>
  tolerance: string
}

export type StatementLines = Record<string, Money>

export interface StatementsYear {
  year: number
  income_statement: StatementLines
  balance_sheet: StatementLines
  cash_flow: StatementLines
}

export interface Flag {
  code: string
  severity: 'error' | 'warning'
  year: number
  message: string
  amount: Money
}

export interface TraceEntry {
  formula: string
  inputs: Record<string, Money>
  value: Money
}

export interface ScenarioResult {
  years: StatementsYear[]
  flags: Flag[]
  trace: Record<string, TraceEntry> | null
}

export interface CalculationResult {
  company_name: string
  is_demo: boolean
  historicals: StatementsYear[]
  scenarios: Record<ScenarioName, ScenarioResult>
}

export interface SavedModel {
  id: string
  version: number
  created_at: string
  updated_at: string
  model: ModelPayload
  result: CalculationResult
}

export interface CreatedModel extends SavedModel {
  write_token: string
}

export interface ErrorDetail {
  location: string
  message: string
}
