/** Display definitions for the three statements. `node` links a line to its calculation-graph key. */

export interface LineDef {
  key: string
  label: string
  total?: boolean
  node?: string
}

export type StatementKey = 'income_statement' | 'balance_sheet' | 'cash_flow'

export const STATEMENT_TITLES: Record<StatementKey, string> = {
  income_statement: 'Income statement',
  balance_sheet: 'Balance sheet',
  cash_flow: 'Cash flow',
}

export const STATEMENT_LINES: Record<StatementKey, LineDef[]> = {
  income_statement: [
    { key: 'revenue', label: 'Revenue', node: 'revenue' },
    { key: 'cogs', label: 'Cost of goods sold', node: 'cogs' },
    { key: 'gross_profit', label: 'Gross profit', total: true },
    { key: 'sga', label: 'SG&A', node: 'sga' },
    { key: 'depreciation', label: 'Depreciation', node: 'depreciation' },
    { key: 'ebit', label: 'EBIT', total: true },
    { key: 'interest_expense', label: 'Net interest expense', node: 'interest_expense' },
    { key: 'pre_tax_income', label: 'Pre-tax income', total: true, node: 'pre_tax_income' },
    { key: 'tax_expense', label: 'Tax', node: 'tax_expense' },
    { key: 'net_income', label: 'Net income', total: true, node: 'net_income' },
  ],
  balance_sheet: [
    { key: 'cash', label: 'Cash', node: 'cash' },
    { key: 'accounts_receivable', label: 'Accounts receivable', node: 'accounts_receivable' },
    { key: 'inventory', label: 'Inventory', node: 'inventory' },
    { key: 'other_current_assets', label: 'Other current assets', node: 'other_current_assets' },
    { key: 'ppe_net', label: 'Net PP&E', node: 'ppe' },
    { key: 'total_assets', label: 'Total assets', total: true },
    { key: 'accounts_payable', label: 'Accounts payable', node: 'accounts_payable' },
    { key: 'other_current_liabilities', label: 'Other current liabilities', node: 'other_current_liabilities' },
    { key: 'revolver', label: 'Revolver', node: 'revolver' },
    { key: 'term_loan', label: 'Term loan', node: 'term_loan' },
    { key: 'total_liabilities', label: 'Total liabilities', total: true },
    { key: 'common_stock', label: 'Common stock' },
    { key: 'retained_earnings', label: 'Retained earnings', node: 'retained_earnings' },
    { key: 'total_equity', label: 'Total equity', total: true },
  ],
  cash_flow: [
    { key: 'net_income', label: 'Net income', node: 'net_income' },
    { key: 'depreciation', label: 'Depreciation', node: 'depreciation' },
    { key: 'change_in_receivables', label: 'Change in receivables' },
    { key: 'change_in_inventory', label: 'Change in inventory' },
    { key: 'change_in_other_current_assets', label: 'Change in other current assets' },
    { key: 'change_in_payables', label: 'Change in payables' },
    { key: 'change_in_other_current_liabilities', label: 'Change in other current liabilities' },
    { key: 'operating_cash_flow', label: 'Operating cash flow', total: true },
    { key: 'capex', label: 'Capital expenditure', node: 'capex' },
    { key: 'investing_cash_flow', label: 'Investing cash flow', total: true },
    { key: 'revolver_net_borrowing', label: 'Revolver borrowing / (repayment)' },
    { key: 'term_loan_repayment', label: 'Term loan repayment', node: 'term_loan_repayment' },
    { key: 'dividends', label: 'Dividends', node: 'dividends' },
    { key: 'financing_cash_flow', label: 'Financing cash flow', total: true },
    { key: 'net_change_in_cash', label: 'Net change in cash', total: true },
    { key: 'beginning_cash', label: 'Beginning cash' },
    { key: 'ending_cash', label: 'Ending cash', total: true },
  ],
}

export interface AssumptionDef {
  key: string
  label: string
  kind: 'percent' | 'days' | 'amount'
}

export const ASSUMPTION_GROUPS: { title: string; rows: AssumptionDef[] }[] = [
  {
    title: 'Revenue and operating costs',
    rows: [
      { key: 'revenue_growth', label: 'Revenue growth', kind: 'percent' },
      { key: 'cogs_pct', label: 'COGS % of revenue', kind: 'percent' },
      { key: 'sga_pct', label: 'SG&A % of revenue', kind: 'percent' },
      { key: 'tax_rate', label: 'Tax rate', kind: 'percent' },
    ],
  },
  {
    title: 'Investment and working capital',
    rows: [
      { key: 'capex_pct', label: 'Capex % of revenue', kind: 'percent' },
      { key: 'depreciation_rate', label: 'Depreciation % of opening PP&E', kind: 'percent' },
      { key: 'dso', label: 'Receivable days (DSO)', kind: 'days' },
      { key: 'dio', label: 'Inventory days (DIO)', kind: 'days' },
      { key: 'dpo', label: 'Payable days (DPO)', kind: 'days' },
    ],
  },
  {
    title: 'Financing and cash',
    rows: [
      { key: 'term_loan_repayment', label: 'Term loan repayment', kind: 'amount' },
      { key: 'term_loan_rate', label: 'Term loan interest rate', kind: 'percent' },
      { key: 'revolver_rate', label: 'Revolver interest rate', kind: 'percent' },
      { key: 'revolver_limit', label: 'Revolver limit', kind: 'amount' },
      { key: 'min_cash', label: 'Minimum cash', kind: 'amount' },
      { key: 'cash_yield', label: 'Interest earned on cash', kind: 'percent' },
      { key: 'dividend_payout', label: 'Dividend payout ratio', kind: 'percent' },
    ],
  },
]
