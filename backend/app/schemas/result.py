"""Response contracts. Amounts are serialised as strings rounded to 4 decimal places so
clients never receive binary-float artefacts or 28-digit noise."""

from decimal import ROUND_HALF_EVEN, Decimal
from typing import Annotated, Any, Self

from pydantic import BaseModel, ConfigDict, PlainSerializer

from app.engine.types import (
    BalanceSheet,
    CashFlow,
    Flag,
    ForecastYear,
    HistoricalYear,
    IncomeStatement,
    ModelResult,
)

OUTPUT_QUANTUM = Decimal("0.0001")


def _round(value: Decimal) -> str:
    return str(value.quantize(OUTPUT_QUANTUM, rounding=ROUND_HALF_EVEN))


Money = Annotated[Decimal, PlainSerializer(_round, return_type=str, when_used="json")]


class FromEngine(BaseModel):
    """Builds a response model from an engine object, reading stored fields and properties."""

    model_config = ConfigDict(frozen=True)

    @classmethod
    def from_engine(cls, obj: Any) -> Self:
        return cls(**{name: getattr(obj, name) for name in cls.model_fields})


class IncomeStatementOut(FromEngine):
    revenue: Money
    cogs: Money
    gross_profit: Money
    sga: Money
    depreciation: Money
    ebit: Money
    interest_expense: Money
    pre_tax_income: Money
    tax_expense: Money
    net_income: Money


class BalanceSheetOut(FromEngine):
    cash: Money
    accounts_receivable: Money
    inventory: Money
    other_current_assets: Money
    ppe_net: Money
    total_assets: Money
    accounts_payable: Money
    other_current_liabilities: Money
    revolver: Money
    term_loan: Money
    total_liabilities: Money
    common_stock: Money
    retained_earnings: Money
    total_equity: Money


class CashFlowOut(FromEngine):
    beginning_cash: Money
    net_income: Money
    depreciation: Money
    change_in_receivables: Money
    change_in_inventory: Money
    change_in_other_current_assets: Money
    change_in_payables: Money
    change_in_other_current_liabilities: Money
    operating_cash_flow: Money
    capex: Money
    investing_cash_flow: Money
    revolver_net_borrowing: Money
    term_loan_repayment: Money
    dividends: Money
    financing_cash_flow: Money
    net_change_in_cash: Money
    ending_cash: Money


class StatementsYearOut(BaseModel):
    year: int
    income_statement: IncomeStatementOut
    balance_sheet: BalanceSheetOut
    cash_flow: CashFlowOut


class FlagOut(FromEngine):
    code: str
    severity: str
    year: int
    message: str
    amount: Money


class TraceEntryOut(BaseModel):
    formula: str
    inputs: dict[str, Money]
    value: Money


class ScenarioResultOut(BaseModel):
    years: list[StatementsYearOut]
    flags: list[FlagOut]
    trace: dict[str, TraceEntryOut] | None = None


class CalculationOut(BaseModel):
    company_name: str
    is_demo: bool
    historicals: list[StatementsYearOut]
    scenarios: dict[str, ScenarioResultOut]


def _statements(
    year: int, income: IncomeStatement, balance: BalanceSheet, cash_flow: CashFlow
) -> StatementsYearOut:
    return StatementsYearOut(
        year=year,
        income_statement=IncomeStatementOut.from_engine(income),
        balance_sheet=BalanceSheetOut.from_engine(balance),
        cash_flow=CashFlowOut.from_engine(cash_flow),
    )


def historical_out(h: HistoricalYear) -> StatementsYearOut:
    return _statements(h.year, h.income_statement, h.balance_sheet, h.cash_flow)


def forecast_year_out(y: ForecastYear) -> StatementsYearOut:
    return _statements(y.year, y.income_statement, y.balance_sheet, y.cash_flow)


def scenario_result_out(result: ModelResult, include_trace: bool) -> ScenarioResultOut:
    flags: list[Flag] = list(result.flags)
    trace = (
        {
            key: TraceEntryOut(formula=e.formula, inputs=dict(e.inputs), value=e.value)
            for key, e in result.trace.items()
        }
        if include_trace
        else None
    )
    return ScenarioResultOut(
        years=[forecast_year_out(y) for y in result.years],
        flags=[FlagOut.from_engine(f) for f in flags],
        trace=trace,
    )
