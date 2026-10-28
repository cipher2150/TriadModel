"""Canonical line items, assumptions and results.

Sign convention for cash flow items: positive = cash inflow, negative = cash outflow.
Income statement expenses are stored as positive amounts.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from app.engine.graph import TraceEntry


@dataclass(frozen=True)
class IncomeStatement:
    revenue: Decimal
    cogs: Decimal
    sga: Decimal
    depreciation: Decimal
    interest_expense: Decimal  # net of interest income
    tax_expense: Decimal

    @property
    def gross_profit(self) -> Decimal:
        return self.revenue - self.cogs

    @property
    def ebit(self) -> Decimal:
        return self.gross_profit - self.sga - self.depreciation

    @property
    def pre_tax_income(self) -> Decimal:
        return self.ebit - self.interest_expense

    @property
    def net_income(self) -> Decimal:
        return self.pre_tax_income - self.tax_expense


@dataclass(frozen=True)
class BalanceSheet:
    cash: Decimal
    accounts_receivable: Decimal
    inventory: Decimal
    other_current_assets: Decimal
    ppe_net: Decimal
    accounts_payable: Decimal
    other_current_liabilities: Decimal
    revolver: Decimal
    term_loan: Decimal
    common_stock: Decimal
    retained_earnings: Decimal

    @property
    def total_assets(self) -> Decimal:
        return (
            self.cash
            + self.accounts_receivable
            + self.inventory
            + self.other_current_assets
            + self.ppe_net
        )

    @property
    def total_liabilities(self) -> Decimal:
        return (
            self.accounts_payable + self.other_current_liabilities + self.revolver + self.term_loan
        )

    @property
    def total_equity(self) -> Decimal:
        return self.common_stock + self.retained_earnings


@dataclass(frozen=True)
class CashFlow:
    beginning_cash: Decimal
    net_income: Decimal
    depreciation: Decimal
    change_in_receivables: Decimal
    change_in_inventory: Decimal
    change_in_other_current_assets: Decimal
    change_in_payables: Decimal
    change_in_other_current_liabilities: Decimal
    capex: Decimal
    revolver_net_borrowing: Decimal
    term_loan_repayment: Decimal
    dividends: Decimal

    @property
    def operating_cash_flow(self) -> Decimal:
        return (
            self.net_income
            + self.depreciation
            + self.change_in_receivables
            + self.change_in_inventory
            + self.change_in_other_current_assets
            + self.change_in_payables
            + self.change_in_other_current_liabilities
        )

    @property
    def investing_cash_flow(self) -> Decimal:
        return self.capex

    @property
    def financing_cash_flow(self) -> Decimal:
        return self.revolver_net_borrowing + self.term_loan_repayment + self.dividends

    @property
    def net_change_in_cash(self) -> Decimal:
        return self.operating_cash_flow + self.investing_cash_flow + self.financing_cash_flow

    @property
    def ending_cash(self) -> Decimal:
        return self.beginning_cash + self.net_change_in_cash


@dataclass(frozen=True)
class HistoricalYear:
    year: int
    income_statement: IncomeStatement
    balance_sheet: BalanceSheet
    cash_flow: CashFlow


@dataclass(frozen=True)
class YearAssumptions:
    """Drivers for one forecast year. Rates are fractions (0.10 = 10%); DSO/DIO/DPO are days."""

    revenue_growth: Decimal
    cogs_pct: Decimal
    sga_pct: Decimal
    depreciation_rate: Decimal  # of opening net PP&E
    capex_pct: Decimal  # of revenue
    dso: Decimal
    dio: Decimal
    dpo: Decimal
    tax_rate: Decimal
    term_loan_rate: Decimal
    revolver_rate: Decimal
    cash_yield: Decimal
    term_loan_repayment: Decimal  # scheduled amount
    min_cash: Decimal
    revolver_limit: Decimal
    dividend_payout: Decimal  # fraction of positive net income


@dataclass(frozen=True)
class Assumptions:
    years: tuple[YearAssumptions, ...]


@dataclass(frozen=True)
class ModelInput:
    historicals: tuple[HistoricalYear, ...]
    assumptions: Assumptions
    tolerance: Decimal


class Severity(StrEnum):
    ERROR = "error"
    WARNING = "warning"


class FlagCode(StrEnum):
    BS_IMBALANCE = "BS_IMBALANCE"
    CASH_TIE_OUT = "CASH_TIE_OUT"
    NI_TIE_OUT = "NI_TIE_OUT"
    RE_ROLLFORWARD = "RE_ROLLFORWARD"
    PPE_ROLLFORWARD = "PPE_ROLLFORWARD"
    DEBT_ROLLFORWARD = "DEBT_ROLLFORWARD"
    CASH_BELOW_MINIMUM = "CASH_BELOW_MINIMUM"
    REVOLVER_LIMIT_EXCEEDED = "REVOLVER_LIMIT_EXCEEDED"
    NEGATIVE_CASH = "NEGATIVE_CASH"
    NEGATIVE_EQUITY = "NEGATIVE_EQUITY"


@dataclass(frozen=True)
class Flag:
    code: FlagCode
    severity: Severity
    year: int
    message: str
    amount: Decimal


@dataclass(frozen=True)
class ForecastYear:
    year: int
    income_statement: IncomeStatement
    balance_sheet: BalanceSheet
    cash_flow: CashFlow
    # Running cash balance kept by the calculation graph; independent of the cash flow
    # statement so the two can be reconciled.
    ledger_cash: Decimal
    unfunded_shortfall: Decimal


@dataclass(frozen=True)
class ModelResult:
    years: tuple[ForecastYear, ...]
    flags: tuple[Flag, ...]
    trace: dict[str, TraceEntry]


class EngineError(Exception):
    """Base class for contract violations (not financial outcomes, which become flags)."""


class InvalidInputError(EngineError):
    pass
